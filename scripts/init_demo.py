#!/usr/bin/env python3
"""
Demo initialization script for OpenFyxer.
Creates sample data for demonstration purposes.
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import random

API_BASE_URL = "http://localhost:8000/api/v1"

DEMO_USER = {
    "email": "demo@openfyxer.local",
    "password": "DemoPassword123!",
    "full_name": "Demo User",
}

SAMPLE_EMAILS = [
    {
        "subject": "URGENT: Q4 Budget Review Required",
        "sender": "cfo@company.com",
        "body": "Hi,\n\nWe need to review the Q4 budget by end of day. Please prioritize this.\n\nBest,\nJohn",
        "category": "urgent",
    },
    {
        "subject": "Question about project timeline",
        "sender": "client@customer.com",
        "body": "Hello,\n\nCould you please provide an update on the project timeline? We're planning our next quarter.\n\nThanks,\nSarah",
        "category": "to_respond",
    },
    {
        "subject": "Meeting notes from yesterday",
        "sender": "colleague@company.com",
        "body": "Hi team,\n\nAttached are the meeting notes from yesterday's standup. Key points:\n- Sprint progress on track\n- New feature launch next week\n- Team outing planned for Friday\n\nBest,\nMike",
        "category": "fyi",
    },
    {
        "subject": "Weekly Tech Newsletter - Issue #42",
        "sender": "newsletter@techsite.com",
        "body": "Welcome to this week's newsletter!\n\nTop Stories:\n1. AI advances in 2024\n2. New programming languages\n3. Cloud computing trends\n\nRead more at techsite.com",
        "category": "newsletter",
    },
    {
        "subject": "Re: Partnership proposal",
        "sender": "partner@business.com",
        "body": "Thank you for your proposal. We've reviewed it internally and would like to schedule a call to discuss further.\n\nAre you available next Tuesday at 2 PM?\n\nRegards,\nEmma",
        "category": "to_respond",
    },
]

SAMPLE_CALENDAR_EVENTS = [
    {
        "title": "Team Standup",
        "description": "Daily team sync meeting",
        "start_offset_hours": 1,
        "duration_hours": 0.5,
        "location": "Conference Room A",
    },
    {
        "title": "Client Call - Project Review",
        "description": "Quarterly review with client",
        "start_offset_hours": 3,
        "duration_hours": 1,
        "location": "Zoom",
    },
    {
        "title": "Lunch with Marketing Team",
        "description": "Discuss Q1 campaign",
        "start_offset_hours": 5,
        "duration_hours": 1,
        "location": "Cafe Downstairs",
    },
    {
        "title": "Product Planning Session",
        "description": "Plan features for next release",
        "start_offset_hours": 24,
        "duration_hours": 2,
        "location": "Meeting Room B",
    },
]

SAMPLE_MEETINGS = [
    {
        "title": "Project Kickoff Meeting",
        "description": "Initial planning for Q1 project",
        "participants": ["alice@company.com", "bob@company.com", "charlie@company.com"],
        "transcript": """
Alice: Welcome everyone to the project kickoff. Let's discuss our goals for Q1.

Bob: I think we should focus on the customer portal redesign. It's been requested multiple times.

Charlie: Agreed. We also need to improve the API performance. Current response times are too slow.

Alice: Good points. Let's prioritize the portal redesign and allocate 60% of our resources there.

Bob: What about the timeline? Can we deliver by end of March?

Alice: That's ambitious but doable. Let's set March 31st as our target.

Charlie: I'll start on the API optimization this week. Should have initial improvements by next Friday.

Alice: Perfect. Let's reconvene next Monday to check progress. Meeting adjourned.
        """,
        "summary": "Team agreed to prioritize customer portal redesign (60% resources) with March 31st deadline. API optimization to start immediately with initial improvements expected by next Friday.",
        "action_items": [
            "Alice: Create detailed project plan by Wednesday",
            "Bob: Start portal wireframes",
            "Charlie: Begin API optimization, report by Friday",
        ],
    },
]

SAMPLE_DOCUMENTS = [
    {
        "filename": "company_policies.txt",
        "content": """
Company Policies Document

1. Work Hours
   - Standard hours: 9 AM to 5 PM
   - Flexible scheduling available with manager approval
   - Remote work: Up to 3 days per week

2. Time Off
   - Annual leave: 20 days
   - Sick leave: 10 days
   - Personal days: 3 days

3. Expense Policy
   - All expenses over $100 require manager approval
   - Travel bookings through company portal
   - Meal allowance: $50/day for business travel

4. Communication
   - Slack for internal communication
   - Email for external communication
   - Weekly team meetings mandatory
        """,
    },
    {
        "filename": "project_requirements.txt",
        "content": """
Project Requirements - Customer Portal Redesign

1. User Authentication
   - SSO integration with company IdP
   - Multi-factor authentication support
   - Password reset functionality

2. Dashboard
   - Overview of recent orders
   - Account balance display
   - Quick actions menu

3. Order Management
   - View order history
   - Track shipments
   - Request returns

4. Support
   - Live chat integration
   - Ticket submission
   - FAQ section

5. Performance Requirements
   - Page load time < 2 seconds
   - Mobile responsive design
   - 99.9% uptime SLA

