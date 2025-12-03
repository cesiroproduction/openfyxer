"""Email service for handling email operations."""

import asyncio
import base64
import email
import imaplib
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import decrypt_value, encrypt_value
from app.core.exceptions import EmailProviderError
from app.models.email import Email
from app.models.email_account import EmailAccount


class EmailService:
    """Service for email operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_account(self, account_id: UUID, user_id: UUID) -> Optional[EmailAccount]:
        """Get email account by ID."""
        result = await self.db.execute(
            select(EmailAccount).where(
                EmailAccount.id == account_id,
                EmailAccount.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def sync_emails(
        self,
        account: EmailAccount,
        max_emails: int = 100,
    ) -> List[Email]:
        """Sync emails from provider."""
        if account.provider == "gmail":
            return await self._sync_gmail(account, max_emails)
        elif account.provider == "outlook":
            return await self._sync_outlook(account, max_emails)
        elif account.provider == "yahoo":
            return await self._sync_yahoo(account, max_emails)
        elif account.provider == "imap":
            return await self._sync_imap(account, max_emails)
        else:
            raise EmailProviderError(f"Unsupported provider: {account.provider}")

    async def _sync_gmail(
        self,
        account: EmailAccount,
        max_emails: int,
    ) -> List[Email]:
        """Sync emails from Gmail using OAuth."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            if not account.oauth_token:
                raise EmailProviderError("Gmail OAuth token not configured")

            token = decrypt_value(account.oauth_token)
            refresh_token = (
                decrypt_value(account.oauth_refresh_token) if account.oauth_refresh_token else None
            )

            creds = Credentials(
                token=token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
            )

            # Refresh token if needed and persist the new credentials
            if creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request

                creds.refresh(Request())
                account.oauth_token = encrypt_value(creds.token)
                if creds.refresh_token:
                    account.oauth_refresh_token = encrypt_value(creds.refresh_token)
                account.oauth_token_expiry = creds.expiry

            service = build("gmail", "v1", credentials=creds)

            # Get messages
            results = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    maxResults=max_emails,
                    labelIds=["INBOX"],
                )
                .execute()
            )

            messages = results.get("messages", [])
            synced_emails = []

            for msg in messages:
                msg_data = (
                    service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=msg["id"],
                        format="full",
                    )
                    .execute()
                )

                email_obj = await self._parse_gmail_message(account, msg_data)
                if email_obj:
                    synced_emails.append(email_obj)

            # Update last sync time
            account.last_sync = datetime.utcnow()
            await self.db.commit()

            return synced_emails

        except Exception as e:
            raise EmailProviderError(f"Gmail sync failed: {str(e)}")

    async def _sync_outlook(
        self,
        account: EmailAccount,
        max_emails: int,
    ) -> List[Email]:
        """Sync emails from Outlook using OAuth."""
        try:
            import requests

            if not account.oauth_token:
                raise EmailProviderError("Outlook OAuth token not configured")

            token = decrypt_value(account.oauth_token)

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            # Get messages from inbox
            url = (
                f"https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$top={max_emails}"
            )
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                raise EmailProviderError(f"Outlook API error: {response.text}")

            messages = response.json().get("value", [])
            synced_emails = []

            for msg in messages:
                email_obj = await self._parse_outlook_message(account, msg)
                if email_obj:
                    synced_emails.append(email_obj)

            # Update last sync time
            account.last_sync = datetime.utcnow()
            await self.db.commit()

            return synced_emails

        except Exception as e:
            raise EmailProviderError(f"Outlook sync failed: {str(e)}")

    async def _sync_yahoo(
        self,
        account: EmailAccount,
        max_emails: int,
    ) -> List[Email]:
        """Sync emails from Yahoo using IMAP."""
        return await self._sync_imap_generic(
            account,
            max_emails,
            host="imap.mail.yahoo.com",
            port=993,
        )

    async def _sync_imap(
        self,
        account: EmailAccount,
        max_emails: int,
    ) -> List[Email]:
        """Sync emails using generic IMAP."""
        if not account.imap_host or not account.imap_password:
            raise EmailProviderError("IMAP credentials not configured")

        return await self._sync_imap_generic(
            account,
            max_emails,
            host=account.imap_host,
            port=account.imap_port or 993,
        )

    async def _sync_imap_generic(
        self,
        account: EmailAccount,
        max_emails: int,
        host: str,
        port: int,
    ) -> List[Email]:
        """Generic IMAP sync implementation."""
        try:
            password = decrypt_value(account.imap_password) if account.imap_password else None
            if not password:
                raise EmailProviderError("IMAP password not configured")

            # Run IMAP operations in thread pool
            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(
                None,
                self._fetch_imap_emails,
                host,
                port,
                account.email_address,
                password,
                max_emails,
            )

            synced_emails = []
            for msg_data in emails:
                email_obj = await self._parse_imap_message(account, msg_data)
                if email_obj:
                    synced_emails.append(email_obj)

            # Update last sync time
            account.last_sync = datetime.utcnow()
            await self.db.commit()

            return synced_emails

        except Exception as e:
            raise EmailProviderError(f"IMAP sync failed: {str(e)}")

    def _fetch_imap_emails(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        max_emails: int,
    ) -> List[Dict[str, Any]]:
        """Fetch emails via IMAP (blocking operation)."""
        emails = []

        try:
            mail = imaplib.IMAP4_SSL(host, port)
            mail.login(username, password)
            mail.select("INBOX")

            # Search for all emails
            _, message_numbers = mail.search(None, "ALL")
            message_list = message_numbers[0].split()

            # Get latest emails
            for num in message_list[-max_emails:]:
                _, msg_data = mail.fetch(num, "(RFC822)")
                if msg_data[0]:
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    emails.append(
                        {
                            "message_id": msg.get("Message-ID", ""),
                            "subject": msg.get("Subject", ""),
                            "from": msg.get("From", ""),
                            "to": msg.get("To", ""),
                            "cc": msg.get("Cc", ""),
                            "date": msg.get("Date", ""),
                            "body": self._get_email_body(msg),
                        }
                    )

            mail.logout()

        except Exception as e:
            raise EmailProviderError(f"IMAP fetch failed: {str(e)}")

        return emails

    def _get_email_body(self, msg: email.message.Message) -> Tuple[str, str]:
        """Extract email body (text and HTML)."""
        text_body = ""
        html_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    text_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                elif content_type == "text/html":
                    html_body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
        else:
            content_type = msg.get_content_type()
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode("utf-8", errors="ignore")
                if content_type == "text/html":
                    html_body = body
                else:
                    text_body = body

        return text_body, html_body

    async def _parse_gmail_message(
        self,
        account: EmailAccount,
        msg_data: Dict[str, Any],
    ) -> Optional[Email]:
        """Parse Gmail message into Email model."""
        try:
            headers = {
                h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])
            }

            # Check if email already exists
            message_id = msg_data.get("id", "")
            existing = await self.db.execute(
                select(Email).where(
                    Email.account_id == account.id,
                    Email.message_id == message_id,
                )
            )
            if existing.scalar_one_or_none():
                return None

            # Extract body
            body_text = ""
            body_html = ""
            payload = msg_data.get("payload", {})

            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    elif part.get("mimeType") == "text/html":
                        data = part.get("body", {}).get("data", "")
                        body_html = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            else:
                data = payload.get("body", {}).get("data", "")
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

            email_obj = Email(
                account_id=account.id,
                message_id=message_id,
                thread_id=msg_data.get("threadId"),
                subject=headers.get("Subject"),
                sender=headers.get("From", ""),
                recipients=[headers.get("To", "")] if headers.get("To") else None,
                cc=[headers.get("Cc", "")] if headers.get("Cc") else None,
                body_text=body_text,
                body_html=body_html,
                snippet=msg_data.get("snippet"),
                labels=msg_data.get("labelIds"),
                has_attachments=any(part.get("filename") for part in payload.get("parts", [])),
                is_read="UNREAD" not in msg_data.get("labelIds", []),
                is_starred="STARRED" in msg_data.get("labelIds", []),
                received_at=datetime.fromtimestamp(int(msg_data.get("internalDate", 0)) / 1000),
            )

            self.db.add(email_obj)
            return email_obj

        except Exception as e:
            print(f"Error parsing Gmail message: {e}")
            return None

    async def _parse_outlook_message(
        self,
        account: EmailAccount,
        msg_data: Dict[str, Any],
    ) -> Optional[Email]:
        """Parse Outlook message into Email model."""
        try:
            message_id = msg_data.get("id", "")

            # Check if email already exists
            existing = await self.db.execute(
                select(Email).where(
                    Email.account_id == account.id,
                    Email.message_id == message_id,
                )
            )
            if existing.scalar_one_or_none():
                return None

            email_obj = Email(
                account_id=account.id,
                message_id=message_id,
                thread_id=msg_data.get("conversationId"),
                subject=msg_data.get("subject"),
                sender=msg_data.get("from", {}).get("emailAddress", {}).get("address", ""),
                sender_name=msg_data.get("from", {}).get("emailAddress", {}).get("name"),
                recipients=[
                    r.get("emailAddress", {}).get("address", "")
                    for r in msg_data.get("toRecipients", [])
                ],
                cc=[
                    r.get("emailAddress", {}).get("address", "")
                    for r in msg_data.get("ccRecipients", [])
                ],
                body_text=(
                    msg_data.get("body", {}).get("content", "")
                    if msg_data.get("body", {}).get("contentType") == "text"
                    else None
                ),
                body_html=(
                    msg_data.get("body", {}).get("content", "")
                    if msg_data.get("body", {}).get("contentType") == "html"
                    else None
                ),
                snippet=msg_data.get("bodyPreview"),
                has_attachments=msg_data.get("hasAttachments", False),
                is_read=msg_data.get("isRead", False),
                received_at=(
                    datetime.fromisoformat(
                        msg_data.get("receivedDateTime", "").replace("Z", "+00:00")
                    )
                    if msg_data.get("receivedDateTime")
                    else None
                ),
            )

            self.db.add(email_obj)
            return email_obj

        except Exception as e:
            print(f"Error parsing Outlook message: {e}")
            return None

    async def _parse_imap_message(
        self,
        account: EmailAccount,
        msg_data: Dict[str, Any],
    ) -> Optional[Email]:
        """Parse IMAP message into Email model."""
        try:
            message_id = msg_data.get("message_id", "")

            # Check if email already exists
            existing = await self.db.execute(
                select(Email).where(
                    Email.account_id == account.id,
                    Email.message_id == message_id,
                )
            )
            if existing.scalar_one_or_none():
                return None

            body_text, body_html = msg_data.get("body", ("", ""))

            email_obj = Email(
                account_id=account.id,
                message_id=message_id,
                subject=msg_data.get("subject"),
                sender=msg_data.get("from", ""),
                recipients=[msg_data.get("to", "")] if msg_data.get("to") else None,
                cc=[msg_data.get("cc", "")] if msg_data.get("cc") else None,
                body_text=body_text,
                body_html=body_html,
                snippet=body_text[:200] if body_text else None,
            )

            self.db.add(email_obj)
            return email_obj

        except Exception as e:
            print(f"Error parsing IMAP message: {e}")
            return None

    async def send_email(
        self,
        account: EmailAccount,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        if account.provider == "gmail":
            return await self._send_gmail(account, to, subject, body, cc, bcc, html_body)
        elif account.provider == "outlook":
            return await self._send_outlook(account, to, subject, body, cc, bcc, html_body)
        else:
            return await self._send_smtp(account, to, subject, body, cc, bcc, html_body)

    async def _send_gmail(
        self,
        account: EmailAccount,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send email via Gmail API."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            token = decrypt_value(account.oauth_token)
            refresh_token = (
                decrypt_value(account.oauth_refresh_token) if account.oauth_refresh_token else None
            )

            creds = Credentials(
                token=token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
            )

            service = build("gmail", "v1", credentials=creds)

            message = MIMEMultipart("alternative")
            message["To"] = ", ".join(to)
            message["From"] = account.email_address
            message["Subject"] = subject

            if cc:
                message["Cc"] = ", ".join(cc)
            if bcc:
                message["Bcc"] = ", ".join(bcc)

            message.attach(MIMEText(body, "plain"))
            if html_body:
                message.attach(MIMEText(html_body, "html"))

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(
                userId="me",
                body={"raw": raw},
            ).execute()

            return True

        except Exception as e:
            raise EmailProviderError(f"Gmail send failed: {str(e)}")

    async def _send_outlook(
        self,
        account: EmailAccount,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send email via Outlook API."""
        try:
            import requests

            token = decrypt_value(account.oauth_token)

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            email_data = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML" if html_body else "Text",
                        "content": html_body or body,
                    },
                    "toRecipients": [{"emailAddress": {"address": addr}} for addr in to],
                },
                "saveToSentItems": True,
            }

            if cc:
                email_data["message"]["ccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in cc
                ]
            if bcc:
                email_data["message"]["bccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in bcc
                ]

            response = requests.post(
                "https://graph.microsoft.com/v1.0/me/sendMail",
                headers=headers,
                json=email_data,
            )

            if response.status_code != 202:
                raise EmailProviderError(f"Outlook send failed: {response.text}")

            return True

        except Exception as e:
            raise EmailProviderError(f"Outlook send failed: {str(e)}")

    async def _send_smtp(
        self,
        account: EmailAccount,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send email via SMTP."""
        try:
            if not account.smtp_host or not account.imap_password:
                raise EmailProviderError("SMTP credentials not configured")

            password = decrypt_value(account.imap_password)

            message = MIMEMultipart("alternative")
            message["To"] = ", ".join(to)
            message["From"] = account.email_address
            message["Subject"] = subject

            if cc:
                message["Cc"] = ", ".join(cc)

            message.attach(MIMEText(body, "plain"))
            if html_body:
                message.attach(MIMEText(html_body, "html"))

            all_recipients = to + (cc or []) + (bcc or [])

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_smtp_sync,
                account.smtp_host,
                account.smtp_port or 587,
                account.email_address,
                password,
                all_recipients,
                message.as_string(),
            )

            return True

        except Exception as e:
            raise EmailProviderError(f"SMTP send failed: {str(e)}")

    def _send_smtp_sync(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        recipients: List[str],
        message: str,
    ) -> None:
        """Send email via SMTP (blocking operation)."""
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, recipients, message)

    async def classify_email(self, email_obj: Email) -> str:
        """Classify email into category using LLM."""
        # This will be implemented with LLM service
        # For now, return a basic classification based on keywords
        subject = (email_obj.subject or "").lower()
        body = (email_obj.body_text or "").lower()
        content = f"{subject} {body}"

        if any(word in content for word in ["urgent", "asap", "immediately", "critical"]):
            return "urgent"
        elif any(word in content for word in ["unsubscribe", "newsletter", "weekly digest"]):
            return "newsletter"
        elif any(word in content for word in ["spam", "winner", "lottery", "click here"]):
            return "spam"
        elif any(word in content for word in ["reply", "response", "answer", "question"]):
            return "to_respond"
        else:
            return "fyi"

    async def detect_language(self, text: str) -> str:
        """Detect language of text."""
        # Simple language detection based on common words
        romanian_words = [
            "și",
            "este",
            "pentru",
            "care",
            "sunt",
            "sau",
            "dar",
            "mai",
            "poate",
        ]
        text_lower = text.lower()

        romanian_count = sum(1 for word in romanian_words if word in text_lower)

        if romanian_count >= 2:
            return "ro"
        return "en"
