---

## DEVQ_FRAMEWORK_ECOSYSTEM

**Description:** Comprehensive framework ecosystem and technology stack guidelines for DevQ.ai projects.

**Target Files:** `requirements.txt`, `package.json`, configuration files

**Always Apply:** true

### Required Backend Stack (Non-Negotiable)

**Core Infrastructure**
- **Authentication**: Better-auth for secure authentication flows
- **Database Migration**: Alembic for SQLAlchemy schema management
- **Database Toolkit**: SQLAlchemy for ORM and database operations
- **Environment Variables**: Python-dotenv for configuration management
- **Logging**: Logfire for comprehensive observability
- **Testing**: PyTest for test-driven development
- **Code Review**: CodeRabbit for automated code analysis

**Web Framework (Primary)**
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **Alternative Consideration**: Based on project requirements

### Computational & Scientific Frameworks

**Genetic Algorithms & Optimization**
```python
# PyGAD integration example
import pygad
import numpy as np
import logfire

def create_genetic_optimizer(
    fitness_function: callable,
    num_generations: int = 100,
    num_parents_mating: int = 4,
    sol_per_pop: int = 8,
    num_genes: int = 10
) -> pygad.GA:
    """Create optimized genetic algorithm instance."""
    
    with logfire.span("GA Initialization"):
        ga_instance = pygad.GA(
            num_generations=num_generations,
            num_parents_mating=num_parents_mating,
            fitness_func=fitness_function,
            sol_per_pop=sol_per_pop,
            num_genes=num_genes,
            gene_type=float,
            parent_selection_type="sss",
            keep_parents=1,
            crossover_type="single_point",
            mutation_type="random",
            mutation_percent_genes=10
        )
        
        logfire.info("Genetic algorithm configured", 
                    generations=num_generations,
                    population_size=sol_per_pop)
    
    return ga_instance
```

**Scientific Computing Stack**
- **NumPy**: Numerical computing foundation
- **Pandas**: Data manipulation and analysis
- **PyTorch**: Deep learning and neural networks
- **PyMC**: Probabilistic programming and Bayesian inference
- **SciComPy**: Scientific computing utilities
- **Game Theory**: Axelrod for strategic analysis
- **Random Forest**: Wildwood for ensemble methods

### Database & Storage Solutions

**Primary Database Stack**
```python
# SurrealDB integration example
import surrealdb
import logfire

class SurrealDBManager:
    """Manage SurrealDB connections and operations."""
    
    def __init__(self, url: str, namespace: str, database: str):
        self.url = url
        self.namespace = namespace
        self.database = database
        self.client = None
    
    async def connect(self):
        """Establish connection to SurrealDB."""
        with logfire.span("SurrealDB Connection"):
            self.client = surrealdb.Surreal()
            await self.client.connect(self.url)
            await self.client.use(self.namespace, self.database)
            
            logfire.info("Connected to SurrealDB",
                        namespace=self.namespace,
                        database=self.database)
    
    async def create_record(self, table: str, data: dict) -> dict:
        """Create new record with logging."""
        with logfire.span("Create Record", table=table):
            result = await self.client.create(table, data)
            logfire.info("Record created", table=table, id=result.get('id'))
            return result
```

**Database Options**
- **SurrealDB**: Multi-model database (graph, document, key-value)
- **Graphiti**: Knowledge graph construction and querying
- **Neo4j**: Graph database for complex relationships
- **Logfire**: Observability data storage and analysis

### Frontend Technology Stack

**Required Frontend Components**
- **Next.js**: React-based web framework with App Router
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn UI**: Component library built on Radix UI
- **Tiptap**: Rich text editor for content creation
- **Anime.js**: Animation library for smooth interactions

**Data Visualization Options**
```typescript
// Visualization framework selection guide
const visualizationFrameworks = {
  // Python-based (for Panel/Streamlit apps)
  python: {
    panel: "Interactive dashboards with Bokeh backend",
    bokeh: "Web-ready interactive visualizations",
    streamlit: "Rapid prototyping and data apps"
  },
  
  // Web-based (for Next.js apps)
  web: {
    d3: "Custom, complex data visualizations",
    recharts: "React-based charts for standard use cases",
    plotly: "Interactive scientific visualizations"
  }
};

// Example: Next.js with Recharts integration
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export function GeneticAlgorithmChart({ data }: { data: any[] }) {
  return (
    <div className="w-full h-96 p-4">
      <LineChart width={800} height={300} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="generation" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="bestFitness" stroke="#8884d8" />
        <Line type="monotone" dataKey="avgFitness" stroke="#82ca9d" />
      </LineChart>
    </div>
  );
}
```

### Specialized Framework Categories

**Agent Frameworks (AI/ML Projects)**
- **Pydantic AI**: Type-safe AI agent development
- **Archon**: Multi-agent orchestration system
- **Flowise**: Visual workflow builder for AI agents
- **AgentSeek**: Intelligent search and discovery agents

