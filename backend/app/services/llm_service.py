"""LLM service for handling AI model operations."""

import asyncio
import json
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.encryption import decrypt_value
from app.core.exceptions import LLMError


class LLMService:
    """Service for LLM operations."""

    def __init__(
        self,
        provider: str = "local",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Generate text using the configured LLM."""
        if self.provider == "local":
            return await self._generate_local(prompt, system_prompt, max_tokens, temperature, stop)
        elif self.provider == "openai":
            return await self._generate_openai(prompt, system_prompt, max_tokens, temperature, stop)
        elif self.provider == "gemini":
            return await self._generate_gemini(prompt, system_prompt, max_tokens, temperature, stop)
        elif self.provider == "claude":
            return await self._generate_claude(prompt, system_prompt, max_tokens, temperature, stop)
        elif self.provider == "cohere":
            return await self._generate_cohere(prompt, system_prompt, max_tokens, temperature, stop)
        else:
            raise LLMError(f"Unsupported LLM provider: {self.provider}")

    async def _generate_local(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        stop: Optional[List[str]],
    ) -> str:
        """Generate using local Ollama."""
        try:
            import httpx

            model = self.model or settings.LOCAL_LLM_MODEL

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": temperature,
                            "stop": stop or [],
                        },
                    },
                )

                if response.status_code != 200:
                    raise LLMError(f"Ollama error: {response.text}")

                result = response.json()
                return result.get("message", {}).get("content", "")

        except Exception as e:
            raise LLMError(f"Local LLM generation failed: {str(e)}")

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        stop: Optional[List[str]],
    ) -> str:
        """Generate using OpenAI API."""
        try:
            from openai import AsyncOpenAI

            if not self.api_key:
                raise LLMError("OpenAI API key not configured")

            client = AsyncOpenAI(api_key=self.api_key)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self.model or "gpt-4-turbo-preview",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            raise LLMError(f"OpenAI generation failed: {str(e)}")

    async def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        stop: Optional[List[str]],
    ) -> str:
        """Generate using Google Gemini API."""
        try:
            import google.generativeai as genai

            if not self.api_key:
                raise LLMError("Gemini API key not configured")

            genai.configure(api_key=self.api_key)

            model = genai.GenerativeModel(
                model_name=self.model or "gemini-pro",
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                    "stop_sequences": stop or [],
                },
            )

            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(full_prompt),
            )

            return response.text

        except Exception as e:
            raise LLMError(f"Gemini generation failed: {str(e)}")

    async def _generate_claude(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        stop: Optional[List[str]],
    ) -> str:
        """Generate using Anthropic Claude API."""
        try:
            from anthropic import AsyncAnthropic

            if not self.api_key:
                raise LLMError("Claude API key not configured")

            client = AsyncAnthropic(api_key=self.api_key)

            response = await client.messages.create(
                model=self.model or "claude-3-sonnet-20240229",
                max_tokens=max_tokens,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                stop_sequences=stop or [],
            )

            return response.content[0].text

        except Exception as e:
            raise LLMError(f"Claude generation failed: {str(e)}")

    async def _generate_cohere(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        stop: Optional[List[str]],
    ) -> str:
        """Generate using Cohere API."""
        try:
            import cohere

            if not self.api_key:
                raise LLMError("Cohere API key not configured")

            client = cohere.AsyncClient(api_key=self.api_key)

            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = await client.generate(
                model=self.model or "command",
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop_sequences=stop or [],
            )

            return response.generations[0].text

        except Exception as e:
            raise LLMError(f"Cohere generation failed: {str(e)}")

    async def generate_email_draft(
        self,
        original_email: Dict[str, Any],
        user_style: Optional[Dict[str, Any]] = None,
        tone: str = "professional",
        language: str = "en",
    ) -> str:
        """Generate an email draft response."""
        system_prompt = self._build_email_system_prompt(user_style, tone, language)

        prompt = f"""Generate a response to the following email:

From: {original_email.get('sender', 'Unknown')}
Subject: {original_email.get('subject', 'No Subject')}

{original_email.get('body', '')}

---
Write a {tone} response in {language}. Be concise and helpful."""

        return await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=500,
            temperature=0.7,
        )

    def _build_email_system_prompt(
        self,
        user_style: Optional[Dict[str, Any]],
        tone: str,
        language: str,
    ) -> str:
        """Build system prompt for email generation."""
        lang_instruction = "Romanian" if language == "ro" else "English"

        base_prompt = f"""You are an AI assistant helping to draft email responses.
Write in {lang_instruction}.
Use a {tone} tone.
Be concise and clear.
Do not include placeholder text like [Your Name].
"""

        if user_style:
            if user_style.get("common_greetings"):
                base_prompt += f"\nPreferred greetings: {', '.join(user_style['common_greetings'])}"
            if user_style.get("common_closings"):
                base_prompt += f"\nPreferred closings: {', '.join(user_style['common_closings'])}"
            if user_style.get("signature"):
                base_prompt += f"\nSignature: {user_style['signature']}"

        return base_prompt

    async def classify_email(
        self,
        subject: str,
        body: str,
        sender: str,
    ) -> Dict[str, Any]:
        """Classify an email using LLM."""
        prompt = f"""Classify the following email into one of these categories:
- urgent: Requires immediate attention
- to_respond: Needs a response but not urgent
- fyi: Informational, no response needed
- newsletter: Marketing or newsletter content
- spam: Unwanted or suspicious email

Also detect the language (en or ro) and sentiment (positive, negative, neutral).

Email:
From: {sender}
Subject: {subject}

{body[:1000]}

Respond in JSON format:
{{"category": "...", "language": "...", "sentiment": "...", "priority_score": 0.0-1.0}}"""

        response = await self.generate(
            prompt=prompt,
            max_tokens=100,
            temperature=0.3,
        )

        try:
            # Try to parse JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        # Default classification
        return {
            "category": "fyi",
            "language": "en",
            "sentiment": "neutral",
            "priority_score": 0.5,
        }

    async def summarize_meeting(
        self,
        transcript: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Summarize a meeting transcript."""
        lang_instruction = "Romanian" if language == "ro" else "English"

        prompt = f"""Summarize the following meeting transcript in {lang_instruction}.

Provide:
1. Executive summary (2-3 sentences)
2. Key decisions made
3. Action items with assignees if mentioned
4. Main topics discussed

Transcript:
{transcript[:4000]}

Respond in JSON format:
{{
    "summary": "...",
    "key_decisions": ["..."],
    "action_items": ["..."],
    "topics": ["..."]
}}"""

        response = await self.generate(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.5,
        )

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        return {
            "summary": "Unable to generate summary",
            "key_decisions": [],
            "action_items": [],
            "topics": [],
        }

    async def answer_question(
        self,
        question: str,
        context: str,
        language: str = "en",
    ) -> str:
        """Answer a question based on context."""
        lang_instruction = "Romanian" if language == "ro" else "English"

        prompt = f"""Based on the following context, answer the question in {lang_instruction}.
If the answer is not in the context, say so.

Context:
{context[:3000]}

Question: {question}

Answer:"""

        return await self.generate(
            prompt=prompt,
            max_tokens=500,
            temperature=0.5,
        )

    async def get_embeddings(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """Get embeddings for texts."""
        if self.provider == "local":
            return await self._get_local_embeddings(texts)
        elif self.provider == "openai":
            return await self._get_openai_embeddings(texts)
        else:
            # Fallback to local embeddings
            return await self._get_local_embeddings(texts)

    async def _get_local_embeddings(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """Get embeddings using local model."""
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer("all-MiniLM-L6-v2")

            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: model.encode(texts).tolist(),
            )

            return embeddings

        except Exception as e:
            raise LLMError(f"Local embeddings failed: {str(e)}")

    async def _get_openai_embeddings(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """Get embeddings using OpenAI API."""
        try:
            from openai import AsyncOpenAI

            if not self.api_key:
                raise LLMError("OpenAI API key not configured")

            client = AsyncOpenAI(api_key=self.api_key)

            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )

            return [item.embedding for item in response.data]

        except Exception as e:
            raise LLMError(f"OpenAI embeddings failed: {str(e)}")
