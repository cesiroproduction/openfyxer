"""Transcription service for audio processing."""

import asyncio
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.exceptions import TranscriptionError


class TranscriptionService:
    """Service for audio transcription using Whisper."""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "auto",
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _get_model(self):
        """Get or initialize the Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                # Determine device
                device = self.device
                compute_type = self.compute_type

                if device == "auto":
                    try:
                        import torch
                        device = "cuda" if torch.cuda.is_available() else "cpu"
                    except ImportError:
                        device = "cpu"

                if compute_type == "auto":
                    compute_type = "float16" if device == "cuda" else "int8"

                self._model = WhisperModel(
                    self.model_size,
                    device=device,
                    compute_type=compute_type,
                )

            except Exception as e:
                raise TranscriptionError(f"Failed to load Whisper model: {str(e)}")

        return self._model

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transcribe audio file."""
        if not os.path.exists(audio_path):
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        try:
            import time
            start_time = time.time()

            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio_path,
                language,
            )

            transcription_time = time.time() - start_time

            return {
                "text": result["text"],
                "language": result["language"],
                "segments": result["segments"],
                "duration_seconds": result["duration"],
                "transcription_time_seconds": transcription_time,
            }

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {str(e)}")

    def _transcribe_sync(
        self,
        audio_path: str,
        language: Optional[str],
    ) -> Dict[str, Any]:
        """Synchronous transcription (runs in thread pool)."""
        model = self._get_model()

        # Transcribe
        segments, info = model.transcribe(
            audio_path,
            language=language if language and language != "auto" else None,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
            ),
        )

        # Collect segments
        segment_list = []
        full_text = []

        for segment in segments:
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            })
            full_text.append(segment.text.strip())

        return {
            "text": " ".join(full_text),
            "language": info.language,
            "segments": segment_list,
            "duration": info.duration,
        }

    async def transcribe_with_diarization(
        self,
        audio_path: str,
        language: Optional[str] = None,
        num_speakers: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Transcribe audio with speaker diarization."""
        # First, get basic transcription
        transcription = await self.transcribe(audio_path, language)

        # TODO: Implement speaker diarization using pyannote.audio
        # For now, return transcription without diarization
        transcription["speakers"] = []

        return transcription

    async def detect_language(
        self,
        audio_path: str,
    ) -> str:
        """Detect language from audio."""
        if not os.path.exists(audio_path):
            raise TranscriptionError(f"Audio file not found: {audio_path}")

        try:
            loop = asyncio.get_event_loop()
            language = await loop.run_in_executor(
                None,
                self._detect_language_sync,
                audio_path,
            )
            return language

        except Exception as e:
            raise TranscriptionError(f"Language detection failed: {str(e)}")

    def _detect_language_sync(self, audio_path: str) -> str:
        """Synchronous language detection."""
        model = self._get_model()

        # Use first 30 seconds for language detection
        _, info = model.transcribe(
            audio_path,
            language=None,
            beam_size=1,
        )

        return info.language

    async def get_audio_duration(
        self,
        audio_path: str,
    ) -> float:
        """Get audio file duration in seconds."""
        try:
            import subprocess

            loop = asyncio.get_event_loop()
            duration = await loop.run_in_executor(
                None,
                self._get_duration_sync,
                audio_path,
            )
            return duration

        except Exception as e:
            raise TranscriptionError(f"Failed to get audio duration: {str(e)}")

    def _get_duration_sync(self, audio_path: str) -> float:
        """Get duration synchronously using ffprobe."""
        import subprocess

        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise TranscriptionError(f"ffprobe error: {result.stderr}")

        return float(result.stdout.strip())

    async def convert_audio(
        self,
        input_path: str,
        output_format: str = "wav",
        sample_rate: int = 16000,
    ) -> str:
        """Convert audio to optimal format for transcription."""
        try:
            import subprocess

            # Generate output path
            output_path = tempfile.mktemp(suffix=f".{output_format}")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._convert_audio_sync,
                input_path,
                output_path,
                sample_rate,
            )

            return output_path

        except Exception as e:
            raise TranscriptionError(f"Audio conversion failed: {str(e)}")

    def _convert_audio_sync(
        self,
        input_path: str,
        output_path: str,
        sample_rate: int,
    ) -> None:
        """Convert audio synchronously using ffmpeg."""
        import subprocess

        result = subprocess.run(
            [
                "ffmpeg",
                "-i", input_path,
                "-ar", str(sample_rate),
                "-ac", "1",
                "-y",
                output_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise TranscriptionError(f"ffmpeg error: {result.stderr}")

    async def extract_audio_from_video(
        self,
        video_path: str,
    ) -> str:
        """Extract audio from video file."""
        try:
            output_path = tempfile.mktemp(suffix=".wav")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._extract_audio_sync,
                video_path,
                output_path,
            )

            return output_path

        except Exception as e:
            raise TranscriptionError(f"Audio extraction failed: {str(e)}")

    def _extract_audio_sync(
        self,
        video_path: str,
        output_path: str,
    ) -> None:
        """Extract audio synchronously using ffmpeg."""
        import subprocess

        result = subprocess.run(
            [
                "ffmpeg",
                "-i", video_path,
                "-vn",
                "-ar", "16000",
                "-ac", "1",
                "-y",
                output_path,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise TranscriptionError(f"ffmpeg error: {result.stderr}")

    def get_available_models(self) -> list:
        """Get list of available Whisper models."""
        return [
            {
                "id": "tiny",
                "name": "Tiny",
                "description": "Fastest, lowest accuracy (~1GB VRAM)",
                "size_mb": 75,
            },
            {
                "id": "base",
                "name": "Base",
                "description": "Good balance of speed and accuracy (~1GB VRAM)",
                "size_mb": 142,
            },
            {
                "id": "small",
                "name": "Small",
                "description": "Better accuracy, slower (~2GB VRAM)",
                "size_mb": 466,
            },
            {
                "id": "medium",
                "name": "Medium",
                "description": "High accuracy (~5GB VRAM)",
                "size_mb": 1500,
            },
            {
                "id": "large-v3",
                "name": "Large v3",
                "description": "Best accuracy, slowest (~10GB VRAM)",
                "size_mb": 2900,
            },
        ]

    def get_supported_languages(self) -> list:
        """Get list of supported languages."""
        return [
            {"code": "en", "name": "English"},
            {"code": "ro", "name": "Romanian"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
            {"code": "it", "name": "Italian"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "nl", "name": "Dutch"},
            {"code": "pl", "name": "Polish"},
            {"code": "ru", "name": "Russian"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "ar", "name": "Arabic"},
            {"code": "hi", "name": "Hindi"},
        ]
