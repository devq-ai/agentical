"""
Database Connection Pool for Agentical

High-performance database connection pool for SurrealDB with:
- Connection pooling and management
- Health checks and automatic recovery
- Query optimization and caching
- Performance monitoring and metrics
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import logfire
try:
    import surrealdb
    SURREALDB_AVAILABLE = True
except ImportError:
    SURREALDB_AVAILABLE = False
    surrealdb = None

logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    """Database connection configuration"""
    url: str = "ws://localhost:8000/rpc"
    username: str = "root"
    password: str = "root"
    namespace: str = "ptolemies"
    database: str = "knowledge"
    max_connections: int = 20
    min_connections: int = 5
    connection_timeout: float = 10.0
    query_timeout: float = 30.0
    health_check_interval: int = 60
    max_retries: int = 3


@dataclass
class ConnectionStats:
    """Connection pool statistics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_query_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_health_check: Optional[datetime] = None
    uptime: timedelta = field(default_factory=lambda: timedelta(0))


class PooledConnection:
    """Wrapper for pooled database connection"""
    
    def __init__(self, connection: Any, pool: 'DatabasePool'):
        self.connection = connection
        self.pool = pool
        self.created_at = datetime.utcnow()
        self.last_used = datetime.utcnow()
        self.query_count = 0
        self.is_healthy = True
        self.in_use = False
    
    async def execute(self, query: str, **kwargs) -> Any:
        """Execute query with monitoring"""
        start_time = time.time()
        
        try:
            with logfire.span("Database query", query=query[:100]):
                result = await self.connection.query(query, **kwargs)
                
            execution_time = time.time() - start_time
            self.last_used = datetime.utcnow()
            self.query_count += 1
            
            # Update pool statistics
            self.pool._update_query_stats(execution_time, True)
            
            logfire.info("Database query executed", 
                        execution_time=execution_time,
                        query_length=len(query))
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.pool._update_query_stats(execution_time, False)
            self.is_healthy = False
            
            logfire.error("Database query failed", 
                         error=str(e),
                         execution_time=execution_time)
            raise
    
    async def health_check(self) -> bool:
        """Check connection health"""
        try:
            await self.connection.query("SELECT 1")
            self.is_healthy = True
            return True
        except Exception:
            self.is_healthy = False
            return False


