import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///./documents.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    document_type = Column(String, nullable=False)
    filename = Column(String, nullable=True)
    extracted_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass


async def save_document(doc_id: str, document_type: str, data: dict, filename: str = None):
    async with AsyncSessionLocal() as session:
        doc = Document(
            id=doc_id,
            document_type=document_type,
            filename=filename,
            extracted_data=json.dumps(data),
        )
        session.add(doc)
        await session.commit()


async def delete_document(doc_id: str):
    from sqlalchemy import delete
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Document).where(Document.id == doc_id))
        await session.commit()


async def update_document(doc_id: str, data: dict):
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.extracted_data = json.dumps(data)
            await session.commit()


async def get_all_documents(document_type: str = None):
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        query = select(Document).order_by(Document.created_at.desc())
        if document_type:
            query = query.where(Document.document_type == document_type)
        result = await session.execute(query)
        docs = result.scalars().all()
        return [
            {
                "id": d.id,
                "document_type": d.document_type,
                "filename": d.filename,
                "created_at": d.created_at.isoformat(),
                "data": json.loads(d.extracted_data),
            }
            for d in docs
        ]