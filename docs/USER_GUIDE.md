# OpenFyxer User Guide

This guide will help you get started with OpenFyxer and make the most of its features.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard](#dashboard)
3. [Inbox Management](#inbox-management)
4. [Calendar](#calendar)
5. [Knowledge Base](#knowledge-base)
6. [Meetings](#meetings)
7. [AI Chat](#ai-chat)
8. [Settings](#settings)

## Getting Started

### First Login

1. Navigate to http://localhost:3000 (or your configured URL)
2. Click "Register" to create your account
3. Enter your email, full name, and password
4. After registration, you'll be redirected to the dashboard

### Initial Setup

After your first login, we recommend:

1. **Connect Email Accounts**: Go to Settings > Email Accounts to connect your email
2. **Configure LLM**: Choose between local or cloud LLM in Settings > LLM Settings
3. **Set Language**: Choose your preferred language (English or Romanian)
4. **Enable 2FA**: For security, enable two-factor authentication in Settings > Security

## Dashboard

The dashboard provides an overview of your assistant's activity:

**Stats Cards**
- Time Saved: Estimated time saved by AI assistance
- Emails Processed: Number of emails analyzed
- Drafts Generated: AI-generated draft responses
- Meetings Transcribed: Meetings with transcriptions

**Urgent Emails**
Shows up to 5 emails marked as urgent that need your attention.

**Today's Meetings**
Lists your meetings for today with quick access to join links.

**Indexing Status**
Shows the progress of indexing emails, documents, and meetings into the knowledge base.

## Inbox Management

### Email Categories

OpenFyxer automatically categorizes your emails:

- **Urgent**: Requires immediate attention
- **To Respond**: Needs a reply but not urgent
- **FYI**: Informational, no response needed
- **Newsletter**: Marketing and newsletter content
- **Spam**: Unwanted or suspicious emails

### Viewing Emails

1. Click on "Inbox" in the sidebar
2. Use category filters to view specific types
3. Click on an email to view its full content
4. The right panel shows email details and actions

### Email Actions

- **Star**: Mark important emails for quick access
- **Archive**: Remove from inbox without deleting
- **Mark Read/Unread**: Toggle read status
- **Generate Draft**: Create an AI-powered response

### AI Draft Generation

1. Select an email that needs a response
2. Click "Generate Draft"
3. Review the generated draft
4. Edit if needed
5. Click "Approve" then "Send" to send the email

The AI considers:
- Your writing style (configured in Settings)
- The email's language (responds in same language)
- Previous conversation context
- Your knowledge base for relevant information

### Syncing Emails

Click the "Sync" button to fetch new emails from all connected accounts. Emails are also synced automatically in the background.

## Calendar

### Viewing Events

1. Click "Calendar" in the sidebar
2. Toggle between Week and Month views
3. Navigate using Previous/Next buttons
4. Click "Today" to return to current date

### Creating Events

1. Click "New Event" button
2. Fill in event details:
   - Title (required)
   - Start and End time
   - Location
   - Description
   - Attendees (comma-separated emails)
   - All-day toggle
3. Click "Create"

### Event Details

Click on any event to view details:
- Full description
- Attendee list
- Location
- Edit or Delete options

### Conflict Detection

When creating events, the system automatically checks for conflicts with existing events and warns you if there's an overlap.

## Knowledge Base

The Knowledge Base uses GraphRAG to index and search your data.

### Asking Questions

1. Go to "Knowledge Base" in the sidebar
2. Type your question in the search box
3. Click "Search" or press Enter
4. View the AI-generated answer with source citations

Example questions:
- "What did John say about the project deadline?"
- "Find emails about the Q4 budget"
- "What were the action items from last week's meeting?"

### Understanding Results

Each result shows:
- **Answer**: AI-generated response to your question
- **Confidence**: How confident the AI is in the answer
- **Sources**: Documents, emails, or meetings used to generate the answer

### Uploading Documents

1. Click "Upload Document"
2. Select a file (PDF, DOCX, TXT supported)
3. Wait for indexing to complete
4. The document is now searchable

### Managing Documents

View all indexed documents in the table:
- Filename and type
- File size
- Indexed date
- Delete option

## Meetings

### Creating Meetings

1. Go to "Meetings" in the sidebar
2. Click "New Meeting"
3. Enter meeting details:
   - Title
   - Date and time
   - Description
   - Participants

### Uploading Audio

1. Select a meeting
2. Click "Upload Audio"
3. Select your audio file (MP3, WAV, M4A supported)
4. Wait for upload to complete

### Transcription

1. After uploading audio, click "Transcribe"
2. Wait for transcription to complete (may take a few minutes)
3. View the full transcript in the meeting details

### Summarization

1. After transcription, click "Summarize"
2. The AI generates:
   - Executive summary
   - Key discussion points
   - Action items with assignees
   - Key decisions made

### Follow-up Emails

1. After summarization, click "Generate Follow-up"
2. Review the generated email
3. Edit if needed
4. Send to meeting participants

## AI Chat

The AI Chat allows you to have conversations with your assistant.

### Starting a Conversation

1. Go to "Chat" in the sidebar
2. Type your message in the input box
3. Press Enter or click Send

### What You Can Ask

- Questions about your emails and documents
- Help drafting responses
- Meeting summaries
- Calendar queries
- General assistance

### Suggestions

The sidebar shows suggested prompts based on your recent activity:
- "Summarize my unread emails"
- "What meetings do I have today?"
- "Draft a response to [recent email]"

### Chat History

Your conversation history is preserved. Click "Clear History" to start fresh.

## Settings

### Profile

- View your email and name
- Set your email writing style:
  - Formal
  - Friendly
  - Professional
  - Concise

### Email Accounts

**Adding an Account**
1. Click "Add Email Account"
2. Select provider (Gmail, Outlook, Yahoo, IMAP)
3. For OAuth providers, complete the authorization flow
4. For IMAP, enter server details and credentials

**Removing an Account**
Click the trash icon next to any account to disconnect it.

### LLM Settings

**Provider Selection**
- Local (Ollama): Runs on your machine, no API key needed
- OpenAI: Requires API key
- Google Gemini: Requires API key
- Anthropic Claude: Requires API key
- Cohere: Requires API key

**API Keys**
Enter API keys for cloud providers. Keys are encrypted and stored securely.

### Notifications

Configure how you receive notifications:
- **Slack**: Enter webhook URL for Slack notifications
- **Email**: Set notification email address

Click "Test" to verify your configuration.

### Security

**Two-Factor Authentication**
1. Click "Enable 2FA"
2. Scan QR code with authenticator app
3. Enter verification code
4. 2FA is now active

**Change Password**
1. Enter current password
2. Enter new password (min 8 characters)
3. Confirm new password
4. Click "Change Password"

### Appearance

**Theme**
- Light: Light background, dark text
- Dark: Dark background, light text
- System: Follows your OS preference

**Language**
- English
- Romanian (Romana)

## Tips and Best Practices

### Email Management

1. Review urgent emails first thing in the morning
2. Use AI drafts as starting points, always review before sending
3. Archive emails you've handled to keep inbox clean
4. Use the knowledge base to find old emails instead of scrolling

### Calendar

1. Set buffer time between meetings in your preferences
2. Use the conflict detection to avoid double-booking
3. Add descriptions to help the AI understand meeting context

### Knowledge Base

1. Upload important documents for better AI responses
2. Be specific in your questions for better results
3. Check source citations to verify AI answers

### Security

1. Enable 2FA for account protection
2. Use strong, unique passwords
3. Review audit logs periodically
4. Don't share API keys

## Troubleshooting

### Email Not Syncing

1. Check if the account is connected in Settings
2. Try disconnecting and reconnecting the account
3. Verify OAuth tokens haven't expired

### Slow AI Responses

1. Local LLM is slower than cloud providers
2. Consider switching to a cloud LLM for faster responses
3. Check system resources if using local LLM

### Transcription Failed

1. Ensure audio file is in supported format
2. Check file size (max 100MB)
3. Try re-uploading the file

### Can't Find Information

1. Verify the content has been indexed
2. Check indexing status in Dashboard
3. Try rephrasing your question
4. Use more specific keywords

## Keyboard Shortcuts

- `Ctrl/Cmd + K`: Open quick search
- `Ctrl/Cmd + N`: New email draft
- `Ctrl/Cmd + Enter`: Send message/draft
- `Esc`: Close modal/dialog

## Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Review the FAQ in the documentation
3. Open an issue on GitHub
4. Contact support