Timeline: Q1 2024
Budget: $150,000
        """,
    },
]


async def create_demo_user(client: httpx.AsyncClient) -> str:
    """Create demo user and return access token."""
    print("Creating demo user...")
    
    try:
        response = await client.post(
            f"{API_BASE_URL}/auth/register",
            json=DEMO_USER,
        )
        if response.status_code == 201:
            print("  Demo user created successfully")
        elif response.status_code == 400:
            print("  Demo user already exists, logging in...")
    except Exception as e:
        print(f"  Registration error (may already exist): {e}")
    
    response = await client.post(
        f"{API_BASE_URL}/auth/login",
        data={
            "username": DEMO_USER["email"],
            "password": DEMO_USER["password"],
        },
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("  Logged in successfully")
        return token
    else:
        raise Exception(f"Failed to login: {response.text}")


async def create_sample_emails(client: httpx.AsyncClient, token: str):
    """Create sample emails."""
    print("\nCreating sample emails...")
    headers = {"Authorization": f"Bearer {token}"}
    
    for email in SAMPLE_EMAILS:
        try:
            response = await client.post(
                f"{API_BASE_URL}/emails/demo",
                headers=headers,
                json={
                    "subject": email["subject"],
                    "sender": email["sender"],
                    "body_text": email["body"],
                    "category": email["category"],
                    "received_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 48))).isoformat(),
                },
            )
            if response.status_code in [200, 201]:
                print(f"  Created: {email['subject'][:50]}...")
            else:
                print(f"  Skipped (endpoint may not exist): {email['subject'][:30]}...")
        except Exception as e:
            print(f"  Error creating email: {e}")


async def create_sample_events(client: httpx.AsyncClient, token: str):
    """Create sample calendar events."""
    print("\nCreating sample calendar events...")
    headers = {"Authorization": f"Bearer {token}"}
    
    now = datetime.utcnow()
    
    for event in SAMPLE_CALENDAR_EVENTS:
        try:
            start_time = now + timedelta(hours=event["start_offset_hours"])
            end_time = start_time + timedelta(hours=event["duration_hours"])
            
            response = await client.post(
                f"{API_BASE_URL}/calendar/events",
                headers=headers,
                json={
                    "title": event["title"],
                    "description": event["description"],
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "location": event["location"],
                    "timezone": "UTC",
                },
            )
            if response.status_code in [200, 201]:
                print(f"  Created: {event['title']}")
            else:
                print(f"  Skipped: {event['title']}")
        except Exception as e:
            print(f"  Error creating event: {e}")


async def create_sample_meetings(client: httpx.AsyncClient, token: str):
    """Create sample meetings with transcripts."""
    print("\nCreating sample meetings...")
    headers = {"Authorization": f"Bearer {token}"}
    
    for meeting in SAMPLE_MEETINGS:
        try:
            response = await client.post(
                f"{API_BASE_URL}/meetings",
                headers=headers,
                json={
                    "title": meeting["title"],
                    "description": meeting["description"],
                    "meeting_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "participants": meeting["participants"],
                    "transcript": meeting["transcript"],
                    "summary": meeting["summary"],
                    "action_items": meeting["action_items"],
                    "status": "completed",
                },
            )
            if response.status_code in [200, 201]:
                print(f"  Created: {meeting['title']}")
            else:
                print(f"  Skipped: {meeting['title']}")
        except Exception as e:
            print(f"  Error creating meeting: {e}")


async def create_sample_documents(client: httpx.AsyncClient, token: str):
    """Create sample documents for RAG."""
    print("\nCreating sample documents...")
    headers = {"Authorization": f"Bearer {token}"}
    
    for doc in SAMPLE_DOCUMENTS:
        try:
            files = {
                "file": (doc["filename"], doc["content"].encode(), "text/plain")
            }
            response = await client.post(
                f"{API_BASE_URL}/rag/documents",
                headers=headers,
                files=files,
            )
            if response.status_code in [200, 201]:
                print(f"  Uploaded: {doc['filename']}")
            else:
                print(f"  Skipped: {doc['filename']}")
        except Exception as e:
            print(f"  Error uploading document: {e}")


async def test_rag_query(client: httpx.AsyncClient, token: str):
    """Test RAG query functionality."""
    print("\nTesting RAG query...")
    headers = {"Authorization": f"Bearer {token}"}
    
    queries = [
        "What is the project deadline?",
        "What are the company work hours?",
        "Who are the meeting participants?",
    ]
    
    for query in queries:
        try:
            response = await client.post(
                f"{API_BASE_URL}/rag/query",
                headers=headers,
                json={"query": query},
            )
            if response.status_code == 200:
                result = response.json()
                print(f"  Q: {query}")
                print(f"  A: {result.get('answer', 'No answer')[:100]}...")
            else:
                print(f"  Query skipped: {query[:30]}...")
        except Exception as e:
            print(f"  Error querying: {e}")


async def main():
    """Main demo initialization function."""
    print("=" * 60)
    print("OpenFyxer Demo Initialization")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            health = await client.get(f"{API_BASE_URL.replace('/api/v1', '')}/health")
            if health.status_code != 200:
                print("ERROR: Backend is not running. Start with: docker-compose up -d")
                return
        except Exception:
            print("ERROR: Cannot connect to backend. Start with: docker-compose up -d")
            return
        
        try:
            token = await create_demo_user(client)
            
            await create_sample_emails(client, token)
            await create_sample_events(client, token)
            await create_sample_meetings(client, token)
            await create_sample_documents(client, token)
            await test_rag_query(client, token)
            
            print("\n" + "=" * 60)
            print("Demo initialization complete!")
            print("=" * 60)
            print(f"\nLogin credentials:")
            print(f"  Email: {DEMO_USER['email']}")
            print(f"  Password: {DEMO_USER['password']}")
            print(f"\nAccess the application at: http://localhost:3000")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
