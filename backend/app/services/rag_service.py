"""RAG service for knowledge base operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.models.email import Email
from app.models.meeting import Meeting
from app.services.llm_service import LLMService


class RAGService:
    """Service for RAG and knowledge base operations."""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: Optional[LLMService] = None,
    ):
        self.db = db
        self.llm_service = llm_service or LLMService()
        self._neo4j_driver = None

    async def get_neo4j_driver(self):
        """Get Neo4j driver instance."""
        if self._neo4j_driver is None:
            from neo4j import AsyncGraphDatabase

            self._neo4j_driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
        return self._neo4j_driver

    async def close(self):
        """Close Neo4j connection."""
        if self._neo4j_driver:
            await self._neo4j_driver.close()

    async def index_email(
        self,
        email_obj: Email,
        user_id: UUID,
    ) -> bool:
        """Index an email in the knowledge graph."""
        try:
            driver = await self.get_neo4j_driver()

            # Get embeddings for email content
            content = f"{email_obj.subject or ''} {email_obj.body_text or ''}"
            embeddings = await self.llm_service.get_embeddings([content])

            async with driver.session() as session:
                # Create Email node
                await session.run(
                    """
                    MERGE (e:Email {id: $email_id})
                    SET e.subject = $subject,
                        e.sender = $sender,
                        e.received_at = $received_at,
                        e.category = $category,
                        e.embedding = $embedding,
                        e.user_id = $user_id
                    """,
                    email_id=str(email_obj.id),
                    subject=email_obj.subject,
                    sender=email_obj.sender,
                    received_at=(
                        email_obj.received_at.isoformat()
                        if email_obj.received_at
                        else None
                    ),
                    category=email_obj.category,
                    embedding=embeddings[0] if embeddings else None,
                    user_id=str(user_id),
                )

                # Create Person node for sender
                if email_obj.sender:
                    sender_email = self._extract_email(email_obj.sender)
                    sender_name = self._extract_name(email_obj.sender)

                    await session.run(
                        """
                        MERGE (p:Person {email: $email})
                        SET p.name = COALESCE(p.name, $name)
                        WITH p
                        MATCH (e:Email {id: $email_id})
                        MERGE (p)-[:SENT]->(e)
                        """,
                        email=sender_email,
                        name=sender_name,
                        email_id=str(email_obj.id),
                    )

                # Create Person nodes for recipients
                if email_obj.recipients:
                    for recipient in email_obj.recipients:
                        recipient_email = self._extract_email(recipient)
                        recipient_name = self._extract_name(recipient)

                        await session.run(
                            """
                            MERGE (p:Person {email: $email})
                            SET p.name = COALESCE(p.name, $name)
                            WITH p
                            MATCH (e:Email {id: $email_id})
                            MERGE (e)-[:SENT_TO]->(p)
                            """,
                            email=recipient_email,
                            name=recipient_name,
                            email_id=str(email_obj.id),
                        )

                # Extract and create Topic nodes
                topics = await self._extract_topics(content)
                for topic in topics:
                    await session.run(
                        """
                        MERGE (t:Topic {name: $topic})
                        WITH t
                        MATCH (e:Email {id: $email_id})
                        MERGE (e)-[:MENTIONS]->(t)
                        """,
                        topic=topic,
                        email_id=str(email_obj.id),
                    )

            # Update email indexed_at
            email_obj.indexed_at = datetime.utcnow()
            await self.db.commit()

            return True

        except Exception as e:
            print(f"Error indexing email: {e}")
            return False

    async def index_document(
        self,
        document: Document,
        user_id: UUID,
    ) -> bool:
        """Index a document in the knowledge graph."""
        try:
            driver = await self.get_neo4j_driver()

            # Get embeddings for document content
            content = document.content_text or ""
            if not content:
                return False

            embeddings = await self.llm_service.get_embeddings([content[:5000]])

            async with driver.session() as session:
                # Create Document node
                result = await session.run(
                    """
                    MERGE (d:Document {id: $doc_id})
                    SET d.filename = $filename,
                        d.file_type = $file_type,
                        d.summary = $summary,
                        d.embedding = $embedding,
                        d.user_id = $user_id,
                        d.created_at = $created_at
                    RETURN elementId(d) as node_id
                    """,
                    doc_id=str(document.id),
                    filename=document.filename,
                    file_type=document.file_type,
                    summary=document.content_summary,
                    embedding=embeddings[0] if embeddings else None,
                    user_id=str(user_id),
                    created_at=document.created_at.isoformat(),
                )

                record = await result.single()
                if record:
                    document.neo4j_node_id = record["node_id"]

                # Extract and create Topic nodes
                topics = await self._extract_topics(content[:2000])
                for topic in topics:
                    await session.run(
                        """
                        MERGE (t:Topic {name: $topic})
                        WITH t
                        MATCH (d:Document {id: $doc_id})
                        MERGE (d)-[:MENTIONS]->(t)
                        """,
                        topic=topic,
                        doc_id=str(document.id),
                    )

            # Update document indexed_at
            document.indexed_at = datetime.utcnow()
            await self.db.commit()

            return True

        except Exception as e:
            print(f"Error indexing document: {e}")
            return False

    async def index_meeting(
        self,
        meeting: Meeting,
        user_id: UUID,
    ) -> bool:
        """Index a meeting in the knowledge graph."""
        try:
            driver = await self.get_neo4j_driver()

            # Get embeddings for meeting content
            content = (
                f"{meeting.title} {meeting.transcript or ''} {meeting.summary or ''}"
            )
            embeddings = await self.llm_service.get_embeddings([content[:5000]])

            async with driver.session() as session:
                # Create Meeting node
                result = await session.run(
                    """
                    MERGE (m:Meeting {id: $meeting_id})
                    SET m.title = $title,
                        m.summary = $summary,
                        m.meeting_date = $meeting_date,
                        m.embedding = $embedding,
                        m.user_id = $user_id
                    RETURN elementId(m) as node_id
                    """,
                    meeting_id=str(meeting.id),
                    title=meeting.title,
                    summary=meeting.summary,
                    meeting_date=(
                        meeting.meeting_date.isoformat()
                        if meeting.meeting_date
                        else None
                    ),
                    embedding=embeddings[0] if embeddings else None,
                    user_id=str(user_id),
                )

                record = await result.single()
                if record:
                    meeting.neo4j_node_id = record["node_id"]

                # Create Person nodes for participants
                if meeting.participants:
                    for participant in meeting.participants:
                        await session.run(
                            """
                            MERGE (p:Person {email: $email})
                            WITH p
                            MATCH (m:Meeting {id: $meeting_id})
                            MERGE (p)-[:ATTENDED]->(m)
                            """,
                            email=participant,
                            meeting_id=str(meeting.id),
                        )

                # Create Topic nodes
                if meeting.topics:
                    for topic in meeting.topics:
                        await session.run(
                            """
                            MERGE (t:Topic {name: $topic})
                            WITH t
                            MATCH (m:Meeting {id: $meeting_id})
                            MERGE (m)-[:DISCUSSES]->(t)
                            """,
                            topic=topic,
                            meeting_id=str(meeting.id),
                        )

            await self.db.commit()
            return True

        except Exception as e:
            print(f"Error indexing meeting: {e}")
            return False

    async def query(
        self,
        query_text: str,
        user_id: UUID,
        include_emails: bool = True,
        include_documents: bool = True,
        include_meetings: bool = True,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """Query the knowledge base."""
        try:
            # Get query embedding
            query_embedding = await self.llm_service.get_embeddings([query_text])

            driver = await self.get_neo4j_driver()
            results = []

            async with driver.session() as session:
                # Search emails
                if include_emails:
                    email_results = await session.run(
                        """
                        MATCH (e:Email)
                        WHERE e.user_id = $user_id AND e.embedding IS NOT NULL
                        WITH e, gds.similarity.cosine(e.embedding, $embedding) AS score
                        WHERE score > 0.5
                        RETURN 'email' as type, e.id as id, e.subject as title,
                               score, e.received_at as date
                        ORDER BY score DESC
                        LIMIT $limit
                        """,
                        user_id=str(user_id),
                        embedding=query_embedding[0] if query_embedding else [],
                        limit=max_results,
                    )

                    async for record in email_results:
                        results.append(
                            {
                                "type": record["type"],
                                "id": record["id"],
                                "title": record["title"],
                                "score": record["score"],
                                "date": record["date"],
                            }
                        )

                # Search documents
                if include_documents:
                    doc_results = await session.run(
                        """
                        MATCH (d:Document)
                        WHERE d.user_id = $user_id AND d.embedding IS NOT NULL
                        WITH d, gds.similarity.cosine(d.embedding, $embedding) AS score
                        WHERE score > 0.5
                        RETURN 'document' as type, d.id as id, d.filename as title,
                               score, d.created_at as date
                        ORDER BY score DESC
                        LIMIT $limit
                        """,
                        user_id=str(user_id),
                        embedding=query_embedding[0] if query_embedding else [],
                        limit=max_results,
                    )

                    async for record in doc_results:
                        results.append(
                            {
                                "type": record["type"],
                                "id": record["id"],
                                "title": record["title"],
                                "score": record["score"],
                                "date": record["date"],
                            }
                        )

                # Search meetings
                if include_meetings:
                    meeting_results = await session.run(
                        """
                        MATCH (m:Meeting)
                        WHERE m.user_id = $user_id AND m.embedding IS NOT NULL
                        WITH m, gds.similarity.cosine(m.embedding, $embedding) AS score
                        WHERE score > 0.5
                        RETURN 'meeting' as type, m.id as id, m.title as title,
                               score, m.meeting_date as date
                        ORDER BY score DESC
                        LIMIT $limit
                        """,
                        user_id=str(user_id),
                        embedding=query_embedding[0] if query_embedding else [],
                        limit=max_results,
                    )

                    async for record in meeting_results:
                        results.append(
                            {
                                "type": record["type"],
                                "id": record["id"],
                                "title": record["title"],
                                "score": record["score"],
                                "date": record["date"],
                            }
                        )

            # Sort by score and limit
            results.sort(key=lambda x: x["score"], reverse=True)
            results = results[:max_results]

            # Generate answer using LLM
            context = await self._build_context(results, user_id)
            answer = await self.llm_service.answer_question(query_text, context)

            return {
                "answer": answer,
                "sources": results,
            }

        except Exception as e:
            print(f"RAG query error: {e}")
            # Fallback to simple text search
            return await self._fallback_search(query_text, user_id, max_results)

    async def _fallback_search(
        self,
        query_text: str,
        user_id: UUID,
        max_results: int,
    ) -> Dict[str, Any]:
        """Fallback to simple database search."""
        results = []
        search_term = f"%{query_text}%"

        # Search emails
        from app.models.email_account import EmailAccount

        accounts_result = await self.db.execute(
            select(EmailAccount.id).where(EmailAccount.user_id == user_id)
        )
        account_ids = [row[0] for row in accounts_result.fetchall()]

        if account_ids:
            emails_result = await self.db.execute(
                select(Email)
                .where(
                    Email.account_id.in_(account_ids),
                    (Email.subject.ilike(search_term))
                    | (Email.body_text.ilike(search_term)),
                )
                .limit(max_results)
            )

            for email_obj in emails_result.scalars():
                results.append(
                    {
                        "type": "email",
                        "id": str(email_obj.id),
                        "title": email_obj.subject or "No Subject",
                        "score": 0.7,
                        "date": (
                            email_obj.received_at.isoformat()
                            if email_obj.received_at
                            else None
                        ),
                    }
                )

        # Search documents
        docs_result = await self.db.execute(
            select(Document)
            .where(
                Document.user_id == user_id,
                (Document.filename.ilike(search_term))
                | (Document.content_text.ilike(search_term)),
            )
            .limit(max_results)
        )

        for doc in docs_result.scalars():
            results.append(
                {
                    "type": "document",
                    "id": str(doc.id),
                    "title": doc.filename,
                    "score": 0.6,
                    "date": doc.created_at.isoformat(),
                }
            )

        # Search meetings
        meetings_result = await self.db.execute(
            select(Meeting)
            .where(
                Meeting.user_id == user_id,
                (Meeting.title.ilike(search_term))
                | (Meeting.transcript.ilike(search_term)),
            )
            .limit(max_results)
        )

        for meeting in meetings_result.scalars():
            results.append(
                {
                    "type": "meeting",
                    "id": str(meeting.id),
                    "title": meeting.title,
                    "score": 0.6,
                    "date": (
                        meeting.meeting_date.isoformat()
                        if meeting.meeting_date
                        else None
                    ),
                }
            )

        return {
            "answer": f"Found {len(results)} results for '{query_text}'",
            "sources": results[:max_results],
        }

    async def _build_context(
        self,
        results: List[Dict[str, Any]],
        user_id: UUID,
    ) -> str:
        """Build context string from search results."""
        context_parts = []

        for result in results[:5]:
            if result["type"] == "email":
                email_result = await self.db.execute(
                    select(Email).where(Email.id == UUID(result["id"]))
                )
                email_obj = email_result.scalar_one_or_none()
                if email_obj:
                    context_parts.append(
                        f"Email: {email_obj.subject}\n{email_obj.body_text[:500] if email_obj.body_text else ''}"
                    )

            elif result["type"] == "document":
                doc_result = await self.db.execute(
                    select(Document).where(Document.id == UUID(result["id"]))
                )
                doc = doc_result.scalar_one_or_none()
                if doc:
                    context_parts.append(
                        f"Document: {doc.filename}\n{doc.content_text[:500] if doc.content_text else ''}"
                    )

            elif result["type"] == "meeting":
                meeting_result = await self.db.execute(
                    select(Meeting).where(Meeting.id == UUID(result["id"]))
                )
                meeting = meeting_result.scalar_one_or_none()
                if meeting:
                    context_parts.append(
                        f"Meeting: {meeting.title}\n{meeting.summary or meeting.transcript[:500] if meeting.transcript else ''}"
                    )

        return "\n\n---\n\n".join(context_parts)

    async def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text using LLM."""
        try:
            prompt = f"""Extract 3-5 main topics from this text. Return only the topics as a comma-separated list.

Text: {text[:1000]}

Topics:"""

            response = await self.llm_service.generate(
                prompt=prompt,
                max_tokens=100,
                temperature=0.3,
            )

            topics = [t.strip() for t in response.split(",")]
            return [t for t in topics if t and len(t) < 50][:5]

        except Exception:
            return []

    def _extract_email(self, email_string: str) -> str:
        """Extract email address from string like 'Name <email@example.com>'."""
        import re

        match = re.search(r"<([^>]+)>", email_string)
        if match:
            return match.group(1).lower()
        return email_string.lower().strip()

    def _extract_name(self, email_string: str) -> str:
        """Extract name from string like 'Name <email@example.com>'."""
        import re

        match = re.search(r"^([^<]+)", email_string)
        if match:
            name = match.group(1).strip()
            if name:
                return name
        return email_string.split("@")[0]

    async def get_graph_data(
        self,
        user_id: UUID,
        node_type: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get knowledge graph data for visualization."""
        try:
            driver = await self.get_neo4j_driver()

            nodes = []
            relationships = []

            async with driver.session() as session:
                # Get nodes
                node_query = """
                    MATCH (n)
                    WHERE n.user_id = $user_id
                """
                if node_type:
                    node_query += f" AND n:{node_type}"
                node_query += """
                    RETURN labels(n)[0] as type, n.id as id, 
                           COALESCE(n.name, n.title, n.subject, n.filename) as name,
                           properties(n) as properties
                    LIMIT $limit
                """

                node_results = await session.run(
                    node_query,
                    user_id=str(user_id),
                    limit=limit,
                )

                async for record in node_results:
                    nodes.append(
                        {
                            "id": record["id"],
                            "type": record["type"],
                            "name": record["name"],
                            "properties": record["properties"],
                        }
                    )

                # Get relationships
                rel_query = """
                    MATCH (a)-[r]->(b)
                    WHERE a.user_id = $user_id OR b.user_id = $user_id
                    RETURN a.id as source, b.id as target, type(r) as type,
                           properties(r) as properties
                    LIMIT $limit
                """

                rel_results = await session.run(
                    rel_query,
                    user_id=str(user_id),
                    limit=limit * 2,
                )

                async for record in rel_results:
                    relationships.append(
                        {
                            "source_id": record["source"],
                            "target_id": record["target"],
                            "type": record["type"],
                            "properties": record["properties"] or {},
                        }
                    )

            return {
                "nodes": nodes,
                "relationships": relationships,
            }

        except Exception as e:
            print(f"Error getting graph data: {e}")
            return {"nodes": [], "relationships": []}