class DatabasePool:
    """High-performance database connection pool"""
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.stats = ConnectionStats()
        self.connections: List[PooledConnection] = []
        self.available_connections: asyncio.Queue = asyncio.Queue()
        self.connection_semaphore = asyncio.Semaphore(config.max_connections)
        
        # Query result cache
        self.query_cache: Dict[str, tuple] = {}  # query -> (result, timestamp)
        self.cache_ttl = 300  # 5 minutes
        
        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._pool_initialized = False
        self._startup_time = datetime.utcnow()
        
        logger.info(f"Database pool initialized with {config.max_connections} max connections")
    
    async def initialize(self) -> None:
        """Initialize the connection pool"""
        if not SURREALDB_AVAILABLE:
            logger.error("SurrealDB not available - install surrealdb package")
            return
        
        with logfire.span("Database pool initialization"):
            # Create initial connections
            for _ in range(self.config.min_connections):
                try:
                    conn = await self._create_connection()
                    if conn:
                        await self.available_connections.put(conn)
                        self.connections.append(conn)
                        self.stats.total_connections += 1
                        self.stats.idle_connections += 1
                except Exception as e:
                    logger.error(f"Failed to create initial connection: {e}")
                    self.stats.failed_connections += 1
            
            # Start health check monitoring
            self._health_check_task = asyncio.create_task(self._health_monitor())
            self._pool_initialized = True
            
            logfire.info("Database pool initialized", 
                        total_connections=self.stats.total_connections)
    
    async def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new database connection"""
        try:
            if not SURREALDB_AVAILABLE:
                return None
            
            with logfire.span("Creating database connection"):
                db = surrealdb.Surreal()
                await asyncio.wait_for(
                    db.connect(self.config.url),
                    timeout=self.config.connection_timeout
                )
                
                await db.signin({
                    "user": self.config.username,
                    "pass": self.config.password
                })
                
                await db.use(self.config.namespace, self.config.database)
                
                conn = PooledConnection(db, self)
                
                logfire.info("Database connection created successfully")
                return conn
                
        except Exception as e:
            logfire.error("Failed to create database connection", error=str(e))
            return None
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        if not self._pool_initialized:
            await self.initialize()
        
        async with self.connection_semaphore:
            connection = None
            
            try:
                # Try to get an existing connection
                try:
                    connection = await asyncio.wait_for(
                        self.available_connections.get(),
                        timeout=1.0
                    )
                    
                    # Verify connection is healthy
                    if not connection.is_healthy:
                        await self._replace_connection(connection)
                        connection = await self._create_connection()
                        
                except asyncio.TimeoutError:
                    # Create new connection if none available
                    if self.stats.total_connections < self.config.max_connections:
                        connection = await self._create_connection()
                        if connection:
                            self.connections.append(connection)
                            self.stats.total_connections += 1
                
                if connection:
                    connection.in_use = True
                    self.stats.active_connections += 1
                    self.stats.idle_connections -= 1
                    
                    yield connection
                    
                else:
                    raise Exception("No database connections available")
                    
            finally:
                if connection:
                    connection.in_use = False
                    self.stats.active_connections -= 1
                    self.stats.idle_connections += 1
                    
                    # Return connection to pool if healthy
                    if connection.is_healthy:
                        await self.available_connections.put(connection)
                    else:
                        await self._replace_connection(connection)
    
    async def execute_query(self, query: str, use_cache: bool = True, **kwargs) -> Any:
        """Execute query with caching and monitoring"""
        # Check cache first
        if use_cache:
            cached_result = self._get_cached_result(query, kwargs)
            if cached_result is not None:
                self.stats.cache_hits += 1
                return cached_result
        
        self.stats.cache_misses += 1
        
        # Execute query using pooled connection
        async with self.get_connection() as conn:
            result = await conn.execute(query, **kwargs)
            
            # Cache the result if appropriate
            if use_cache and self._is_cacheable_query(query):
                self._cache_result(query, kwargs, result)
            
            return result
    
    def _get_cached_result(self, query: str, params: Dict[str, Any]) -> Optional[Any]:
        """Get cached query result"""
        cache_key = f"{query}:{hash(frozenset(params.items()))}"
        
        if cache_key in self.query_cache:
            result, timestamp = self.query_cache[cache_key]
            
            # Check if cache entry is still valid
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                # Remove expired entry
                del self.query_cache[cache_key]
        
        return None
    
    def _cache_result(self, query: str, params: Dict[str, Any], result: Any) -> None:
        """Cache query result"""
        cache_key = f"{query}:{hash(frozenset(params.items()))}"
        self.query_cache[cache_key] = (result, time.time())
        
        # Limit cache size
        if len(self.query_cache) > 1000:
            # Remove oldest entries
            sorted_items = sorted(
                self.query_cache.items(),
                key=lambda x: x[1][1]
            )
            for key, _ in sorted_items[:100]:
                del self.query_cache[key]
    
    def _is_cacheable_query(self, query: str) -> bool:
        """Determine if query results can be cached"""
        # Only cache SELECT queries, not INSERT/UPDATE/DELETE
        query_lower = query.lower().strip()
        return (
            query_lower.startswith('select') and
            'now()' not in query_lower and
            'current_timestamp' not in query_lower
        )
    
    async def _replace_connection(self, old_connection: PooledConnection) -> None:
        """Replace a failed connection"""
        try:
            # Remove old connection
            if old_connection in self.connections:
                self.connections.remove(old_connection)
                self.stats.total_connections -= 1
                self.stats.failed_connections += 1
            
            # Create replacement
            new_connection = await self._create_connection()
            if new_connection:
                self.connections.append(new_connection)
                self.stats.total_connections += 1
                await self.available_connections.put(new_connection)
                
        except Exception as e:
            logger.error(f"Failed to replace connection: {e}")
    
    async def _health_monitor(self) -> None:
        """Monitor connection health"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                with logfire.span("Database health check"):
                    healthy_connections = 0
                    
                    for conn in self.connections[:]:  # Copy list to avoid modification during iteration
                        if not conn.in_use:
                            is_healthy = await conn.health_check()
                            if is_healthy:
                                healthy_connections += 1
                            else:
                                await self._replace_connection(conn)
                    
                    self.stats.last_health_check = datetime.utcnow()
                    self.stats.uptime = datetime.utcnow() - self._startup_time
                    
                    logfire.info("Database health check completed",
                               healthy_connections=healthy_connections,
                               total_connections=len(self.connections))
                    
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    def _update_query_stats(self, execution_time: float, success: bool) -> None:
        """Update query execution statistics"""
        self.stats.total_queries += 1
        
        if success:
            self.stats.successful_queries += 1
        else:
            self.stats.failed_queries += 1
        
        # Update rolling average query time
        if self.stats.total_queries == 1:
            self.stats.avg_query_time = execution_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.stats.avg_query_time = (
                alpha * execution_time + 
                (1 - alpha) * self.stats.avg_query_time
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive pool statistics"""
        success_rate = (
            (self.stats.successful_queries / self.stats.total_queries * 100)
            if self.stats.total_queries > 0 else 0
        )
        
        cache_hit_rate = (
            (self.stats.cache_hits / (self.stats.cache_hits + self.stats.cache_misses) * 100)
            if (self.stats.cache_hits + self.stats.cache_misses) > 0 else 0
        )
        
        return {
            "pool_stats": {
                "total_connections": self.stats.total_connections,
                "active_connections": self.stats.active_connections,
                "idle_connections": self.stats.idle_connections,
                "failed_connections": self.stats.failed_connections,
                "max_connections": self.config.max_connections
            },
            "query_stats": {
                "total_queries": self.stats.total_queries,
                "successful_queries": self.stats.successful_queries,
                "failed_queries": self.stats.failed_queries,
                "success_rate": success_rate,
                "avg_query_time": self.stats.avg_query_time
            },
            "cache_stats": {
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "cache_hit_rate": cache_hit_rate,
                "cached_queries": len(self.query_cache)
            },
            "health": {
                "last_health_check": self.stats.last_health_check.isoformat() if self.stats.last_health_check else None,
                "uptime_seconds": self.stats.uptime.total_seconds(),
                "pool_initialized": self._pool_initialized
            }
        }
    
    async def close(self) -> None:
        """Close all connections and cleanup"""
        with logfire.span("Database pool shutdown"):
            if self._health_check_task:
                self._health_check_task.cancel()
            
            for conn in self.connections:
                try:
                    if hasattr(conn.connection, 'close'):
                        await conn.connection.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
            
            self.connections.clear()
            self.query_cache.clear()
            
            logfire.info("Database pool closed")


# Global pool instance
_global_pool: Optional[DatabasePool] = None


def get_database_pool() -> DatabasePool:
    """Get or create global database pool"""
    global _global_pool
    if _global_pool is None:
        config = ConnectionConfig(
            url=os.getenv("SURREALDB_URL", "ws://localhost:8000/rpc"),
            username=os.getenv("SURREALDB_USERNAME", "root"),
            password=os.getenv("SURREALDB_PASSWORD", "root"),
            namespace=os.getenv("SURREALDB_NAMESPACE", "ptolemies"),
            database=os.getenv("SURREALDB_DATABASE", "knowledge")
        )
        _global_pool = DatabasePool(config)
    return _global_pool


# Convenience functions
async def execute_query(query: str, use_cache: bool = True, **kwargs) -> Any:
    """Execute query using global pool"""
    pool = get_database_pool()
    return await pool.execute_query(query, use_cache, **kwargs)


async def get_connection():
    """Get connection from global pool"""
    pool = get_database_pool()
    return pool.get_connection()


def get_database_stats() -> Dict[str, Any]:
    """Get database performance statistics"""
    pool = get_database_pool()
    return pool.get_stats()