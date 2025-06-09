"""
Agent API Endpoints for Agentical Framework

This module provides FastAPI endpoints for interacting with agents in the Agentical
framework, enabling agent creation, listing, execution, and management through
a RESTful API interface.
"""

from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime
import asyncio

import logfire
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from pydantic import BaseModel, Field, constr

from agentical.agents import (
    agent_registry,
    AgentStatus, 
    AgentMetadata,
    AgentCapability,
    AgentExecutionResult
)
from agentical.core.exceptions import (
    AgentNotFoundError,
    AgentExecutionError
)

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/agents",
    tags=["agents"],
    responses={
        404: {"description": "Agent not found"},
        500: {"description": "Internal server error"}
    }
)

# Request and response models
class AgentRequest(BaseModel):
    """Request model for agent execution"""
    agent_id: str = Field(..., description="ID of the agent to execute")
    operation: str = Field(..., description="Operation to execute")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Operation parameters")
    use_knowledge: bool = Field(default=True, description="Whether to use knowledge base")
    tools: Optional[List[str]] = Field(default=None, description="Tools to use for execution")


class AgentResponse(BaseModel):
    """Response model for agent execution"""
    success: bool = Field(..., description="Whether execution was successful")
    agent_id: str = Field(..., description="ID of the agent that executed")
    operation: str = Field(..., description="Operation that was executed")
    result: Dict[str, Any] = Field(..., description="Result of the execution")
    execution_time: float = Field(..., description="Time taken for execution in seconds")
    tools_used: List[str] = Field(default_factory=list, description="Tools used during execution")
    knowledge_queries: int = Field(default=0, description="Number of knowledge queries executed")


class AgentListItem(BaseModel):
    """Model for agent list item"""
    id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type")
    status: str = Field(..., description="Agent status")
    description: str = Field(..., description="Agent description")
    capabilities_count: int = Field(..., description="Number of capabilities")


class AgentDetail(BaseModel):
    """Model for agent detail"""
    id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent name")
    type: str = Field(..., description="Agent type")
    status: str = Field(..., description="Agent status")
    description: str = Field(..., description="Agent description")
    version: str = Field(..., description="Agent version")
    capabilities: List[Dict[str, Any]] = Field(..., description="Agent capabilities")
    available_tools: List[str] = Field(..., description="Available tools")
    model: Optional[str] = Field(default=None, description="Model used by the agent")
    execution_history_count: int = Field(..., description="Number of executions in history")
    infrastructure: Dict[str, Any] = Field(..., description="Infrastructure connections")


class CreateAgentRequest(BaseModel):
    """Request model for agent creation"""
    agent_id: constr(min_length=3, max_length=50) = Field(..., description="Agent ID")
    agent_type: str = Field(..., description="Agent type")
    name: Optional[str] = Field(default=None, description="Agent name")
    description: Optional[str] = Field(default=None, description="Agent description")


class AgentTypes(BaseModel):
    """Model for available agent types"""
    types: List[str] = Field(..., description="Available agent types")


# Agent endpoints
@router.get(
    "",
    response_model=List[AgentListItem],
    summary="List all agents",
    description="Get a list of all registered agents"
)
async def list_agents():
    """List all registered agents"""
    with logfire.span("List agents"):
        agents = agent_registry.list_agents()
        return agents


@router.get(
    "/types",
    response_model=AgentTypes,
    summary="Get available agent types",
    description="Get a list of all available agent types that can be created"
)
async def get_agent_types():
    """Get available agent types"""
    with logfire.span("Get agent types"):
        types = agent_registry.get_available_agent_types()
        return {"types": types}


@router.post(
    "",
    response_model=AgentDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new agent",
    description="Create a new agent of the specified type"
)
async def create_agent(request: CreateAgentRequest):
    """Create a new agent"""
    with logfire.span("Create agent", agent_id=request.agent_id, agent_type=request.agent_type):
        try:
            # Check if agent already exists
            try:
                agent = agent_registry.get_agent(request.agent_id)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Agent with ID {request.agent_id} already exists"
                )
            except AgentNotFoundError:
                pass
            
            # Create the agent
            agent = agent_registry.create_agent(
                agent_id=request.agent_id,
                agent_type=request.agent_type,
                name=request.name or request.agent_id
            )
            
            # Get agent details
            agent_status = await agent.get_status()
            
            # Create response
            agent_detail = AgentDetail(
                id=agent.metadata.id,
                name=agent.metadata.name,
                type=agent.__class__.__name__,
                status=agent.status.value,
                description=agent.metadata.description,
                version=agent.metadata.version,
                capabilities=[cap.dict() if hasattr(cap, "dict") else cap for cap in agent.metadata.capabilities],
                available_tools=agent.metadata.available_tools,
                model=agent.metadata.model,
                execution_history_count=len(agent.execution_history),
                infrastructure=agent_status.get("infrastructure", {})
            )
            
            logfire.info(f"Created agent {request.agent_id} of type {request.agent_type}")
            
            return agent_detail
            
        except ValueError as e:
            logfire.error(f"Error creating agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logfire.error(f"Error creating agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating agent: {str(e)}"
            )


