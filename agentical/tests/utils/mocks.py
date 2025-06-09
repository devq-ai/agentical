"""
Mock Objects for Agentical Tests

This module provides mock implementations of various components, services, and
clients used in the Agentical framework. These mocks are designed to isolate
tests from external dependencies and provide predictable behavior for testing.
"""

from typing import Dict, Any, List, Optional, Union, Callable, Type
import json
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

import pytest
import httpx
from fastapi import FastAPI, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from agentical.agents import (
    BaseAgent,
    AgentMetadata,
    AgentCapability,
    AgentStatus,
    AgentExecutionContext,
    AgentExecutionResult
)
from agentical.core.exceptions import AgenticalError


class MockResponse:
    """Mock implementation of an HTTP response."""
    
    def __init__(
        self,
        status_code: int = 200,
        content: Union[str, bytes, Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        elapsed_ms: float = 50.0
    ):
        """
        Initialize a mock response.
        
        Args:
            status_code: HTTP status code
            content: Response content (string, bytes, or dict)
            headers: Response headers
            cookies: Response cookies
            elapsed_ms: Simulated response time in milliseconds
        """
        self.status_code = status_code
        self._content = content
        self.headers = headers or {}
        self.cookies = cookies or {}
        
        # Create a timedelta for elapsed time
        from datetime import timedelta
        self.elapsed = timedelta(milliseconds=elapsed_ms)
        
        # If content is a dict, convert to JSON string
        if isinstance(self._content, dict):
            self._text = json.dumps(self._content)
            self.headers.setdefault("Content-Type", "application/json")
        else:
            self._text = self._content if isinstance(self._content, str) else ""
    
    @property
    def text(self) -> str:
        """Get response text."""
        return self._text
    
    @property
    def content(self) -> bytes:
        """Get response content as bytes."""
        if isinstance(self._content, bytes):
            return self._content
        return self._text.encode("utf-8")
    
    def json(self) -> Dict[str, Any]:
        """Parse response as JSON."""
        if isinstance(self._content, dict):
            return self._content
        return json.loads(self._text)
    
    def raise_for_status(self):
        """Raise an exception if status code indicates an error."""
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"Mock response error: {self.status_code}",
                request=None,
                response=self
            )


class MockClient:
    """Mock implementation of an HTTP client."""
    
    def __init__(
        self,
        responses: Optional[Dict[str, MockResponse]] = None,
        default_response: Optional[MockResponse] = None,
        raise_for_status: bool = False
    ):
        """
        Initialize a mock client.
        
        Args:
            responses: Mapping of URL patterns to mock responses
            default_response: Default response for unmatched URLs
            raise_for_status: Whether to automatically raise for status
        """
        self.responses = responses or {}
        self.default_response = default_response or MockResponse(
            status_code=200,
            content={"message": "Default mock response"}
        )
        self.raise_for_status = raise_for_status
        self.requests = []  # Track all requests made
    
    def _get_response(self, url: str, method: str) -> MockResponse:
        """Get the appropriate response for a URL and method."""
        # Try exact match first
        key = f"{method}:{url}"
        if key in self.responses:
            return self.responses[key]
        
        # Try method + partial URL match
        for pattern, response in self.responses.items():
            if pattern.startswith(f"{method}:") and pattern.split(":", 1)[1] in url:
                return response
        
        # Return default response
        return self.default_response
    
    def _record_request(self, method: str, url: str, **kwargs):
        """Record a request for later inspection."""
        self.requests.append({
            "method": method,
            "url": url,
            **kwargs
        })
    
    async def get(self, url: str, **kwargs) -> MockResponse:
        """Mock GET request."""
        self._record_request("GET", url, **kwargs)
        response = self._get_response(url, "GET")
        await asyncio.sleep(0.01)  # Simulate network delay
        if self.raise_for_status:
            response.raise_for_status()
        return response
    
    async def post(self, url: str, **kwargs) -> MockResponse:
        """Mock POST request."""
        self._record_request("POST", url, **kwargs)
        response = self._get_response(url, "POST")
        await asyncio.sleep(0.01)  # Simulate network delay
        if self.raise_for_status:
            response.raise_for_status()
        return response
    
    async def put(self, url: str, **kwargs) -> MockResponse:
        """Mock PUT request."""
        self._record_request("PUT", url, **kwargs)
        response = self._get_response(url, "PUT")
        await asyncio.sleep(0.01)  # Simulate network delay
        if self.raise_for_status:
            response.raise_for_status()
        return response
    
    async def delete(self, url: str, **kwargs) -> MockResponse:
        """Mock DELETE request."""
        self._record_request("DELETE", url, **kwargs)
        response = self._get_response(url, "DELETE")
        await asyncio.sleep(0.01)  # Simulate network delay
        if self.raise_for_status:
            response.raise_for_status()
        return response
    
    def add_response(self, method: str, url: str, response: MockResponse):
        """Add a new mock response."""
        self.responses[f"{method}:{url}"] = response
    
    def clear_requests(self):
        """Clear the request history."""
        self.requests = []


