# Knowledge Base in Agentical Framework

## Overview

The `knowledge` directory contains the components for Agentical's knowledge management system, powered by SurrealDB. This module provides a persistent storage system for both system operations and agent tools, enabling semantic search and retrieval of information.

## Directory Structure

```
knowledge/
├── __init__.py             # Package initialization
├── base.py                 # Base knowledge classes
├── surrealdb/              # SurrealDB implementation
│   ├── __init__.py
│   ├── client.py           # SurrealDB client
│   ├── models.py           # SurrealDB data models
│   ├── schema.py           # Database schema definitions
│   ├── migrations/         # Schema migrations
│   └── queries.py          # Common queries
├── embedding/              # Vector embedding functionality
│   ├── __init__.py
│   ├── models.py           # Embedding models
│   └── service.py          # Embedding service
├── indexing/               # Knowledge indexing
│   ├── __init__.py
│   ├── processors.py       # Content processors
│   └── pipelines.py        # Indexing pipelines
├── retrieval/              # Knowledge retrieval
│   ├── __init__.py
│   ├── engines.py          # Retrieval engines
│   └── ranking.py          # Result ranking
└── sync/                   # Knowledge synchronization
    ├── __init__.py
    ├── sources.py          # Data source connectors
    └── scheduler.py        # Sync scheduling
```

## Core Components

### SurrealDB Integration

The `surrealdb/` directory contains the integration with SurrealDB:

- **Client**: Connect to and interact with SurrealDB
- **Models**: Define data structures for knowledge items
- **Schema**: Define database schema and indexes
- **Migrations**: Manage schema changes
- **Queries**: Common queries for knowledge operations

### Embedding

The `embedding/` directory contains functionality for vector embeddings:

- **Service**: Generate embeddings for text content
- **Models**: Define embedding model interfaces
- **Providers**: Support multiple embedding providers (OpenAI, etc.)

### Indexing

The `indexing/` directory contains components for processing and indexing content:

- **Processors**: Process different content types
- **Pipelines**: Define indexing workflows
- **Filters**: Filter and transform content during indexing

### Retrieval

The `retrieval/` directory contains components for searching and retrieving knowledge:

- **Engines**: Implement different search strategies
- **Ranking**: Rank and score search results
- **Formatting**: Format results for consumption

### Synchronization

The `sync/` directory contains components for keeping the knowledge base up-to-date:

- **Sources**: Connect to external data sources
- **Scheduler**: Schedule regular updates
- **Transformers**: Transform external data for storage

## Data Model

The knowledge base uses the following core data models:

- **KnowledgeItem**: The main unit of stored information
- **Tag**: Categorization for knowledge items
- **KnowledgeRelation**: Relationships between knowledge items
- **KnowledgeSearch**: Parameters for search requests
- **SchemaVersion**: Tracking for database schema versions

## Key Features

### Semantic Search

The knowledge base supports semantic search using vector embeddings:

- **Query Embedding**: Convert queries to vector embeddings
- **Vector Similarity**: Find semantically similar content
- **Filtering**: Apply filters for tags, content types, etc.
- **Ranking**: Rank results by relevance score

### Knowledge Management

Comprehensive functionality for knowledge management:

- **CRUD Operations**: Create, read, update, delete knowledge items
- **Batch Processing**: Process multiple items efficiently
- **Versioning**: Track changes to knowledge items
- **Tagging**: Organize knowledge with tags

### Agent Integration

The knowledge base is designed to integrate with agents:

- **Knowledge Retrieval Tools**: Enable agents to query the knowledge base
- **Context Enrichment**: Provide relevant knowledge to agent contexts
- **Tool-based Access**: Access knowledge through standard tool interfaces

## Usage Examples

### Storing Knowledge

```python
from agentical.knowledge import KnowledgeService
from agentical.knowledge.surrealdb.models import KnowledgeItem

# Store information in the knowledge base
knowledge_service = KnowledgeService()
await knowledge_service.store(
    KnowledgeItem(
        title="Quantum Computing Basics",
        content="Quantum computing leverages quantum mechanics principles...",
        tags=["quantum", "computing", "technology"]
    )
)
```

### Retrieving Knowledge

```python
# Retrieve information using semantic search
results = await knowledge_service.search(
    query="How do quantum computers work?",
    limit=5,
    min_score=0.7,
    tags=["quantum"]
)

# Use in an agent tool
@agent.tool_plain("knowledge_retrieve")
async def retrieve_knowledge(query: str, limit: int = 5):
    results = await knowledge_service.search(query, limit=limit)
    return format_results(results)
```

## Configuration

The knowledge base can be configured through:

- **Environment Variables**: Set connection parameters
- **Configuration File**: Detailed configuration options
- **Runtime Configuration**: Dynamic configuration changes

## Extension Points

The knowledge module can be extended in several ways:

1. **New Embedding Models**: Add support for additional embedding providers
2. **Custom Content Processors**: Create processors for specific content types
3. **Specialized Retrieval Engines**: Implement domain-specific search strategies
4. **External Data Sources**: Add connectors for new data sources

## Best Practices

1. Use embeddings appropriate for your domain
2. Index content in batches for efficiency
3. Set appropriate filters for targeted retrieval
4. Monitor embedding and search performance
5. Implement caching for frequently accessed knowledge
6. Keep embeddings up to date with model changes
7. Use tags consistently for effective organization

## Related Components

- **Agents**: Use the knowledge base for information retrieval
- **Tools**: Knowledge retrieval tools for agents
- **API**: Endpoints for knowledge management