**Finance & Trading Frameworks**
```python
# Financial framework integration example
import stripe
import qlib
from plaid.api import plaid_api
import logfire

class FinancialDataManager:
    """Integrate multiple financial data sources."""
    
    def __init__(self):
        self.stripe_client = stripe.StripeClient(api_key="sk_...")
        self.plaid_client = plaid_api.PlaidApi(plaid_configuration)
    
    async def process_payment(self, amount: int, currency: str = "usd") -> dict:
        """Process payment with comprehensive logging."""
        with logfire.span("Payment Processing", amount=amount, currency=currency):
            try:
                payment_intent = await self.stripe_client.payment_intents.create(
                    amount=amount,
                    currency=currency,
                    automatic_payment_methods={"enabled": True}
                )
                
                logfire.info("Payment intent created", 
                           id=payment_intent.id,
                           amount=amount)
                return payment_intent
                
            except Exception as e:
                logfire.error("Payment processing failed", error=str(e))
                raise
```

**Available Finance Tools**
- **Stripe**: Payment processing and subscription management
- **Plaid**: Bank account and transaction data access
- **Qlib**: Quantitative investment research platform
- **Kalshi**: Prediction market data and trading
- **TokenCost**: LLM API cost tracking and optimization
- **Xero**: Accounting and financial management integration

### Data Modeling & Query Frameworks

**Data Pipeline Tools**
```python
# Data modeling with modern tools
from sqlglot import transpile
from linkml import SchemaDefinition
import dbt

# SQL query optimization with SQLGlot
def optimize_query(sql: str, source_dialect: str, target_dialect: str) -> str:
    """Optimize and transpile SQL queries."""
    with logfire.span("Query Optimization"):
        optimized = transpile(sql, read=source_dialect, write=target_dialect)[0]
        logfire.info("Query optimized", 
                    original_length=len(sql),
                    optimized_length=len(optimized))
        return optimized

# Schema definition with LinkML
def define_data_schema():
    """Define structured data schema using LinkML."""
    schema = SchemaDefinition(
        id="https://example.org/schema",
        name="genetic-algorithm-results",
        description="Schema for genetic algorithm optimization results"
    )
    return schema
```

**Available Data Tools**
- **dbt**: Data build tool for analytics engineering
- **SQLGlot**: SQL parsing, optimization, and transpilation
- **AgentQL**: Natural language to SQL query generation
- **LinkML**: Schema definition and validation
- **Cube**: Semantic layer for analytics
- **LookML**: Business intelligence modeling language

#### Zed IDE Agent Rules

Combined development workflow guidelines and rule structure for AI-assisted development in Zed IDE with DevQ.ai standard stack.

---

## DEVQ_PROJECT_STACK

**Description:** Standard five-component architecture for all DevQ.ai projects using FastAPI, Logfire, PyTest, TaskMaster AI, and MCP.

**Target Files:** `**/*`

**Always Apply:** true

### Required Project Components

**1. FastAPI Foundation Framework**
- Use FastAPI as the primary web framework for all projects
- Configure with proper dependency injection and middleware
- Implement structured error handling and validation
- Follow REST API design principles with OpenAPI documentation

**2. Logfire Observability**
- Integrate Pydantic Logfire for comprehensive observability
- Configure automatic instrumentation for FastAPI, SQLite, and HTTP clients
- Use structured logging with proper context and spans
- Monitor performance, errors, and user interactions

**3. PyTest Build-to-Test Development**
- Implement test-driven development with PyTest
- Create comprehensive test suites covering unit, integration, and API tests
- Use fixtures for database setup and teardown
- Maintain high test coverage with clear test organization

**4. TaskMaster AI Project Management**
- Use TaskMaster AI for task-driven development workflows
- Implement proper task breakdown and dependency management
- Follow iterative development with clear milestones
- Track progress through structured task management

**5. MCP Integration (Custom Registry)**
- Leverage Model Context Protocol for AI-powered development
- Use custom MCP registry for specialized capabilities
- Integrate with development workflow for enhanced productivity
- Maintain consistent MCP server configurations across projects

### Standard File Structure

```
project_root/
├── .claude/
│   └── settings.local.json      # Claude Code permissions and MCP discovery
├── .git/
│   └── config                   # Git configuration with DevQ.ai team settings
├── .logfire/
│   └── logfire_credentials.json # Logfire observability credentials
├── .zed/
│   └── settings.json            # Zed IDE configuration with MCP servers
├── mcp/
│   └── mcp-servers.json         # MCP server registry definitions
├── src/                         # Source code directory
├── tests/                       # PyTest test suite
├── .env                         # Environment variables
├── requirements.txt             # Python dependencies
└── main.py                      # FastAPI application entry point
```

---

## PROJECT_CONFIGURATION_FILES

**Description:** Explicit rules for using standard DevQ.ai project configuration files across all projects.

