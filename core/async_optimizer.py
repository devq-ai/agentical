"""
Async Processing Optimizer for Agentical

Advanced async/await optimizations to maximize concurrent processing capabilities
and minimize latency for the Agentical framework.

Features:
- Parallel execution strategies
- Async context managers for resource management
- Optimized I/O operations
- Concurrent tool execution
- Resource pooling and lifecycle management
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Callable, Coroutine, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps

import logfire

logger = logging.getLogger(__name__)


@dataclass
class AsyncConfig:
    """Configuration for async processing optimization"""
    max_concurrent_operations: int = 50
    max_worker_threads: int = 10
    max_worker_processes: int = 4
    operation_timeout: float = 30.0
    batch_size: int = 10
    queue_maxsize: int = 1000


class AsyncTaskManager:
    """Manages async task execution with optimization"""
    
    def __init__(self, config: AsyncConfig = None):
        self.config = config or AsyncConfig()
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_operations)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_worker_threads)
        self.process_pool = ProcessPoolExecutor(max_workers=self.config.max_worker_processes)
        
        # Task tracking
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks = 0
        self.failed_tasks = 0
        
        logger.info(f"AsyncTaskManager initialized with {self.config.max_concurrent_operations} max concurrent operations")
    
    async def execute_with_semaphore(self, coro: Coroutine, task_id: str = None) -> Any:
        """Execute coroutine with semaphore control"""
        async with self.semaphore:
            if task_id:
                task = asyncio.current_task()
                self.active_tasks[task_id] = task
            
            try:
                with logfire.span("Async task execution", task_id=task_id):
                    result = await asyncio.wait_for(
                        coro, 
                        timeout=self.config.operation_timeout
                    )
                
                self.completed_tasks += 1
                return result
                
            except Exception as e:
                self.failed_tasks += 1
                logfire.error("Async task failed", task_id=task_id, error=str(e))
                raise
            finally:
                if task_id and task_id in self.active_tasks:
                    del self.active_tasks[task_id]
    
    async def execute_parallel(self, tasks: List[Coroutine], 
                             return_exceptions: bool = True) -> List[Any]:
        """Execute multiple coroutines in parallel"""
        with logfire.span("Parallel execution", task_count=len(tasks)):
            return await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    
    async def execute_batch(self, tasks: List[Coroutine], 
                          batch_size: int = None) -> List[Any]:
        """Execute tasks in batches to control resource usage"""
        batch_size = batch_size or self.config.batch_size
        results = []
        
        with logfire.span("Batch execution", total_tasks=len(tasks), batch_size=batch_size):
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                batch_results = await self.execute_parallel(batch)
                results.extend(batch_results)
                
                # Small delay between batches to prevent overwhelming
                if i + batch_size < len(tasks):
                    await asyncio.sleep(0.01)
        
        return results
    
    async def execute_with_retry(self, coro: Coroutine, 
                                max_retries: int = 3,
                                backoff_factor: float = 1.0) -> Any:
        """Execute coroutine with retry logic"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await coro
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    delay = backoff_factor * (2 ** attempt)
                    logfire.warning(f"Task failed, retrying in {delay}s", 
                                   attempt=attempt + 1, error=str(e))
                    await asyncio.sleep(delay)
                else:
                    logfire.error("Task failed after all retries", 
                                 attempts=max_retries + 1, error=str(e))
        
        raise last_exception
    
    async def execute_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Execute blocking function in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, func, *args, **kwargs)
    
    async def execute_in_process(self, func: Callable, *args, **kwargs) -> Any:
        """Execute CPU-intensive function in process pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.process_pool, func, *args, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task execution statistics"""
        return {
            "active_tasks": len(self.active_tasks),
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": (
                self.completed_tasks / (self.completed_tasks + self.failed_tasks) * 100
                if (self.completed_tasks + self.failed_tasks) > 0 else 0
            ),
            "semaphore_available": self.semaphore._value,
            "max_concurrent": self.config.max_concurrent_operations
        }
    
    async def close(self):
        """Clean up resources"""
        # Cancel active tasks
        for task in self.active_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        
        # Shutdown executors
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)


