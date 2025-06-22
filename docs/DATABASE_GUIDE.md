# 🗄️ Database Guide - FoodSave AI

## 📋 Overview

The FoodSave AI system uses a PostgreSQL database with SQLAlchemy ORM for data persistence. The database stores user conversations, receipts, products, recipes, and system metadata. This guide covers the database schema, models, configuration, and management.

## 🏗️ Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ conversations : has
    users ||--o{ receipts : uploads
    users ||--o{ pantry_items : owns

    conversations ||--o{ messages : contains
    conversations ||--o{ receipts : references

    receipts ||--o{ receipt_items : contains
    receipt_items ||--o{ products : references

    products ||--o{ pantry_items : stored_as
    products ||--o{ recipe_ingredients : used_in

    recipes ||--o{ recipe_ingredients : contains
    recipes ||--o{ meal_plans : planned_in

    meal_plans ||--o{ meal_plan_items : contains
    categories ||--o{ products : categorizes
    categories ||--o{ recipes : tags
```

### Core Tables

#### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    preferences JSONB DEFAULT '{}'
);
```

#### Conversations
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(100) NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);
```

#### Messages
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    content TEXT NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    agent_used VARCHAR(50),
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);
```

#### Receipts
```sql
CREATE TABLE receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    store_name VARCHAR(255),
    total_amount DECIMAL(10,2),
    purchase_date DATE,
    receipt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_path VARCHAR(500),
    ocr_confidence FLOAT,
    metadata JSONB DEFAULT '{}'
);
```

#### Receipt Items
```sql
CREATE TABLE receipt_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_id UUID REFERENCES receipts(id),
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    category_id UUID REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Products
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category_id UUID REFERENCES categories(id),
    nutritional_info JSONB DEFAULT '{}',
    storage_info JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Pantry Items
```sql
CREATE TABLE pantry_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    product_id UUID REFERENCES products(id),
    quantity DECIMAL(10,3),
    unit VARCHAR(50),
    expiry_date DATE,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);
```

#### Recipes
```sql
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    instructions TEXT,
    cooking_time INTEGER, -- minutes
    difficulty_level INTEGER, -- 1-5
    servings INTEGER,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Recipe Ingredients
```sql
CREATE TABLE recipe_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID REFERENCES recipes(id),
    product_id UUID REFERENCES products(id),
    quantity DECIMAL(10,3),
    unit VARCHAR(50),
    notes TEXT
);
```

#### Categories
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    parent_id UUID REFERENCES categories(id),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Meal Plans
```sql
CREATE TABLE meal_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    plan_date DATE NOT NULL,
    meal_type VARCHAR(20), -- 'breakfast', 'lunch', 'dinner', 'snack'
    recipe_id UUID REFERENCES recipes(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🐍 SQLAlchemy Models

### Base Model
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### User Model
```python
from sqlalchemy import Column, String, UUID, JSON
import uuid

class User(BaseModel):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    preferences = Column(JSON, default={})
```

### Conversation Model
```python
from sqlalchemy import Column, String, UUID, ForeignKey, Text
from sqlalchemy.orm import relationship

class Conversation(BaseModel):
    __tablename__ = 'conversations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    session_id = Column(String(100), nullable=False)
    title = Column(String(255))
    metadata = Column(JSON, default={})

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
```

### Message Model
```python
class Message(BaseModel):
    __tablename__ = 'messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'))
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    agent_used = Column(String(50))
    confidence = Column(Float)
    metadata = Column(JSON, default={})

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
```

### Receipt Model
```python
from sqlalchemy import Column, String, UUID, ForeignKey, Numeric, Date, Float

class Receipt(BaseModel):
    __tablename__ = 'receipts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    store_name = Column(String(255))
    total_amount = Column(Numeric(10, 2))
    purchase_date = Column(Date)
    image_path = Column(String(500))
    ocr_confidence = Column(Float)
    metadata = Column(JSON, default={})

    # Relationships
    user = relationship("User", back_populates="receipts")
    items = relationship("ReceiptItem", back_populates="receipt", cascade="all, delete-orphan")
```

## ⚙️ Database Configuration

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/foodsave_ai
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# Connection Settings
DATABASE_ECHO=false
DATABASE_ECHO_POOL=false
```

### SQLAlchemy Configuration
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

def create_database_engine():
    """Create database engine with optimized settings"""
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=int(os.getenv('DATABASE_POOL_SIZE', 20)),
        max_overflow=int(os.getenv('DATABASE_MAX_OVERFLOW', 30)),
        pool_timeout=int(os.getenv('DATABASE_POOL_TIMEOUT', 30)),
        pool_recycle=int(os.getenv('DATABASE_POOL_RECYCLE', 3600)),
        echo=os.getenv('DATABASE_ECHO', 'false').lower() == 'true',
        echo_pool=os.getenv('DATABASE_ECHO_POOL', 'false').lower() == 'true'
    )
    return engine

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### Async Database Setup
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def create_async_database_engine():
    """Create async database engine"""
    async_engine = create_async_engine(
        DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
        pool_size=20,
        max_overflow=30,
        pool_timeout=30,
        pool_recycle=3600,
        echo=False
    )
    return async_engine

# Async session factory
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

## 🔄 Database Operations

### Repository Pattern
```python
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

class BaseRepository:
    """Base repository with common CRUD operations"""

    def __init__(self, model: Base):
        self.model = model

    async def create(self, db: Session, obj_in: Dict[str, Any]) -> Base:
        """Create new record"""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: Session, id: UUID) -> Optional[Base]:
        """Get record by ID"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Base]:
        """Get multiple records"""
        result = await db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update(self, db: Session, id: UUID, obj_in: Dict[str, Any]) -> Optional[Base]:
        """Update record"""
        await db.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_in)
        )
        await db.commit()
        return await self.get(db, id)

    async def delete(self, db: Session, id: UUID) -> bool:
        """Delete record"""
        result = await db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await db.commit()
        return result.rowcount > 0
```

### Conversation Repository
```python
class ConversationRepository(BaseRepository):
    """Repository for conversation operations"""

    def __init__(self):
        super().__init__(Conversation)

    async def get_by_session_id(self, db: Session, session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID"""
        result = await db.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_user_conversations(self, db: Session, user_id: UUID,
                                   skip: int = 0, limit: int = 50) -> List[Conversation]:
        """Get conversations for a user"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def add_message(self, db: Session, conversation_id: UUID,
                         content: str, role: str, agent_used: str = None) -> Message:
        """Add message to conversation"""
        message = Message(
            conversation_id=conversation_id,
            content=content,
            role=role,
            agent_used=agent_used
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message
```

### Receipt Repository
```python
class ReceiptRepository(BaseRepository):
    """Repository for receipt operations"""

    def __init__(self):
        super().__init__(Receipt)

    async def create_with_items(self, db: Session, receipt_data: Dict[str, Any],
                               items: List[Dict[str, Any]]) -> Receipt:
        """Create receipt with items"""
        # Create receipt
        receipt = await self.create(db, receipt_data)

        # Create receipt items
        for item_data in items:
            item_data['receipt_id'] = receipt.id
            receipt_item = ReceiptItem(**item_data)
            db.add(receipt_item)

        await db.commit()
        await db.refresh(receipt)
        return receipt

    async def get_user_receipts(self, db: Session, user_id: UUID,
                              start_date: date = None, end_date: date = None) -> List[Receipt]:
        """Get receipts for a user with optional date filtering"""
        query = select(Receipt).where(Receipt.user_id == user_id)

        if start_date:
            query = query.where(Receipt.purchase_date >= start_date)
        if end_date:
            query = query.where(Receipt.purchase_date <= end_date)

        query = query.order_by(Receipt.purchase_date.desc())

        result = await db.execute(query)
        return result.scalars().all()
```

## 📊 Query Optimization

### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_receipts_user_id ON receipts(user_id);
CREATE INDEX idx_receipts_purchase_date ON receipts(purchase_date);
CREATE INDEX idx_receipt_items_receipt_id ON receipt_items(receipt_id);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_pantry_items_user_id ON pantry_items(user_id);
CREATE INDEX idx_pantry_items_expiry_date ON pantry_items(expiry_date);
```

### Query Optimization Examples
```python
# Optimized conversation query with eager loading
async def get_conversation_with_messages(db: Session, conversation_id: UUID) -> Conversation:
    """Get conversation with messages using eager loading"""
    result = await db.execute(
        select(Conversation)
        .options(joinedload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    return result.scalar_one_or_none()

# Paginated query with ordering
async def get_recent_conversations(db: Session, user_id: UUID,
                                 page: int = 1, page_size: int = 20) -> List[Conversation]:
    """Get recent conversations with pagination"""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()

# Aggregation query
async def get_user_spending_stats(db: Session, user_id: UUID,
                                start_date: date, end_date: date) -> Dict[str, Any]:
    """Get user spending statistics"""
    result = await db.execute(
        select(
            func.sum(Receipt.total_amount).label('total_spent'),
            func.count(Receipt.id).label('receipt_count'),
            func.avg(Receipt.total_amount).label('avg_receipt')
        )
        .where(
            Receipt.user_id == user_id,
            Receipt.purchase_date >= start_date,
            Receipt.purchase_date <= end_date
        )
    )
    return result.first()._asdict()
```

## 💾 Backup and Restore

### Backup Strategy
```python
import subprocess
from datetime import datetime
import os

class DatabaseBackup:
    """Database backup and restore utilities"""

    def __init__(self, database_url: str, backup_dir: str = "./backups/database"):
        self.database_url = database_url
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    async def create_backup(self) -> str:
        """Create database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.backup_dir}/backup_{timestamp}.sql"

        # Extract connection details
        db_parts = self.database_url.replace('postgresql://', '').split('@')
        user_pass = db_parts[0].split(':')
        host_db = db_parts[1].split('/')

        username = user_pass[0]
        password = user_pass[1]
        host_port = host_db[0].split(':')
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else '5432'
        database = host_db[1]

        # Create backup command
        cmd = [
            'pg_dump',
            f'--host={host}',
            f'--port={port}',
            f'--username={username}',
            f'--dbname={database}',
            '--verbose',
            '--clean',
            '--no-owner',
            '--no-privileges',
            f'--file={backup_file}'
        ]

        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password

        # Execute backup
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            return backup_file
        else:
            raise Exception(f"Backup failed: {result.stderr}")

    async def restore_backup(self, backup_file: str) -> bool:
        """Restore database from backup"""
        # Extract connection details (same as above)
        # ... connection details extraction ...

        # Create restore command
        cmd = [
            'psql',
            f'--host={host}',
            f'--port={port}',
            f'--username={username}',
            f'--dbname={database}',
            '--verbose',
            f'--file={backup_file}'
        ]

        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password

        # Execute restore
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        return result.returncode == 0
```

## 📈 Monitoring

### Database Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

class DatabaseMetrics:
    """Database performance metrics"""

    def __init__(self):
        self.query_count = Counter('database_queries_total', 'Total database queries')
        self.query_duration = Histogram('database_query_duration_seconds', 'Query duration')
        self.connection_count = Gauge('database_connections_active', 'Active connections')
        self.error_count = Counter('database_errors_total', 'Database errors')

    def record_query(self, query_type: str, duration: float, success: bool):
        """Record query metrics"""
        self.query_count.labels(type=query_type).inc()
        self.query_duration.labels(type=query_type).observe(duration)

        if not success:
            self.error_count.labels(type=query_type).inc()
```

### Health Checks
```python
async def check_database_health(db: Session) -> Dict[str, Any]:
    """Check database health and performance"""
    try:
        start_time = time.time()

        # Test basic connectivity
        result = await db.execute(text("SELECT 1"))
        result.fetchone()

        # Test query performance
        result = await db.execute(text("SELECT COUNT(*) FROM conversations"))
        conversation_count = result.scalar()

        # Get connection pool stats
        pool_stats = db.bind.pool.status()

        return {
            "status": "healthy",
            "response_time": time.time() - start_time,
            "conversation_count": conversation_count,
            "pool_size": pool_stats.size,
            "checked_in": pool_stats.checkedin,
            "checked_out": pool_stats.checkedout,
            "overflow": pool_stats.overflow,
            "invalid": pool_stats.invalid
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## 🧪 Testing

### Test Database Setup
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    test_db_url = "postgresql://test_user:test_pass@localhost:5432/foodsave_test"
    engine = create_engine(test_db_url)

    # Run migrations
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)
    command.upgrade(alembic_cfg, "head")

    yield engine

    # Cleanup
    command.downgrade(alembic_cfg, "base")
    engine.dispose()

@pytest.fixture
def test_session(test_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(bind=test_engine)
    session = TestingSessionLocal()

    yield session

    session.rollback()
    session.close()
```

### Repository Tests
```python
class TestConversationRepository:
    """Tests for conversation repository"""

    async def test_create_conversation(self, test_session):
        """Test conversation creation"""
        repo = ConversationRepository()

        conversation_data = {
            "user_id": uuid.uuid4(),
            "session_id": "test_session_123",
            "title": "Test Conversation"
        }

        conversation = await repo.create(test_session, conversation_data)

        assert conversation.id is not None
        assert conversation.session_id == "test_session_123"
        assert conversation.title == "Test Conversation"

    async def test_get_by_session_id(self, test_session):
        """Test getting conversation by session ID"""
        repo = ConversationRepository()

        # Create conversation
        conversation_data = {
            "user_id": uuid.uuid4(),
            "session_id": "test_session_456",
            "title": "Test Conversation"
        }
        created = await repo.create(test_session, conversation_data)

        # Retrieve by session ID
        retrieved = await repo.get_by_session_id(test_session, "test_session_456")

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.session_id == "test_session_456"
```

---

**Last Updated**: 2024-12-21
**Database Version**: 2.0.0