**Target Files:** Configuration files in project root

**Always Apply:** true

### Required Configuration Files

**1. Claude Code Configuration (`./.claude/settings.local.json`)**
- **Purpose**: Defines Claude Code permissions and enables MCP server auto-discovery
- **Usage**: ALWAYS reference this file for Claude Code tool permissions
- **Key Settings**:
  - `"enableAllProjectMcpServers": true` for MCP auto-discovery
  - Bash command allowlist for security
  - Python execution permissions for development tasks

```json
{
  "permissions": {
    "allow": [
      "Bash(ls:*)", "Bash(source:*)", "Bash(git init:*)",
      "Bash(git config:*)", "Bash(python3:*)", "Bash(grep:*)",
      "Bash(PYTHONPATH=src python3:*)"
    ],
    "deny": []
  }
}
```

**2. Git Configuration (`./.git/config`)**
- **Purpose**: Project-specific Git settings with DevQ.ai team configuration
- **Usage**: ALWAYS use DevQ.ai team identity for commits
- **Required Settings**:
  - User name: "DevQ.ai Team"
  - User email: "dion@devq.ai"
  - Remote origin pointing to appropriate DevQ.ai repository

```ini
[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
    logallrefupdates = true
[remote "origin"]
    url = https://github.com/devq-ai/{project-name}.git
    fetch = +refs/heads/*:refs/remotes/origin/*
[user]
    name = DevQ.ai Team
    email = dion@devq.ai
```

**3. Logfire Credentials (`./.logfire/logfire_credentials.json`)**
- **Purpose**: Pydantic Logfire observability credentials and project configuration
- **Usage**: ALWAYS reference for Logfire integration setup
- **Contains**: Project token, name, URL, and API endpoint
- **Security**: Keep credentials secure, reference via environment variables when possible

```json
{
  "token": "pylf_v1_us_...",
  "project_name": "devq-ai-{project}",
  "project_url": "https://logfire-us.pydantic.dev/devq-ai/devq-ai-{project}",
  "logfire_api_url": "https://logfire-us.pydantic.dev"
}
```

**4. Zed IDE Configuration (`./.zed/settings.json`)**
- **Purpose**: Zed editor settings with terminal configuration and MCP server definitions
- **Usage**: ALWAYS configure Zed for DevQ.ai development environment
- **Key Features**:
  - Terminal configuration with DevQ.ai environment sourcing
  - MCP servers for TaskMaster AI and Dart integration
  - Python/TypeScript formatting and LSP settings
  - Project-specific environment variables

```json
{
  "terminal": {
    "shell": {
      "program": "/bin/zsh",
      "args": ["-l", "-c", "export DEVQAI_ROOT=/Users/dionedge/devqai && cd $DEVQAI_ROOT && source ~/.zshrc && source .zshrc.devqai 2>/dev/null || true && zsh -i"]
    },
    "env": {
      "DEVQAI_ROOT": "/Users/dionedge/devqai",
      "PYTHONPATH": "/Users/dionedge/devqai:$PYTHONPATH"
    }
  },
  "mcpServers": {
    "taskmaster-ai": {
      "command": "npx",
      "args": ["-y", "--package=task-master-ai", "task-master-ai"],
      "env": {
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
        "MODEL": "claude-3-7-sonnet-20250219"
      }
    }
  }
}
```

---

## DEVQ_BACKEND_STANDARDS

**Description:** Comprehensive backend development standards following DevQ.ai patterns and best practices.

**Target Files:** `src/**/*.py`, `main.py`, `tests/**/*.py`, `app/**/*.py`

**Always Apply:** true

### Python Configuration (Standard)

**Version & Formatting**
- **Python Version**: 3.12
- **Formatter**: Black (88 character line length)
- **Import Order**: typing → standard library → third-party → first-party → local
- **Type Hints**: Required for all functions and classes
- **Docstrings**: Google-style format for all public functions

### FastAPI Application Structure (Required)

**Standard Project Layout**
```
app/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   └── dependencies/
├── core/
│   ├── config.py
│   └── security.py
├── db/
│   ├── models/
│   └── repositories/
├── schemas/
├── services/
└── main.py
```

**FastAPI Foundation Setup**
```python
# main.py - Standard FastAPI application entry point
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logfire
from contextlib import asynccontextmanager

# Configure Logfire observability (Required)
logfire.configure(token='pylf_v1_us_...')  # From .logfire/logfire_credentials.json

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logfire.info("Application starting up")
    yield
    # Shutdown
    logfire.info("Application shutting down")

app = FastAPI(
    title="DevQ.ai Project",
    description="API built with FastAPI + Logfire + TaskMaster AI",
    version="1.0.0",
    lifespan=lifespan
)

# Enable Logfire instrumentation (Required)
logfire.instrument_fastapi(app, capture_headers=True)
logfire.instrument_sqlite3()
logfire.instrument_httpx()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Practices (Standard)

**SQLAlchemy Configuration**
```python
# database.py - Database configuration
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logfire