@router.get(
    "/{agent_id}",
    response_model=AgentDetail,
    summary="Get agent details",
    description="Get detailed information about an agent"
)
async def get_agent(agent_id: str = Path(..., description="Agent ID")):
    """Get agent details"""
    with logfire.span("Get agent", agent_id=agent_id):
        try:
            # Get the agent
            agent = agent_registry.get_agent(agent_id)
            
            # Get agent status
            agent_status = await agent.get_status()
            
            # Create response
            agent_detail = AgentDetail(
                id=agent.metadata.id,
                name=agent.metadata.name,
                type=agent.__class__.__name__,
                status=agent.status.value,
                description=agent.metadata.description,
                version=agent.metadata.version,
                capabilities=[cap.dict() if hasattr(cap, "dict") else cap for cap in agent.metadata.capabilities],
                available_tools=agent.metadata.available_tools,
                model=agent.metadata.model,
                execution_history_count=len(agent.execution_history),
                infrastructure=agent_status.get("infrastructure", {})
            )
            
            return agent_detail
            
        except AgentNotFoundError:
            logfire.error(f"Agent not found: {agent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        except Exception as e:
            logfire.error(f"Error getting agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting agent: {str(e)}"
            )


@router.post(
    "/execute",
    response_model=AgentResponse,
    summary="Execute an agent operation",
    description="Execute an operation on an agent with the provided parameters"
)
async def execute_agent(request: AgentRequest):
    """Execute an agent operation"""
    with logfire.span("Execute agent", agent_id=request.agent_id, operation=request.operation):
        start_time = datetime.utcnow()
        
        try:
            # Execute the agent
            execution_result = await agent_registry.execute_agent(
                agent_id=request.agent_id,
                operation=request.operation,
                parameters=request.parameters or {}
            )
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create response
            response = AgentResponse(
                success=execution_result.success,
                agent_id=execution_result.agent_id,
                operation=execution_result.operation,
                result=execution_result.result if execution_result.success else {"error": execution_result.error},
                execution_time=execution_time,
                tools_used=execution_result.tools_used or request.tools or [],
                knowledge_queries=execution_result.knowledge_queries
            )
            
            logfire.info(f"Executed {request.operation} on agent {request.agent_id}",
                       success=response.success,
                       execution_time=execution_time)
            
            return response
            
        except AgentNotFoundError:
            logfire.error(f"Agent not found: {request.agent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {request.agent_id}"
            )
        except AgentExecutionError as e:
            logfire.error(f"Agent execution error: {str(e)}")
            
            # Create error response
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            response = AgentResponse(
                success=False,
                agent_id=request.agent_id,
                operation=request.operation,
                result={"error": str(e)},
                execution_time=execution_time,
                tools_used=request.tools or [],
                knowledge_queries=0
            )
            
            return response
        except Exception as e:
            logfire.error(f"Error executing agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing agent: {str(e)}"
            )


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an agent",
    description="Delete an agent from the registry"
)
async def delete_agent(agent_id: str = Path(..., description="Agent ID")):
    """Delete an agent"""
    with logfire.span("Delete agent", agent_id=agent_id):
        try:
            # Delete the agent
            agent_registry.unregister_agent(agent_id)
            
            logfire.info(f"Deleted agent {agent_id}")
            
            return None
            
        except AgentNotFoundError:
            logfire.error(f"Agent not found: {agent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        except Exception as e:
            logfire.error(f"Error deleting agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting agent: {str(e)}"
            )


@router.get(
    "/{agent_id}/capabilities",
    response_model=List[Dict[str, Any]],
    summary="Get agent capabilities",
    description="Get a list of all capabilities supported by the agent"
)
async def get_agent_capabilities(agent_id: str = Path(..., description="Agent ID")):
    """Get agent capabilities"""
    with logfire.span("Get agent capabilities", agent_id=agent_id):
        try:
            # Get the agent
            agent = agent_registry.get_agent(agent_id)
            
            # Get capabilities
            capabilities = await agent.get_capabilities()
            
            # Convert to dictionaries
            capabilities_dict = [cap.dict() if hasattr(cap, "dict") else cap for cap in capabilities]
            
            return capabilities_dict
            
        except AgentNotFoundError:
            logfire.error(f"Agent not found: {agent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        except Exception as e:
            logfire.error(f"Error getting agent capabilities: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting agent capabilities: {str(e)}"
            )


@router.get(
    "/{agent_id}/status",
    response_model=Dict[str, Any],
    summary="Get agent status",
    description="Get the current status of an agent"
)
async def get_agent_status(agent_id: str = Path(..., description="Agent ID")):
    """Get agent status"""
    with logfire.span("Get agent status", agent_id=agent_id):
        try:
            # Get the agent
            agent = agent_registry.get_agent(agent_id)
            
            # Get status
            status = await agent.get_status()
            
            return status
            
        except AgentNotFoundError:
            logfire.error(f"Agent not found: {agent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        except Exception as e:
            logfire.error(f"Error getting agent status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting agent status: {str(e)}"
            )


@router.get(
    "/{agent_id}/history",
    response_model=List[Dict[str, Any]],
    summary="Get agent execution history",
    description="Get the execution history of an agent"
)
async def get_agent_history(
    agent_id: str = Path(..., description="Agent ID"),
    limit: Optional[int] = Query(None, description="Maximum number of history items to return")
):
    """Get agent execution history"""
    with logfire.span("Get agent history", agent_id=agent_id, limit=limit):
        try:
            # Get the agent
            agent = agent_registry.get_agent(agent_id)
            
            # Get history
            history = await agent.get_execution_history(limit)
            
            # Convert to dictionaries
            history_dict = [
                {
                    "execution_id": item.execution_id,
                    "operation": item.operation,
                    "success": item.success,
                    "execution_time": item.execution_time,
                    "result": item.result if item.success else {"error": item.error},
                    "tools_used": item.tools_used,
                    "knowledge_queries": item.knowledge_queries
                }
                for item in history
            ]
            
            return history_dict
            
        except AgentNotFoundError:
            logfire.error(f"Agent not found: {agent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        except Exception as e:
            logfire.error(f"Error getting agent history: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting agent history: {str(e)}"
            )