# Global task manager
_global_task_manager: Optional[AsyncTaskManager] = None


def get_task_manager() -> AsyncTaskManager:
    """Get or create global task manager"""
    global _global_task_manager
    if _global_task_manager is None:
        _global_task_manager = AsyncTaskManager()
    return _global_task_manager


def async_optimized(max_concurrent: int = None, timeout: float = None):
    """Decorator for async function optimization"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            task_manager = get_task_manager()
            
            # Override config if specified
            if max_concurrent:
                semaphore = asyncio.Semaphore(max_concurrent)
            else:
                semaphore = task_manager.semaphore
            
            async with semaphore:
                coro = func(*args, **kwargs)
                if timeout:
                    return await asyncio.wait_for(coro, timeout=timeout)
                else:
                    return await coro
        
        return wrapper
    return decorator


class AsyncResourcePool:
    """Generic async resource pool for managing connections, clients, etc."""
    
    def __init__(self, resource_factory: Callable, 
                 max_size: int = 20, min_size: int = 5):
        self.resource_factory = resource_factory
        self.max_size = max_size
        self.min_size = min_size
        
        self.pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self.created_resources = 0
        self.pool_lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize the resource pool"""
        async with self.pool_lock:
            for _ in range(self.min_size):
                resource = await self.resource_factory()
                await self.pool.put(resource)
                self.created_resources += 1
    
    @asynccontextmanager
    async def get_resource(self):
        """Get resource from pool"""
        resource = None
        try:
            # Try to get existing resource
            try:
                resource = await asyncio.wait_for(self.pool.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # Create new resource if pool is empty and under limit
                if self.created_resources < self.max_size:
                    async with self.pool_lock:
                        if self.created_resources < self.max_size:
                            resource = await self.resource_factory()
                            self.created_resources += 1
            
            if resource is None:
                # Wait for resource to become available
                resource = await self.pool.get()
            
            yield resource
            
        finally:
            if resource:
                # Return resource to pool
                try:
                    await self.pool.put(resource)
                except asyncio.QueueFull:
                    # Pool is full, discard resource
                    pass


class AsyncAgentOptimizer:
    """Specialized async optimizer for agent operations"""
    
    def __init__(self):
        self.task_manager = get_task_manager()
        
    async def execute_agent_operations_parallel(self, operations: List[Dict[str, Any]]) -> List[Any]:
        """Execute multiple agent operations in parallel"""
        async def execute_single_operation(op_data: Dict[str, Any]) -> Dict[str, Any]:
            agent = op_data["agent"]
            operation = op_data["operation"]
            parameters = op_data.get("parameters", {})
            
            with logfire.span("Parallel agent operation", 
                            agent_id=agent.metadata.id,
                            operation=operation):
                return await agent.execute(operation, parameters)
        
        # Create coroutines for all operations
        coroutines = [execute_single_operation(op) for op in operations]
        
        # Execute in batches for better resource management
        return await self.task_manager.execute_batch(coroutines)
    
    async def execute_tools_concurrent(self, tool_calls: List[Dict[str, Any]]) -> List[Any]:
        """Execute multiple tool calls concurrently"""
        async def execute_tool_call(tool_data: Dict[str, Any]) -> Dict[str, Any]:
            tool_name = tool_data["tool_name"]
            parameters = tool_data.get("parameters", {})
            
            with logfire.span("Concurrent tool execution", tool_name=tool_name):
                # Simulate tool execution (replace with actual tool calls)
                await asyncio.sleep(0.01)  # Simulate tool processing time
                return {
                    "tool_name": tool_name,
                    "result": f"Result from {tool_name}",
                    "parameters": parameters,
                    "execution_time": 0.01
                }
        
        coroutines = [execute_tool_call(call) for call in tool_calls]
        return await self.task_manager.execute_parallel(coroutines)
    
    async def optimize_knowledge_queries(self, queries: List[str]) -> List[Any]:
        """Optimize multiple knowledge base queries"""
        async def execute_knowledge_query(query: str) -> Dict[str, Any]:
            with logfire.span("Optimized knowledge query", query=query[:50]):
                # Simulate knowledge base query (replace with actual implementation)
                await asyncio.sleep(0.005)  # Simulate fast query
                return {
                    "query": query,
                    "results": [f"Result for: {query}"],
                    "execution_time": 0.005
                }
        
        # Execute queries with deduplication
        unique_queries = list(set(queries))
        coroutines = [execute_knowledge_query(q) for q in unique_queries]
        
        results = await self.task_manager.execute_parallel(coroutines)
        
        # Map results back to original query order
        result_map = {r["query"]: r for r in results if isinstance(r, dict)}
        return [result_map.get(q, {"error": "Query failed"}) for q in queries]


class AsyncWorkflowExecutor:
    """Execute complex workflows with async optimization"""
    
    def __init__(self):
        self.task_manager = get_task_manager()
        self.agent_optimizer = AsyncAgentOptimizer()
    
    async def execute_workflow_dag(self, workflow_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute workflow steps as directed acyclic graph"""
        results = {}
        completed_steps = set()
        
        while len(completed_steps) < len(workflow_steps):
            # Find steps that can be executed (dependencies satisfied)
            ready_steps = []
            
            for i, step in enumerate(workflow_steps):
                if i in completed_steps:
                    continue
                    
                dependencies = step.get("depends_on", [])
                if all(dep in completed_steps for dep in dependencies):
                    ready_steps.append((i, step))
            
            if not ready_steps:
                raise Exception("Circular dependency detected in workflow")
            
            # Execute ready steps in parallel
            async def execute_step(step_data: tuple) -> tuple:
                step_idx, step = step_data
                step_id = step.get("id", f"step_{step_idx}")
                
                with logfire.span("Workflow step", step_id=step_id):
                    # Simulate step execution
                    await asyncio.sleep(step.get("duration", 0.01))
                    
                    return step_idx, {
                        "step_id": step_id,
                        "result": f"Completed {step_id}",
                        "execution_time": step.get("duration", 0.01)
                    }
            
            coroutines = [execute_step(step_data) for step_data in ready_steps]
            step_results = await self.task_manager.execute_parallel(coroutines)
            
            # Process results
            for step_idx, result in step_results:
                if isinstance(result, tuple):
                    completed_steps.add(result[0])
                    results[f"step_{result[0]}"] = result[1]
                else:
                    # Handle exceptions
                    completed_steps.add(step_idx)
                    results[f"step_{step_idx}"] = {"error": str(result)}
        
        return {
            "workflow_completed": True,
            "total_steps": len(workflow_steps),
            "step_results": results,
            "execution_strategy": "async_dag"
        }


# Utility functions for async optimization
async def optimize_io_operations(operations: List[Callable]) -> List[Any]:
    """Optimize I/O operations using async execution"""
    task_manager = get_task_manager()
    
    async def wrap_operation(op: Callable) -> Any:
        if asyncio.iscoroutinefunction(op):
            return await op()
        else:
            # Execute blocking operation in thread pool
            return await task_manager.execute_in_thread(op)
    
    coroutines = [wrap_operation(op) for op in operations]
    return await task_manager.execute_parallel(coroutines)


async def get_async_performance_metrics() -> Dict[str, Any]:
    """Get async optimization performance metrics"""
    task_manager = get_task_manager()
    
    return {
        "task_manager_stats": task_manager.get_stats(),
        "async_features": [
            "parallel_execution",
            "batch_processing", 
            "retry_logic",
            "resource_pooling",
            "semaphore_control",
            "timeout_management"
        ],
        "optimization_level": "maximum",
        "timestamp": time.time()
    }