# Instrument SQLAlchemy
logfire.instrument_sqlalchemy()

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"  # or PostgreSQL/SurrealDB
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

async def get_db():
    """Database dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Repository Pattern**
```python
# repositories/base.py - Base repository pattern
from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def create(self, obj_in: dict) -> ModelType:
        """Create new database record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def get(self, id: int) -> Optional[ModelType]:
        """Get record by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()
```

### Testing Requirements (Build-to-Test)

**PyTest Configuration**
```python
# conftest.py - Comprehensive test configuration
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logfire

from main import app, get_db
from database import Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_session():
    """Create a database session for testing."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

**Test Coverage Requirements**
- **Minimum Coverage**: 90% line coverage
- **Integration Tests**: All API endpoints must have integration tests
- **Unit Tests**: All business logic functions must have unit tests
- **Mock External Services**: Use pytest-mock for external dependencies

### Security Standards (Required)

**Authentication & Authorization**
```python
# security.py - Security utilities
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import logfire

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key"  # From environment
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logfire.info("Access token created", user=data.get("sub"))
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)
```

### Error Handling & Validation (Standard)

**Centralized Error Handling**
```python
# exceptions.py - Application-wide error handling
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logfire

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logfire.error(
        "HTTP Exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logfire.error("Validation Error", errors=exc.errors(), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation failed", "details": exc.errors()}
    )
```

**Pydantic Models for Validation**
```python
# schemas/user.py - Request/Response models
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Performance & Monitoring (Required)

**Logfire Integration Patterns**
```python
# monitoring.py - Performance monitoring
import time
import logfire
from fastapi import Request

@app.middleware("http")
async def performance_monitoring(request: Request, call_next):
    start_time = time.time()
    
    with logfire.span(
        "HTTP Request",
        method=request.method,
        url=str(request.url),
        user_agent=request.headers.get("user-agent")
    ):
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logfire.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response

# Health check endpoint (Required)
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    with logfire.span("Health check"):
        checks = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "checks": {
                "database": await check_database_connection(),
                "external_apis": await check_external_services()
            }
        }
        
        if not all(checks["checks"].values()):
            logfire.warning("Health check failed", checks=checks["checks"])
            raise HTTPException(status_code=503, detail=checks)
        
        return checks
```

### Environment & Configuration (Standard)

**Environment Management**
```python
# config.py - Application configuration
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App settings
    app_name: str = "DevQ.ai API"
    debug: bool = False
    version: str = "1.0.0"
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # Security
    secret_key: str
    access_token_expire_minutes: int = 30
    
    # Logfire
    logfire_token: str
    
    # External APIs
    anthropic_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### API Design Standards (Required)

**RESTful Endpoint Patterns**
```python
# api/v1/endpoints/users.py - Standard endpoint structure
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logfire

from database import get_db
from schemas.user import UserCreate, UserResponse
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user."""
    with logfire.span("Create user", email=user.email):
        user_service = UserService(db)
        return user_service.create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user by ID."""
    with logfire.span("Get user", user_id=user_id):
        user_service = UserService(db)
        user = user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
```

### Dependency Management (Required)

**Production Dependencies**
```txt
# requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.0.0
logfire[fastapi]>=0.28.0
sqlalchemy>=2.0.0
alembic>=1.12.0
python-dotenv>=1.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
```

**Development Dependencies**
```txt
# requirements-dev.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
httpx>=0.25.0
black>=23.9.0
isort>=5.12.0
mypy>=1.6.0
ruff>=0.0.280
pre-commit>=3.3.0
```

---

## PROJECT_INITIALIZATION_WORKFLOW

**Description:** Standardized workflow for initializing new DevQ.ai projects with the five-component stack.

**Target Files:** Project root and initialization scripts

**Always Apply:** true

### New Project Setup Checklist

**1. Project Structure Creation**
```bash
# Create standard DevQ.ai project structure
mkdir {project-name}
cd {project-name}

# Initialize core directories
mkdir -p src tests .claude .logfire .zed mcp docs

# Create essential files
touch main.py requirements.txt .env .gitignore README.md
```

**2. Configuration Files Setup**

Copy and customize the four required configuration files:

```bash
# Copy configurations from DevQ.ai template
cp /Users/dionedge/devqai/.claude/settings.local.json ./.claude/
cp /Users/dionedge/devqai/.zed/settings.json ./.zed/
cp /Users/dionedge/devqai/mcp/mcp-servers.json ./mcp/
cp /Users/dionedge/devqai/.logfire/logfire_credentials.json ./.logfire/
```

**3. Git Repository Initialization**
```bash
# Initialize Git with DevQ.ai team configuration
git init
git config user.name "DevQ.ai Team"
git config user.email "dion@devq.ai"
git remote add origin https://github.com/devq-ai/{project-name}.git
```