class MockKnowledgeBase:
    """Mock implementation of a knowledge base."""
    
    def __init__(self, items: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize a mock knowledge base.
        
        Args:
            items: Initial knowledge items
        """
        self.items = items or []
        self.queries = []  # Track all queries
        
        # Create method mocks
        self.query = AsyncMock(side_effect=self._query)
        self.add_item = AsyncMock(side_effect=self._add_item)
        self.get_item = AsyncMock(side_effect=self._get_item)
        self.delete_item = AsyncMock(side_effect=self._delete_item)
    
    async def _query(self, query_text: str, **kwargs) -> Dict[str, Any]:
        """Execute a mock knowledge query."""
        self.queries.append({
            "query": query_text,
            "params": kwargs,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Match items based on simple string containment
        results = []
        for item in self.items:
            content = item.get("content", "")
            title = item.get("title", "")
            
            if query_text.lower() in content.lower() or query_text.lower() in title.lower():
                results.append(item.copy())
        
        # Sort by simple relevance (substring position)
        results.sort(key=lambda x: min(
            x.get("content", "").lower().find(query_text.lower()) if query_text.lower() in x.get("content", "").lower() else float('inf'),
            x.get("title", "").lower().find(query_text.lower()) if query_text.lower() in x.get("title", "").lower() else float('inf')
        ))
        
        return {
            "query": query_text,
            "results": results[:kwargs.get("limit", 10)],
            "total_results": len(results),
            "search_time": 0.05,
            "sources": list(set(item.get("metadata", {}).get("source", "unknown") for item in results[:5]))
        }
    
    async def _add_item(self, item: Dict[str, Any]) -> str:
        """Add an item to the knowledge base."""
        item_id = item.get("id", f"item_{len(self.items) + 1}")
        item["id"] = item_id
        self.items.append(item)
        return item_id
    
    async def _get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get an item by ID."""
        for item in self.items:
            if item.get("id") == item_id:
                return item.copy()
        return None
    
    async def _delete_item(self, item_id: str) -> bool:
        """Delete an item by ID."""
        initial_length = len(self.items)
        self.items = [item for item in self.items if item.get("id") != item_id]
        return len(self.items) < initial_length
    
    def clear_queries(self):
        """Clear the query history."""
        self.queries = []
        
    def clear_items(self):
        """Clear all items."""
        self.items = []


class MockAgent(BaseAgent):
    """Mock implementation of an agent for testing."""
    
    def __init__(
        self,
        metadata: Optional[AgentMetadata] = None,
        execution_results: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize a mock agent.
        
        Args:
            metadata: Agent metadata
            execution_results: Predefined execution results for operations
        """
        # Create default metadata if not provided
        if metadata is None:
            metadata = AgentMetadata(
                id="mock_agent",
                name="Mock Agent",
                description="A mock agent for testing",
                version="1.0.0",
                capabilities=[
                    AgentCapability(
                        name="test_operation",
                        description="A test operation",
                        input_schema={"type": "object"},
                        required_tools=["memory"],
                        knowledge_domains=["test"]
                    )
                ],
                available_tools=["memory", "text_processing"],
                model="test-model",
                system_prompts=["You are a mock agent for testing"],
                tags=["mock", "test"]
            )
        
        super().__init__(metadata)
        
        self.execution_results = execution_results or []
        self.execution_history = []
        self.operations = []  # Track all operations
    
    async def _execute_operation(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """Execute a mock operation."""
        self.operations.append({
            "operation": context.operation,
            "parameters": context.parameters,
            "execution_id": context.execution_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Look for a matching predefined result
        for result in self.execution_results:
            if result.get("operation") == context.operation:
                await asyncio.sleep(0.05)  # Simulate processing time
                return result.get("result", {"status": "completed", "message": "Mock execution"})
        
        # Default result
        return {
            "status": "completed",
            "message": f"Executed {context.operation}",
            "timestamp": datetime.utcnow().isoformat(),
            "operation": context.operation,
            "parameters": context.parameters
        }
    
    def clear_operations(self):
        """Clear the operation history."""
        self.operations = []


class MockRedisClient:
    """Mock implementation of a Redis client."""
    
    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """
        Initialize a mock Redis client.
        
        Args:
            initial_data: Initial data in the Redis store
        """
        self.data = initial_data or {}
        self.commands = []  # Track all commands
        
        # Set up default TTLs (time to live) for keys
        self.ttls = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        self._record_command("GET", key)
        return self.data.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration."""
        self._record_command("SET", key, value, ex=ex)
        self.data[key] = value
        
        # Set expiration if provided
        if ex is not None:
            self.ttls[key] = ex
        
        return True
    
    async def delete(self, key: str) -> int:
        """Delete a key."""
        self._record_command("DELETE", key)
        if key in self.data:
            del self.data[key]
            return 1
        return 0
    
    async def exists(self, key: str) -> int:
        """Check if a key exists."""
        self._record_command("EXISTS", key)
        return 1 if key in self.data else 0
    
    async def expire(self, key: str, seconds: int) -> int:
        """Set expiration time for a key."""
        self._record_command("EXPIRE", key, seconds)
        if key in self.data:
            self.ttls[key] = seconds
            return 1
        return 0
    
    async def ttl(self, key: str) -> int:
        """Get the time to live for a key."""
        self._record_command("TTL", key)
        if key not in self.data:
            return -2  # Key does not exist
        if key not in self.ttls:
            return -1  # Key exists but has no expiration
        return self.ttls[key]
    
    async def incr(self, key: str) -> int:
        """Increment a key's value."""
        self._record_command("INCR", key)
        if key not in self.data:
            self.data[key] = "0"
        
        try:
            value = int(self.data[key]) + 1
            self.data[key] = str(value)
            return value
        except ValueError:
            # Simulate Redis behavior for non-integer values
            raise ValueError("value is not an integer")
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get a field from a hash."""
        self._record_command("HGET", key, field)
        hash_data = self.data.get(key, {})
        if isinstance(hash_data, dict):
            return hash_data.get(field)
        return None
    
    async def hset(self, key: str, field: str, value: str) -> int:
        """Set a field in a hash."""
        self._record_command("HSET", key, field, value)
        if key not in self.data:
            self.data[key] = {}
        
        hash_data = self.data[key]
        if not isinstance(hash_data, dict):
            hash_data = {}
            self.data[key] = hash_data
        
        is_new = field not in hash_data
        hash_data[field] = value
        return 1 if is_new else 0
    
    async def hmset(self, key: str, mapping: Dict[str, str]) -> bool:
        """Set multiple fields in a hash."""
        self._record_command("HMSET", key, mapping)
        if key not in self.data:
            self.data[key] = {}
        
        hash_data = self.data[key]
        if not isinstance(hash_data, dict):
            hash_data = {}
            self.data[key] = hash_data
        
        hash_data.update(mapping)
        return True
    
    async def zcard(self, key: str) -> int:
        """Get the number of elements in a sorted set."""
        self._record_command("ZCARD", key)
        zset_data = self.data.get(key, {})
        if isinstance(zset_data, dict):
            return len(zset_data)
        return 0
    
    async def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        """Add elements to a sorted set."""
        self._record_command("ZADD", key, mapping)
        if key not in self.data:
            self.data[key] = {}
        
        zset_data = self.data[key]
        if not isinstance(zset_data, dict):
            zset_data = {}
            self.data[key] = zset_data
        
        added = 0
        for member, score in mapping.items():
            is_new = member not in zset_data
            zset_data[member] = score
            if is_new:
                added += 1
        
        return added
    
    async def zrange(self, key: str, start: int, stop: int) -> List[str]:
        """Get elements in a sorted set by index range."""
        self._record_command("ZRANGE", key, start, stop)
        zset_data = self.data.get(key, {})
        if not isinstance(zset_data, dict):
            return []
        
        # Sort by score
        sorted_members = sorted(zset_data.items(), key=lambda x: x[1])
        members = [member for member, _ in sorted_members]
        
        # Handle negative indices
        if start < 0:
            start = max(0, len(members) + start)
        if stop < 0:
            stop = max(0, len(members) + stop)
        else:
            stop = min(stop + 1, len(members))  # Redis is inclusive of stop
        
        return members[start:stop]
    
    async def zrangebyscore(self, key: str, min_score: float, max_score: float, withscores: bool = False) -> Union[List[str], List[Tuple[str, float]]]:
        """Get elements in a sorted set by score range."""
        self._record_command("ZRANGEBYSCORE", key, min_score, max_score, withscores=withscores)
        zset_data = self.data.get(key, {})
        if not isinstance(zset_data, dict):
            return []
        
        # Filter by score
        filtered = [(member, score) for member, score in zset_data.items() if min_score <= score <= max_score]
        
        # Sort by score
        sorted_results = sorted(filtered, key=lambda x: x[1])
        
        if withscores:
            return sorted_results
        return [member for member, _ in sorted_results]
    
    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        """Remove elements in a sorted set by score range."""
        self._record_command("ZREMRANGEBYSCORE", key, min_score, max_score)
        zset_data = self.data.get(key, {})
        if not isinstance(zset_data, dict):
            return 0
        
        # Find members to remove
        to_remove = [member for member, score in zset_data.items() if min_score <= score <= max_score]
        
        # Remove members
        for member in to_remove:
            del zset_data[member]
        
        return len(to_remove)
    
    async def zremrangebyrank(self, key: str, start: int, stop: int) -> int:
        """Remove elements in a sorted set by index range."""
        self._record_command("ZREMRANGEBYRANK", key, start, stop)
        zset_data = self.data.get(key, {})
        if not isinstance(zset_data, dict):
            return 0
        
        # Sort by score
        sorted_members = sorted(zset_data.items(), key=lambda x: x[1])
        members = [member for member, _ in sorted_members]
        
        # Handle negative indices
        if start < 0:
            start = max(0, len(members) + start)
        if stop < 0:
            stop = max(0, len(members) + stop)
        else:
            stop = min(stop + 1, len(members))  # Redis is inclusive of stop
        
        # Find members to remove
        to_remove = members[start:stop]
        
        # Remove members
        for member in to_remove:
            del zset_data[member]
        
        return len(to_remove)
    
    async def info(self) -> Dict[str, str]:
        """Get server information."""
        self._record_command("INFO")
        return {
            "redis_version": "mock_redis_1.0.0",
            "connected_clients": "1",
            "used_memory": "1024",
            "used_memory_human": "1K",
            "keyspace_hits": "100",
            "keyspace_misses": "10",
            "total_commands_processed": str(len(self.commands))
        }
    
    async def ping(self) -> str:
        """Ping the server."""
        self._record_command("PING")
        return "PONG"
    
    async def eval(self, script: str, keys: List[str], args: List[Any]) -> Any:
        """Evaluate a Lua script."""
        self._record_command("EVAL", script, keys, args)
        # This is a simplistic mock that doesn't actually run Lua
        # For testing, we'll implement some common script patterns
        
        if "hmget" in script.lower() and len(keys) == 1 and len(args) >= 2:
            # Simple HMGET script
            key = keys[0]
            fields = args
            hash_data = self.data.get(key, {})
            if isinstance(hash_data, dict):
                return [hash_data.get(field) for field in fields]
            return [None] * len(fields)
        
        if "token bucket" in script.lower() and len(keys) == 1 and len(args) == 3:
            # Token bucket script
            key = keys[0]
            capacity = float(args[0])
            refill_rate = float(args[1])
            now = float(args[2])
            
            # Simple response
            return [1, capacity - 1, capacity - 1]  # [allowed, current, remaining]
        
        # Default response for unknown scripts
        return None
    
    def _record_command(self, command: str, *args, **kwargs):
        """Record a command for later inspection."""
        self.commands.append({
            "command": command,
            "args": args,
            "kwargs": kwargs,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def clear_commands(self):
        """Clear the command history."""
        self.commands = []
    
    def clear_data(self):
        """Clear all data."""
        self.data = {}
        self.ttls = {}


class MockSurrealDB:
    """Mock implementation of a SurrealDB client."""
    
    def __init__(self, initial_data: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize a mock SurrealDB client.
        
        Args:
            initial_data: Initial data in the database
        """
        self.data = initial_data or {}
        self.queries = []  # Track all queries
        self.connected = False
        self.namespace = None
        self.database = None
    
    async def connect(self, url: str) -> None:
        """Connect to the database."""
        self._record_query("CONNECT", url)
        self.connected = True
    
    async def use(self, namespace: str, database: str) -> None:
        """Select namespace and database."""
        self._record_query("USE", namespace, database)
        self.namespace = namespace
        self.database = database
    
    async def select(self, thing: str) -> List[Dict[str, Any]]:
        """Select records from a table."""
        self._record_query("SELECT", thing)
        
        # Parse table name and optional ID
        parts = thing.split(":")
        table = parts[0]
        id_filter = parts[1] if len(parts) > 1 else None
        
        # Get table data
        table_data = self.data.get(table, {})
        
        if id_filter:
            # Select specific record
            record = table_data.get(id_filter)
            return [record] if record else []
        
        # Select all records
        return list(table_data.values())
    
    async def create(self, thing: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a record."""
        self._record_query("CREATE", thing, data)
        
        # Parse table name and optional ID
        parts = thing.split(":")
        table = parts[0]
        record_id = parts[1] if len(parts) > 1 else f"{table}_{len(self.data.get(table, {})) + 1}"
        
        # Create table if it doesn't exist
        if table not in self.data:
            self.data[table] = {}
        
        # Create record
        record = {
            "id": f"{table}:{record_id}",
            **data,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add to table
        self.data[table][record_id] = record
        
        return record
    
    async def update(self, thing: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a record."""
        self._record_query("UPDATE", thing, data)
        
        # Parse table name and ID
        parts = thing.split(":")
        if len(parts) != 2:
            raise ValueError("Update requires both table and ID")
        
        table, record_id = parts
        
        # Check if table and record exist
        if table not in self.data or record_id not in self.data[table]:
            raise ValueError(f"Record {thing} not found")
        
        # Update record
        record = self.data[table][record_id]
        updated_record = {
            **record,
            **data,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.data[table][record_id] = updated_record
        
        return updated_record
    
    async def delete(self, thing: str) -> bool:
        """Delete a record."""
        self._record_query("DELETE", thing)
        
        # Parse table name and optional ID
        parts = thing.split(":")
        
        if len(parts) == 1:
            # Delete entire table
            table = parts[0]
            if table in self.data:
                del self.data[table]
                return True
            return False
        
        # Delete specific record
        table, record_id = parts
        
        # Check if table and record exist
        if table not in self.data or record_id not in self.data[table]:
            return False
        
        # Delete record
        del self.data[table][record_id]
        
        return True
    
    async def query(self, query: str, vars: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Execute a custom query."""
        self._record_query("QUERY", query, vars)
        
        # This is a simplistic mock that doesn't actually parse SQL
        # For testing, we'll implement some common query patterns
        
        # SELECT query
        if query.lower().startswith("select"):
            # Extract table name (very simplistic)
            table_match = query.lower().split("from")[1].strip().split()[0] if "from" in query.lower() else None
            
            if table_match and table_match in self.data:
                return list(self.data[table_match].values())
            
            return []
        
        # CREATE query
        if query.lower().startswith("create"):
            # Very simplistic mock response
            return [{"status": "OK", "result": "Record created"}]
        
        # Default response
        return [{"status": "OK", "result": "Query executed"}]
    
    def _record_query(self, operation: str, *args):
        """Record a query for later inspection."""
        self.queries.append({
            "operation": operation,
            "args": args,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def clear_queries(self):
        """Clear the query history."""
        self.queries = []
    
    def clear_data(self):
        """Clear all data."""
        self.data = {}