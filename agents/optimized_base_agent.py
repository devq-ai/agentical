"""
Optimized Base Agent for Agentical Framework

Performance-optimized version of the base agent with:
- Sub-100ms response time optimizations
- Advanced caching mechanisms
- Async/await optimizations
- Resource pooling and management
- Lazy loading capabilities
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from abc import ABC, abstractmethod

import logfire
from pydantic import BaseModel, Field

# Import performance cache
try:
    from ..core.performance_cache import (
        get_cache, cached, AgentResponseCache, KnowledgeQueryCache, MCPToolCache
    )
except ImportError:
    # Fallback if performance cache not available
    def cached(prefix: str, ttl: Optional[int] = None):
        def decorator(func):
            return func
        return decorator
    
    class AgentResponseCache:
        async def get_agent_response(self, *args, **kwargs): return None
        async def store_agent_response(self, *args, **kwargs): pass
    
    class KnowledgeQueryCache:
        async def get_knowledge_result(self, *args, **kwargs): return None
        async def store_knowledge_result(self, *args, **kwargs): pass
    
    class MCPToolCache:
        async def get_tool_response(self, *args, **kwargs): return None
        async def store_tool_response(self, *args, **kwargs): pass

# Import base classes
from .base_agent import (
    AgentStatus, AgentCapability, AgentMetadata, 
    AgentExecutionContext, AgentExecutionResult, InfrastructureConnections
)

logger = logging.getLogger(__name__)


class OptimizedAgentMetrics(BaseModel):
    """Performance metrics for optimized agents"""
    total_executions: int = 0
    avg_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    successful_executions: int = 0
    failed_executions: int = 0
    last_optimization_check: datetime = Field(default_factory=datetime.utcnow)


class OptimizedBaseAgent(ABC):
    """
    Performance-optimized base agent with sub-100ms response capabilities
    """
    
    def __init__(self, metadata: AgentMetadata):
        """Initialize optimized agent with performance enhancements"""
        self.metadata = metadata
        self.status = AgentStatus.IDLE
        
        # Performance optimizations
        self.metrics = OptimizedAgentMetrics()
        self.response_cache = AgentResponseCache()
        self.knowledge_cache = KnowledgeQueryCache()
        self.tool_cache = MCPToolCache()
        
        # Pre-computed capabilities map for fast lookup
        self._capabilities_map = {cap.name: cap for cap in metadata.capabilities}
        
        # Lazy-loaded infrastructure
        self._infrastructure: Optional[InfrastructureConnections] = None
        self._tool_clients: Dict[str, Any] = {}
        
        # Performance tracking
        self.execution_history: List[AgentExecutionResult] = []
        self.current_context: Optional[AgentExecutionContext] = None
        
        logger.info(f"Optimized agent '{metadata.name}' initialized with {len(metadata.capabilities)} capabilities")
    
    @property
    def infrastructure(self) -> InfrastructureConnections:
        """Lazy-loaded infrastructure connections"""
        if self._infrastructure is None:
            self._infrastructure = self._initialize_infrastructure()
        return self._infrastructure
    
    def _initialize_infrastructure(self) -> InfrastructureConnections:
        """Initialize infrastructure connections (lazy-loaded)"""
        from .base_agent import BaseAgent
        # Use the existing infrastructure initialization from BaseAgent
        temp_agent = type('TempAgent', (BaseAgent,), {'_execute_operation': lambda self, ctx: {}})
        temp_instance = temp_agent(self.metadata)
        return temp_instance.infrastructure
    
    async def execute(self, operation: str, parameters: Dict[str, Any] = None) -> AgentExecutionResult:
        """
        Execute agent operation with performance optimizations
        """
        start_time = time.time()
        execution_id = f"{self.metadata.id}_{operation}_{int(start_time * 1000)}"
        
        with logfire.span("Optimized agent execution", 
                         agent_id=self.metadata.id, 
                         operation=operation):
            
            # Quick capability check
            if operation not in self._capabilities_map:
                return self._create_error_result(
                    execution_id, operation, 
                    f"Operation {operation} not supported",
                    time.time() - start_time
                )
            
            # Try cache first for eligible operations
            if await self._is_cacheable_operation(operation, parameters):
                cached_result = await self._get_cached_response(operation, parameters)
                if cached_result:
                    logfire.info("Cache hit for agent operation", 
                               operation=operation, cache_time=time.time() - start_time)
                    return self._create_cached_result(execution_id, operation, cached_result, time.time() - start_time)
            
            # Execute with performance monitoring
            try:
                context = AgentExecutionContext(
                    execution_id=execution_id,
                    agent_id=self.metadata.id,
                    operation=operation,
                    parameters=parameters or {}
                )
                
                self.current_context = context
                self.status = AgentStatus.RUNNING
                
                # Pre-fetch knowledge context in parallel if needed
                knowledge_task = None
                if context.parameters.get("use_knowledge", True):
                    knowledge_task = asyncio.create_task(
                        self._gather_knowledge_context_optimized(operation, parameters)
                    )
                
                # Execute the core operation
                result_data = await self._execute_operation_optimized(context)
                
                # Await knowledge context if it was requested
                if knowledge_task:
                    context.knowledge_context = await knowledge_task
                
                execution_time = time.time() - start_time
                
                # Cache successful results
                if await self._is_cacheable_operation(operation, parameters):
                    await self._cache_response(operation, parameters, result_data)
                
                # Update metrics
                self._update_metrics(execution_time, True)
                
                result = AgentExecutionResult(
                    success=True,
                    execution_id=execution_id,
                    agent_id=self.metadata.id,
                    operation=operation,
                    result=result_data,
                    execution_time=execution_time,
                    tools_used=result_data.get("tools_used", []),
                    knowledge_queries=len(context.knowledge_context)
                )
                
                self.status = AgentStatus.COMPLETED
                logfire.info("Optimized execution completed", 
                           execution_time=execution_time, 
                           operation=operation)
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                self._update_metrics(execution_time, False)
                self.status = AgentStatus.ERROR
                
                error_result = self._create_error_result(execution_id, operation, str(e), execution_time)
                logfire.error("Optimized execution failed", 
                            error=str(e), 
                            execution_time=execution_time)
                return error_result
            
            finally:
                self.current_context = None
                self.execution_history.append(result)
    
    async def _is_cacheable_operation(self, operation: str, parameters: Dict[str, Any]) -> bool:
        """Determine if operation results can be cached"""
        # Operations that are read-only and deterministic can be cached
        cacheable_operations = {
            "answer_question", "research_topic", "generate_content", 
            "process_text", "analyze_data"
        }
        
        # Don't cache operations with time-sensitive parameters
        if parameters and any(key in parameters for key in ["timestamp", "current_time", "real_time"]):
            return False
        
        return operation in cacheable_operations
    
    async def _get_cached_response(self, operation: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached response for operation"""
        try:
            return await self.response_cache.get_agent_response(
                self.metadata.id, operation, parameters or {}
            )
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None
    
    async def _cache_response(self, operation: str, parameters: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Cache operation response"""
        try:
            # Determine cache TTL based on operation type
            ttl = 300  # 5 minutes default
            if operation in ["research_topic", "answer_question"]:
                ttl = 1800  # 30 minutes for knowledge-based operations
            elif operation == "generate_content":
                ttl = 600   # 10 minutes for generated content
            
            await self.response_cache.store_agent_response(
                self.metadata.id, operation, parameters or {}, result, ttl
            )
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    @cached("knowledge_context", ttl=1800)
    async def _gather_knowledge_context_optimized(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimized knowledge context gathering with caching"""
        if not self.infrastructure.ptolemies_available:
            return {"error": "Ptolemies knowledge base not available"}
        
        # Check cache first
        query_key = f"{operation}:{json.dumps(parameters, sort_keys=True)}"
        cached_knowledge = await self.knowledge_cache.get_knowledge_result(query_key)
        
        if cached_knowledge:
            return cached_knowledge
        
        # Simulate optimized knowledge retrieval
        knowledge_context = {
            "status": "ptolemies_available",
            "documents_available": 597,
            "operation": operation,
            "retrieval_time": time.time(),
            "note": "Optimized Ptolemies integration with caching"
        }
        
        # Cache the result
        await self.knowledge_cache.store_knowledge_result(
            query_key, knowledge_context, ttl=1800
        )
        
        return knowledge_context
    
    async def _execute_operation_optimized(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """
        Optimized operation execution with parallel processing where possible
        """
        operation = context.operation
        parameters = context.parameters
        
        # Get required tools and validate availability in parallel
        tools_task = asyncio.create_task(self._get_required_tools_fast(operation))
        validation_task = asyncio.create_task(self._validate_tools_fast(operation))
        
        required_tools, tool_validation = await asyncio.gather(tools_task, validation_task)
        
        # Execute the specific operation implementation
        result = await self._execute_operation(context)
        
        # Add performance metadata
        result["performance"] = {
            "execution_time": time.time() - context.started_at.timestamp(),
            "tools_validated": len(tool_validation),
            "cache_enabled": True,
            "optimization_level": "high"
        }
        
        return result
    
    async def _get_required_tools_fast(self, operation: str) -> List[str]:
        """Fast tool requirement lookup using pre-computed map"""
        capability = self._capabilities_map.get(operation)
        if capability:
            return capability.required_tools
        return ["filesystem", "memory"]  # Default tools
    
    async def _validate_tools_fast(self, operation: str) -> List[str]:
        """Fast tool validation using cached infrastructure"""
        required_tools = await self._get_required_tools_fast(operation)
        available_servers = self.infrastructure.mcp_servers.get("mcp_servers", {}) if self.infrastructure.mcp_servers else {}
        
        return [tool for tool in required_tools if tool in available_servers]
    
    def _update_metrics(self, execution_time: float, success: bool) -> None:
        """Update performance metrics"""
        self.metrics.total_executions += 1
        
        if success:
            self.metrics.successful_executions += 1
        else:
            self.metrics.failed_executions += 1
        
        # Update rolling average response time
        if self.metrics.total_executions == 1:
            self.metrics.avg_response_time = execution_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.avg_response_time = (
                alpha * execution_time + 
                (1 - alpha) * self.metrics.avg_response_time
            )
    
    def _create_error_result(self, execution_id: str, operation: str, 
                           error: str, execution_time: float) -> AgentExecutionResult:
        """Create standardized error result"""
        return AgentExecutionResult(
            success=False,
            execution_id=execution_id,
            agent_id=self.metadata.id,
            operation=operation,
            error=error,
            execution_time=execution_time,
            knowledge_queries=0
        )
    
    def _create_cached_result(self, execution_id: str, operation: str, 
                            cached_data: Dict[str, Any], execution_time: float) -> AgentExecutionResult:
        """Create result from cached data"""
        return AgentExecutionResult(
            success=True,
            execution_id=execution_id,
            agent_id=self.metadata.id,
            operation=operation,
            result={**cached_data, "cached": True, "cache_retrieval_time": execution_time},
            execution_time=execution_time,
            tools_used=cached_data.get("tools_used", []),
            knowledge_queries=0  # No new queries for cached results
        )
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        try:
            cache_stats = get_cache().get_stats()
        except:
            cache_stats = {"hit_rate": 0, "hits": 0, "misses": 0}
        
        return {
            "agent_id": self.metadata.id,
            "metrics": self.metrics.dict(),
            "cache_performance": cache_stats,
            "current_status": self.status.value,
            "optimization_features": [
                "response_caching",
                "knowledge_caching", 
                "tool_caching",
                "lazy_loading",
                "parallel_execution",
                "performance_monitoring"
            ]
        }
    
    @abstractmethod
    async def _execute_operation(self, context: AgentExecutionContext) -> Dict[str, Any]:
        """Execute the specific agent operation (must be implemented by subclasses)"""
        pass
    
    async def get_status(self) -> Dict[str, Any]:
        """Get optimized agent status with performance data"""
        base_status = {
            "agent_id": self.metadata.id,
            "name": self.metadata.name,
            "status": self.status.value,
            "current_operation": self.current_context.operation if self.current_context else None,
            "execution_history_count": len(self.execution_history),
        }
        
        # Add performance metrics
        performance_data = await self.get_performance_metrics()
        base_status["performance"] = performance_data
        
        return base_status