**4. Python Environment Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install standard dependencies
pip install fastapi uvicorn pytest logfire pydantic
pip install -r requirements.txt
```

**5. TaskMaster AI Integration**
```bash
# Initialize TaskMaster AI for project management
npx task-master-ai init
# Or use MCP tool: initialize_project
```

### Standard Dependencies (requirements.txt)

```txt
# FastAPI Foundation
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0

# Logfire Observability
logfire[fastapi]>=0.28.0

# Testing Framework
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0  # For async testing

# Database (Optional - add as needed)
sqlalchemy>=2.0.0
alembic>=1.12.0

# Development Tools
black>=23.9.0
isort>=5.12.0
flake8>=6.1.0
mypy>=1.6.0

# TaskMaster AI (Global install recommended)
# npm install -g task-master-ai
```

### Environment Variables Template (.env)

```bash
# FastAPI Configuration
DEBUG=true
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here

# Logfire Configuration
LOGFIRE_TOKEN=pylf_v1_us_...
LOGFIRE_PROJECT_NAME={project-name}
LOGFIRE_SERVICE_NAME={project-name}-api
LOGFIRE_ENVIRONMENT=development

# TaskMaster AI Configuration
ANTHROPIC_API_KEY=sk-ant-...
MODEL=claude-3-7-sonnet-20250219
MAX_TOKENS=64000
TEMPERATURE=0.2
DEFAULT_SUBTASKS=5
DEFAULT_PRIORITY=medium

# Database Configuration (if applicable)
DATABASE_URL=sqlite:///./app.db
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_USERNAME=root
SURREALDB_PASSWORD=root

# MCP Server Configuration
DART_TOKEN=dsa_...
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...
```

### Initial FastAPI Application Template

```python
# main.py - Initial application setup
from fastapi import FastAPI
import logfire
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Logfire
logfire.configure(
    token=os.getenv("LOGFIRE_TOKEN"),
    project_name=os.getenv("LOGFIRE_PROJECT_NAME"),
    service_name=os.getenv("LOGFIRE_SERVICE_NAME"),
    environment=os.getenv("LOGFIRE_ENVIRONMENT", "development")
)

# Create FastAPI application
app = FastAPI(
    title=os.getenv("LOGFIRE_PROJECT_NAME", "DevQ.ai API"),
    description="FastAPI application with Logfire observability",
    version="1.0.0",
    debug=os.getenv("DEBUG", "false").lower() == "true"
)

