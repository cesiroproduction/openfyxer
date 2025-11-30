"""Notification service for sending notifications."""

import asyncio
import json
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.core.encryption import decrypt_value
from app.core.exceptions import NotificationError


class NotificationService:
    """Service for sending notifications."""

    def __init__(
        self,
        slack_webhook_url: Optional[str] = None,
        sms_provider: Optional[str] = None,
        sms_api_key: Optional[str] = None,
        sms_phone_number: Optional[str] = None,
        notification_email: Optional[str] = None,
    ):
        self.slack_webhook_url = slack_webhook_url
        self.sms_provider = sms_provider
        self.sms_api_key = sms_api_key
        self.sms_phone_number = sms_phone_number
        self.notification_email = notification_email

    async def send_slack(
        self,
        message: str,
        channel: Optional[str] = None,
        username: str = "OpenFyxer",
        icon_emoji: str = ":robot_face:",
    ) -> bool:
        """Send notification via Slack webhook."""
        if not self.slack_webhook_url:
            raise NotificationError("Slack webhook URL not configured")

        try:
            payload = {
                "text": message,
                "username": username,
                "icon_emoji": icon_emoji,
            }

            if channel:
                payload["channel"] = channel

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=payload,
                    timeout=10.0,
                )

                if response.status_code != 200:
                    raise NotificationError(f"Slack API error: {response.text}")

            return True

        except Exception as e:
            raise NotificationError(f"Slack notification failed: {str(e)}")

    async def send_slack_rich(
        self,
        title: str,
        message: str,
        color: str = "#36a64f",
        fields: Optional[Dict[str, str]] = None,
        actions: Optional[list] = None,
    ) -> bool:
        """Send rich Slack notification with attachments."""
        if not self.slack_webhook_url:
            raise NotificationError("Slack webhook URL not configured")

        try:
            attachment = {
                "color": color,
                "title": title,
                "text": message,
                "ts": int(asyncio.get_event_loop().time()),
            }

            if fields:
                attachment["fields"] = [
                    {"title": k, "value": v, "short": True}
                    for k, v in fields.items()
                ]

            if actions:
                attachment["actions"] = actions

            payload = {
                "attachments": [attachment],
                "username": "OpenFyxer",
                "icon_emoji": ":robot_face:",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=payload,
                    timeout=10.0,
                )

                if response.status_code != 200:
                    raise NotificationError(f"Slack API error: {response.text}")

            return True

        except Exception as e:
            raise NotificationError(f"Slack notification failed: {str(e)}")

    async def send_sms(
        self,
        message: str,
        to_number: Optional[str] = None,
    ) -> bool:
        """Send SMS notification."""
        if not self.sms_api_key:
            raise NotificationError("SMS API key not configured")

        phone = to_number or self.sms_phone_number
        if not phone:
            raise NotificationError("Phone number not configured")

        if self.sms_provider == "twilio":
            return await self._send_twilio_sms(message, phone)
        else:
            raise NotificationError(f"Unsupported SMS provider: {self.sms_provider}")

    async def _send_twilio_sms(
        self,
        message: str,
        to_number: str,
    ) -> bool:
        """Send SMS via Twilio."""
        try:
            # Parse Twilio credentials (format: account_sid:auth_token:from_number)
            parts = self.sms_api_key.split(":")
            if len(parts) != 3:
                raise NotificationError("Invalid Twilio credentials format")

            account_sid, auth_token, from_number = parts

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                    auth=(account_sid, auth_token),
                    data={
                        "To": to_number,
                        "From": from_number,
                        "Body": message,
                    },
                    timeout=10.0,
                )

                if response.status_code not in [200, 201]:
                    raise NotificationError(f"Twilio API error: {response.text}")

            return True

        except Exception as e:
            raise NotificationError(f"Twilio SMS failed: {str(e)}")

    async def send_email(
        self,
        subject: str,
        body: str,
        to_email: Optional[str] = None,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send email notification."""
        email_to = to_email or self.notification_email
        if not email_to:
            raise NotificationError("Notification email not configured")

        try:
            import aiosmtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.SMTP_FROM_EMAIL or "noreply@openfyxer.local"
            message["To"] = email_to

            message.attach(MIMEText(body, "plain"))
            if html_body:
                message.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST or "localhost",
                port=settings.SMTP_PORT or 587,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )

            return True

        except Exception as e:
            raise NotificationError(f"Email notification failed: {str(e)}")

    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Send webhook notification."""
        try:
            default_headers = {
                "Content-Type": "application/json",
                "User-Agent": "OpenFyxer/1.0",
            }

            if headers:
                default_headers.update(headers)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=default_headers,
                    timeout=10.0,
                )

                if response.status_code >= 400:
                    raise NotificationError(f"Webhook error: {response.status_code}")

            return True

        except Exception as e:
            raise NotificationError(f"Webhook notification failed: {str(e)}")

    async def notify_new_email(
        self,
        sender: str,
        subject: str,
        category: str,
        preview: str,
    ) -> None:
        """Send notification for new email."""
        message = f"New {category} email from {sender}: {subject}\n\n{preview[:200]}"

        # Send to configured channels
        if self.slack_webhook_url:
            color = "#ff0000" if category == "urgent" else "#36a64f"
            await self.send_slack_rich(
                title=f"New Email: {subject}",
                message=f"From: {sender}\n{preview[:200]}",
                color=color,
                fields={"Category": category},
            )

        if self.sms_phone_number and category == "urgent":
            await self.send_sms(f"Urgent email from {sender}: {subject}")

    async def notify_draft_ready(
        self,
        email_subject: str,
        draft_preview: str,
    ) -> None:
        """Send notification when draft is ready for review."""
        if self.slack_webhook_url:
            await self.send_slack_rich(
                title="Draft Ready for Review",
                message=f"Re: {email_subject}\n\n{draft_preview[:200]}",
                color="#0066cc",
            )

    async def notify_meeting_reminder(
        self,
        title: str,
        start_time: str,
        location: Optional[str] = None,
        meeting_link: Optional[str] = None,
    ) -> None:
        """Send meeting reminder notification."""
        message = f"Upcoming meeting: {title} at {start_time}"
        if location:
            message += f"\nLocation: {location}"
        if meeting_link:
            message += f"\nJoin: {meeting_link}"

        if self.slack_webhook_url:
            fields = {"Time": start_time}
            if location:
                fields["Location"] = location

            await self.send_slack_rich(
                title=f"Meeting Reminder: {title}",
                message=message,
                color="#ffcc00",
                fields=fields,
            )

        if self.sms_phone_number:
            await self.send_sms(message)

    async def notify_transcription_complete(
        self,
        meeting_title: str,
        summary: Optional[str] = None,
    ) -> None:
        """Send notification when transcription is complete."""
        if self.slack_webhook_url:
            message = f"Transcription complete for: {meeting_title}"
            if summary:
                message += f"\n\nSummary: {summary[:300]}"

            await self.send_slack_rich(
                title="Transcription Complete",
                message=message,
                color="#36a64f",
            )

    async def notify_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send error notification."""
        if self.slack_webhook_url:
            fields = {"Error Type": error_type}
            if context:
                for k, v in list(context.items())[:3]:
                    fields[k] = str(v)

            await self.send_slack_rich(
                title="OpenFyxer Error",
                message=error_message,
                color="#ff0000",
                fields=fields,
            )