# Enable Logfire instrumentation
logfire.instrument_fastapi(app, capture_headers=True)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "DevQ.ai API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check with Logfire logging."""
    with logfire.span("Health check"):
        logfire.info("Health check requested")
        return {
            "status": "healthy",
            "service": os.getenv("LOGFIRE_SERVICE_NAME"),
            "environment": os.getenv("LOGFIRE_ENVIRONMENT")
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
```

### Initial Test Suite Template

```python
# tests/test_main.py - Basic test setup
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["status"] == "healthy"

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "environment" in data

@pytest.mark.asyncio
async def test_logfire_integration():
    """Test that Logfire integration is working."""
    # This test ensures Logfire doesn't break the application
    response = client.get("/health")
    assert response.status_code == 200
```

### Post-Initialization Workflow

**1. Verify Configuration**
```bash
# Test FastAPI application
python main.py
# Should start on http://localhost:8000

# Run initial tests
pytest tests/

# Verify Logfire integration
# Check Logfire dashboard for incoming data
```

**2. Initialize TaskMaster AI Development**
```bash
# Create initial project tasks
task-master parse-prd --input=project-requirements.txt
# Or create tasks manually:
task-master add-task --prompt="Set up FastAPI application structure"
task-master add-task --prompt="Implement Logfire observability"
task-master add-task --prompt="Create comprehensive test suite"
```

**3. Commit Initial Setup**
```bash
git add .
git commit -m "Initial DevQ.ai project setup with FastAPI, Logfire, PyTest, TaskMaster AI, and MCP integration"
git push -u origin main
```

---

## DEVELOPMENT_WORKFLOW_INTEGRATION

**Description:** Integrated development workflow combining all five components for optimal productivity.

**Target Files:** Development process and team practices

**Always Apply:** true

### Daily Development Workflow

**1. Session Initialization**
```bash
# Start Zed IDE (automatically loads MCP servers and environment)
zed .

# In Zed terminal, activate development environment
source .zshrc.devqai  # Loads DevQ.ai tools and navigation

# Review current tasks using TaskMaster AI
task-master list  # Or use MCP tool: get_tasks
task-master next   # Or use MCP tool: next_task
```

**2. Feature Development Process**

**Planning Phase**
- Use `analyze_project_complexity` to assess task complexity
- Break down complex tasks with `expand_task --research`
- Review dependencies and priority with `get_task <id>`

**Implementation Phase**
```python
# Start implementation with Logfire span for tracking
with logfire.span("Feature implementation", feature="user-authentication"):
    # Implement feature with proper error handling
    # Write tests as you develop (TDD approach)
    # Use MCP servers for code assistance and automation
```

**Testing Phase**
```bash
# Run tests with coverage
pytest tests/ --cov=src/ --cov-report=html

# Use Logfire to monitor test execution
# Check for performance issues and errors
```

**3. Task Management Integration**

**Progress Tracking**
```bash
# Update task status as work progresses
task-master set-status --id=5 --status=in-progress
task-master set-status --id=5.2 --status=done

# Add new tasks discovered during development
task-master add-task --prompt="Add rate limiting to API endpoints" --priority=high
```

**Implementation Notes**
```bash
# Use TaskMaster AI to log implementation details
task-master update-subtask --id=5.2 --prompt="Implemented JWT authentication with FastAPI security utilities. Used bcrypt for password hashing. Added tests for login/logout functionality."
```

### Quality Assurance Workflow

**1. Code Quality Checks**
```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

**2. Test Coverage and Performance**
```bash
# Comprehensive testing
pytest tests/ --cov=src/ --cov-report=html --cov-fail-under=90

# Performance testing with Logfire monitoring
# Use load testing tools while monitoring Logfire dashboards
```

**3. Observability Validation**
```python
# Ensure proper Logfire integration
def test_logfire_instrumentation():
    """Verify Logfire is properly capturing application metrics."""
    with TestClient(app) as client:
        response = client.get("/api/test-endpoint")
        # Check Logfire dashboard for proper span creation and metrics
        assert response.status_code == 200
```

### Deployment and Production Workflow

**1. Pre-Deployment Checklist**
- [ ] All tests passing with adequate coverage
- [ ] Logfire observability configured for production
- [ ] Environment variables properly configured
- [ ] TaskMaster AI tasks marked as complete
- [ ] MCP server configurations verified

**2. Production Monitoring**
```python
# Production Logfire configuration
logfire.configure(
    token=os.getenv("LOGFIRE_TOKEN"),
    environment="production",
    service_name=f"{project_name}-api",
    sample_rate=0.1  # Adjust based on traffic
)

# Production error handling
@app.exception_handler(Exception)
async def production_exception_handler(request: Request, exc: Exception):
    logfire.error("Production error", error=str(exc), request_url=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "request_id": str(uuid4())}
    )
```

**3. Continuous Improvement**
- Monitor Logfire dashboards for performance issues
- Use TaskMaster AI to track maintenance and improvement tasks
- Leverage MCP servers for automated monitoring and analysis
- Regular code reviews focusing on observability and testing quality

This integrated workflow ensures all five components work together seamlessly, providing comprehensive project management, observability, testing, and development acceleration through AI-assisted tools.

## CURSOR_RULES_STRUCTURE

**Description:** Guidelines for creating and maintaining development rules to ensure consistency and effectiveness across IDE assistants.

**Target Files:** `*.md`, rule files, documentation

**Always Apply:** true

### Required Rule Structure

```markdown
---
description: Clear, one-line description of what the rule enforces
globs: path/to/files/*.ext, other/path/**/*
alwaysApply: boolean
---

- **Main Points in Bold**
  - Sub-points with details
  - Examples and explanations
```

### File References
- Use `[filename](path/to/file)` to reference files
- Example: `[schema.prisma](prisma/schema.prisma)` for code references
- Use descriptive link text for clarity

### Code Examples
- Use language-specific code blocks with clear annotations

```javascript
// ✅ DO: Show good examples
const goodExample = true;

// ❌ DON'T: Show anti-patterns  
const badExample = false;
```

### Rule Content Guidelines
- Start with high-level overview
- Include specific, actionable requirements
- Show examples of correct implementation
- Reference existing code when possible
- Keep rules DRY by referencing other rules

### Best Practices
- Use bullet points for clarity
- Keep descriptions concise
- Include both DO and DON'T examples
- Reference actual code over theoretical examples
- Use consistent formatting across rules

---

## TASKMASTER_WORKFLOW

**Description:** Comprehensive guide for using TaskMaster to manage task-driven development workflows in Zed IDE.

**Target Files:** `**/*`

**Always Apply:** true

### Primary Interaction Methods

**MCP Server Integration (Recommended for Zed)**
- Zed integrates with TaskMaster through MCP server for optimal performance
- Use structured data exchange and rich error handling
- Access via MCP tools: `get_tasks`, `add_subtask`, `expand_task`, etc.
- Restart MCP server if core logic changes in `scripts/modules`

**CLI Fallback**
- Global `task-master` command for direct terminal interaction
- Install globally: `npm install -g task-master-ai` or use `npx task-master-ai`
- All CLI commands mirror MCP tools functionality

### Standard Development Workflow

1. **Project Initialization**
   - Use `initialize_project` MCP tool or `task-master init`
   - Parse PRD with `parse_prd` tool or `task-master parse-prd --input='<prd-file.txt>'`
   - Generate initial tasks.json structure

2. **Session Management**
   - Begin with `get_tasks` tool or `task-master list` to review current state
   - Determine next work with `next_task` tool or `task-master next`
   - View specific details with `get_task` tool or `task-master show <id>`

3. **Task Analysis & Breakdown**
   - Analyze complexity: `analyze_project_complexity` tool or `task-master analyze-complexity --research`
   - Review reports: `complexity_report` tool or `task-master complexity-report`
   - Break down tasks: `expand_task` tool or `task-master expand --id=<id> --force --research`
   - Clear subtasks if needed: `clear_subtasks` tool or `task-master clear-subtasks --id=<id>`

4. **Implementation Process**
   - Select tasks based on dependencies (all marked 'done'), priority, and ID order
   - Implement following task details and project standards
   - Update progress: `set_task_status` tool or `task-master set-status --id=<id> --status=done`
   - Handle drift: `update` tool or `task-master update --from=<id> --prompt="..."`

5. **Maintenance**
   - Add new tasks: `add_task` tool or `task-master add-task --prompt="..." --research`
   - Manage dependencies: `add_dependency`/`remove_dependency` tools
   - Validate structure: `validate_dependencies` and `fix_dependencies` tools
   - Generate files: `generate` tool or `task-master generate`

### Task Structure Fields

- **id**: Unique identifier (Example: `1`, `1.1`)
- **title**: Brief, descriptive title
- **description**: Concise summary of task goals
- **status**: Current state (`pending`, `done`, `deferred`, `in-progress`)
- **dependencies**: IDs of prerequisite tasks with status indicators (✅ done, ⏱️ pending)
- **priority**: Importance level (`high`, `medium`, `low`)
- **details**: In-depth implementation instructions
- **testStrategy**: Verification approach
- **subtasks**: List of smaller, specific tasks

### Configuration Management

**Primary: `.taskmaster/config.json`**
- Managed via `task-master models --setup` command
- Stores AI model selections, parameters, logging level
- View/set via `task-master models` or `models` MCP tool

**Environment Variables (API Keys Only)**
- Store in `.env` for CLI or MCP configuration for Zed
- Required keys: `ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY`, etc.
- Endpoints: `AZURE_OPENAI_ENDPOINT`, `OLLAMA_BASE_URL`

### Iterative Subtask Implementation

1. **Understand Goals**: Use `get_task` to understand subtask requirements
2. **Plan Implementation**: Explore codebase, identify files/functions to modify
3. **Log Planning**: Use `update_subtask` to record detailed implementation plan
4. **Begin Work**: Set status to `in-progress` with `set_task_status`
5. **Refine & Log**: Continuously update subtask with findings and progress
6. **Complete**: Mark as `done` and commit changes with descriptive messages

### Task Analysis Techniques

**Complexity Analysis**
- Focus on tasks with scores 8-10 for detailed breakdown
- Use analysis results for appropriate subtask allocation
- Reports automatically inform expansion recommendations

**Dependency Management**
- Prevent circular dependencies
- Validate before adding/removing relationships
- Maintain proper parent-child relationships
- Use status indicators for quick assessment

---

## DEV_ENVIRONMENT_INTEGRATION

**Description:** Integration guidelines for Zed IDE with DevQ.ai development environment.

**Target Files:** `**/*`

**Always Apply:** true

### Zed Configuration Integration

**MCP Server Configuration**
- Leverage existing `.zed/settings.json` MCP server definitions
- Use comprehensive MCP server registry from `mcp/mcp-servers.json`
- Access 18+ specialized servers for development tasks

**Available MCP Capabilities**
- **Core Development**: filesystem, git, fetch, memory, sequential thinking
- **Knowledge Management**: ptolemies (SurrealDB), context7 (Redis), bayes
- **Web & Automation**: crawl4ai, github, calendar integration
- **Specialized Tools**: dart, shadcn-ui, magic code generation
- **Database Operations**: surrealdb, multi-model operations
- **Constraint Solving**: z3, pysat, minizinc solvers

**Environment Setup**
- Source `.zshrc.devqai` for enhanced terminal commands
- Use zoxide for smart directory navigation (`z`, `zi`, `zz`, `zq`, `zr`)
- Access quick navigation: `ag`, `bayes`, `darwin`, `nash`, `ptolemies`
- Utilize MCP management: `start-context7`, `start-crawl4ai`, `mcp-inspect`

### Project Standards

**Code Formatting**
- Backend: 88 character line length, Black formatter
- Frontend: 100 character line length, single quotes, required semicolons
- Python: 3.12, Black formatter, Google-style docstrings
- TypeScript: Strict mode, ES2022 target

**Documentation Requirements**
- All public APIs must have complete documentation
- Google-style docstrings for Python
- React components with props and state descriptions
- Include code examples for non-trivial functions

**Database Integration**
- **SurrealDB**: Knowledge bases with vector search
- **PostgreSQL**: Default for relational data
- **Redis**: Caching and pub/sub messaging
- **Neo4j**: RAG and Knowledge Graph operations

---

## SELF_IMPROVEMENT

**Description:** Guidelines for continuously improving development rules and workflows.

**Target Files:** `**/*`

**Always Apply:** true

### Rule Improvement Triggers

- New code patterns not covered by existing rules
- Repeated similar implementations across files
- Common error patterns that could be prevented
- New libraries or tools used consistently
- Emerging best practices in the codebase

### Analysis Process

- Compare new code with existing rules
- Identify patterns for standardization
- Check for consistent error handling patterns
- Monitor test patterns and coverage
- Look for external documentation references

### Rule Updates

**Add New Rules When:**
- New technology/pattern used in 3+ files
- Common bugs could be prevented by a rule
- Code reviews repeatedly mention same feedback
- New security or performance patterns emerge

**Modify Existing Rules When:**
- Better examples exist in the codebase
- Additional edge cases discovered
- Related rules have been updated
- Implementation details have changed

### Pattern Recognition Example

```javascript
// If you see repeated patterns like:
const data = await prisma.user.findMany({
  select: { id: true, email: true },
  where: { status: 'ACTIVE' }
});

// Consider adding database optimization rules:
// - Standard select fields
// - Common where conditions
// - Performance optimization patterns
```

### Quality Assurance

- Rules should be actionable and specific
- Examples should come from actual code
- References should be up to date
- Patterns should be consistently enforced

### Continuous Improvement Process

- Monitor code review comments
- Track common development questions
- Update rules after major refactors
- Add links to relevant documentation
- Cross-reference related rules
- Document breaking changes

### Rule Lifecycle Management

**Deprecation Process**
- Mark outdated patterns as deprecated
- Remove rules that no longer apply
- Update references to deprecated rules
- Document migration paths for old patterns

**Documentation Maintenance**
- Keep examples synchronized with code
- Update references to external docs
- Maintain links between related rules
- Version control rule changes

---

## CODE_ANALYSIS_TECHNIQUES

**Description:** Systematic approaches for codebase analysis and refactoring support.

**Target Files:** `**/*`

**Always Apply:** true

### Top-Level Function Analysis

**Purpose**: Understand module structure and plan refactors

**Command Pattern**:
```bash
grep -E "export (function|const) \w+|function \w+\(|const \w+ = \(|module\.exports" --include="*.js" -r ./
```

**Benefits**:
- Quickly identify public API functions
- Compare functions between files during refactoring
- Verify expected functions exist in refactored modules
- Identify duplicate functionality or naming conflicts

**Usage Examples**:
```bash
# Map functions in source file
grep -E "function \w+\(" scripts/dev.js

# Check exports in directory
grep -E "export (function|const)" scripts/modules/

# Find naming conflicts
grep -E "function (get|set|create|update)\w+\(" -r ./
```

**Integration with Workflow**:
1. Start by mapping all functions in source file
2. Create target module files based on function grouping
3. Verify all functions properly migrated
4. Check for unintentional duplications or omissions

### Refactoring Workflow

**Preparation Phase**
- Use function analysis to understand current structure
- Identify logical groupings for modularization
- Plan dependency relationships between modules

**Implementation Phase**
- Create module files with clear responsibility boundaries
- Migrate functions maintaining existing interfaces
- Update import/export statements systematically

**Validation Phase**
- Verify all functions accessible through new structure
- Test functionality preservation
- Update documentation and examples

---

## ERROR_HANDLING_PATTERNS

**Description:** Standardized error handling and validation patterns for robust development.

**Target Files:** `**/*`

**Always Apply:** true

### Agent Tool Usage

- Agent components must implement error handling for all tool usage
- Provide meaningful error messages for debugging
- Handle network timeouts and API failures gracefully
- Log errors with sufficient context for troubleshooting

### API Development

- Endpoints must include proper validation and error responses
- Use consistent error response formats
- Implement rate limiting and abuse prevention
- Document error codes and their meanings

### Database Operations

- Use connection pooling and transaction management
- Handle connection failures and retry logic
- Validate data before database operations
- Implement proper rollback mechanisms

### Frontend Components

- Support both light and dark themes
- Handle loading and error states
- Provide user-friendly error messages
- Implement proper form validation

---

## SECURITY_BEST_PRACTICES

**Description:** Security guidelines for safe development practices.

**Target Files:** `**/*`

**Always Apply:** true

### API Security

- Validate all inputs and sanitize outputs
- Use proper authentication and authorization
- Implement CSRF protection
- Follow OWASP security guidelines

### Data Protection

- Encrypt sensitive data at rest and in transit
- Use environment variables for secrets
- Implement proper access controls
- Regular security audits and updates

### Code Security

- Avoid hardcoded credentials
- Use secure coding practices
- Regular dependency updates
- Static code analysis for vulnerabilities