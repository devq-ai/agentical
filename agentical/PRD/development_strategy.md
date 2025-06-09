# Agentical Development Strategy
## UPDATED: Leveraging Existing DevQ.ai Infrastructure

**Version**: 1.1  
**Date**: 2025-06-09  
**Project**: Agentical - Agentic AI Framework  
**PRD Reference**: `./agentical_prd.md`  
**Test Plan Reference**: `./test_plan.md`  
**Key Infrastructure**: `./devqai/ptolemies` (Production Knowledge Base) + `./devqai/mcp` (MCP Tools)
</thinking>

<edits>

<old_text>
## 🎯 Development Philosophy

### Core Principles

**1. Build-to-Test Development**
- Test-driven development with >90% coverage requirement
- Every component built with comprehensive test suite
- Continuous integration with automated quality gates

**2. DevQ.ai Standard Stack Compliance**
- FastAPI foundation with Logfire observability
- PyTest testing framework with comprehensive coverage
- TaskMaster AI project management integration
- MCP protocol implementation for tool interoperability

**3. Type-Safe by Design**
- Pydantic AI integration for robust type validation
- Comprehensive schema definitions for all data models
- Runtime validation with clear error messages

**4. Modular Architecture**
- Clear separation between agents, workflows, tools, and playbooks
- Plugin-based extensibility for future enhancements
- Dependency injection for testability and flexibility

---

## 🎯 Development Philosophy

### Core Principles

**1. Build-to-Test Development**
- Test-driven development with >90% coverage requirement
- Every component built with comprehensive test suite
- Continuous integration with automated quality gates

**2. DevQ.ai Standard Stack Compliance**
- FastAPI foundation with Logfire observability
- PyTest testing framework with comprehensive coverage
- TaskMaster AI project management integration
- MCP protocol implementation for tool interoperability

**3. Type-Safe by Design**
- Pydantic AI integration for robust type validation
- Comprehensive schema definitions for all data models
- Runtime validation with clear error messages

**4. Modular Architecture**
- Clear separation between agents, workflows, tools, and playbooks
- Plugin-based extensibility for future enhancements
- Dependency injection for testability and flexibility

---

## 🤖 Agent Development Strategy

### Agent Architecture Framework

#### Base Agent Pattern
```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class AgentCapability(BaseModel):
    """Define agent capabilities"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

class AgentMetadata(BaseModel):
    """Agent metadata and configuration"""
    id: str
    name: str
    description: str
    version: str
    capabilities: List[AgentCapability]
    tools: List[str]
    model: str
    system_prompts: List[str]
    created_at: datetime
    updated_at: datetime

class BaseAgent:
    """Foundation for all Agentical agents"""
    
    def __init__(self, metadata: AgentMetadata, agent: Agent):
        self.metadata = metadata
        self.agent = agent
        self.status = "idle"
        
    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent operation with comprehensive error handling"""
        
    async def validate_capabilities(self, operation: str) -> bool:
        """Validate agent can perform requested operation"""
        
    async def get_health_status(self) -> Dict[str, Any]:
        """Return agent health and capability status"""
```

### Agent Development Priorities

#### Phase 1: Foundation Agents (Weeks 3-4)
**Priority**: Critical
**Target**: 5 essential agents operational

1. **SuperAgent** (Meta-coordinator)
   - **Purpose**: Multi-agent orchestration and customer interface
   - **Capabilities**: Agent delegation, workflow coordination, multimodal interaction
   - **Tools**: All available tools, agent registry access
   - **Model**: Claude-3.7-Sonnet for complex reasoning
   - **Development Effort**: 3 days
   
2. **CodeAgent** (Development)
   - **Purpose**: Full-stack development with code generation and review
   - **Capabilities**: Multi-language code generation, testing, documentation
   - **Tools**: code_execution, github_tool, filesystem, git
   - **Model**: Claude-3.7-Sonnet for code quality
   - **Development Effort**: 2 days

3. **GitHubAgent** (Repository Management)
   - **Purpose**: GitHub workflow automation and repository management
   - **Capabilities**: Repository operations, PR automation, issue tracking
   - **Tools**: github_tool, github_mcp, git
   - **Model**: GPT-4 for API integration
   - **Development Effort**: 2 days

4. **DataScienceAgent** (Analytics)
   - **Purpose**: Data analysis and machine learning capabilities
   - **Capabilities**: EDA, ML model development, statistical analysis
   - **Tools**: data_analysis, bayesian_update, visualization
   - **Model**: Claude-3.7-Sonnet for analytical reasoning
   - **Development Effort**: 2 days

5. **ResearchAgent** (Information Gathering)
   - **Purpose**: Research and information gathering with source validation
   - **Capabilities**: Web research, source validation, synthesis
   - **Tools**: web_search, crawl4ai_mcp, memory
   - **Model**: GPT-4 for research accuracy
   - **Development Effort**: 1 day

#### Phase 2: Specialized Coordinators (Week 5)
**Priority**: High
**Target**: 5 coordinator agents for workflow management

6. **CodifierAgent** (Documentation)
   - **Purpose**: Code standardization and documentation generation
   - **Capabilities**: Code transformation, documentation, specifications
   - **Development Effort**: 2 days

7. **InspectorAgent** (Quality Assurance)
   - **Purpose**: Code and system inspection with quality analysis
   - **Capabilities**: Quality assessment, compliance verification, approval gates
   - **Development Effort**: 2 days

8. **ObserverAgent** (Monitoring)
   - **Purpose**: System monitoring and behavioral analysis
   - **Capabilities**: Real-time monitoring, pattern analysis, alerting
   - **Development Effort**: 1 day

#### Phase 3: Domain Specialists (Weeks 6-8)
**Priority**: Medium
**Target**: Complete 27 agent catalog

**Development Batches**:
- **Batch 1 (Week 6)**: DevOpsAgent, DBAAgent, TesterAgent, UATAgent (4 agents)
- **Batch 2 (Week 7)**: LegalAgent, InfoSecAgent, UXAgent, PulmiAgent (4 agents)  
- **Batch 3 (Week 8)**: TokenAgent, PlaymakerAgent, + 9 additional specialized agents

### Agent Development Standards

#### Code Structure Template
```python
# agents/{agent_name}.py
from agentical.core.base_agent import BaseAgent, AgentMetadata
from agentical.tools import ToolRegistry
from pydantic_ai import Agent
from pydantic import BaseModel

class {AgentName}Config(BaseModel):
    """Agent-specific configuration"""
    pass

class {AgentName}Input(BaseModel):
    """Agent input validation"""
    pass

class {AgentName}Output(BaseModel):
    """Agent output format"""
    pass

class {AgentName}(BaseAgent):
    """Specialized agent for {domain} operations"""
    
    def __init__(self, config: {AgentName}Config):
        # Initialize with metadata and Pydantic AI agent
        super().__init__(metadata, agent)
    
    async def {primary_operation}(self, input: {AgentName}Input) -> {AgentName}Output:
        """Primary agent operation"""
        pass
```

#### Testing Requirements
```python
# tests/agents/test_{agent_name}.py
import pytest
from agentical.agents.{agent_name} import {AgentName}

class Test{AgentName}:
    @pytest.fixture
    async def agent(self):
        """Create agent instance for testing"""
        return {AgentName}(config)
    
    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.metadata.name == "{agent_name}"
        assert agent.status == "idle"
    
    async def test_primary_operation_success(self, agent):
        """Test successful operation execution"""
        result = await agent.{primary_operation}(valid_input)
        assert result.success is True
    
    async def test_operation_error_handling(self, agent):
        """Test error handling for invalid inputs"""
        with pytest.raises(ValidationError):
            await agent.{primary_operation}(invalid_input)
```

---

## 🛠️ Tool Development Strategy

### Tool Architecture Framework

#### Tool Registry System
```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Dict, Any, List

class ToolMetadata(BaseModel):
    """Tool registration metadata"""
    name: str
    description: str
    category: str
    version: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    dependencies: List[str]
    permissions: List[str]

class BaseTool(ABC):
    """Foundation for all Agentical tools"""
    
    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool operation"""
        pass
    
    async def validate_input(self, parameters: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        pass
    
    async def check_dependencies(self) -> Dict[str, bool]:
        """Check tool dependency availability"""
        pass
```

### Tool Integration Priorities - REVISED

#### Phase 1: Existing MCP Server Integration (Week 2)
**Priority**: Critical
**Target**: Connect to existing 22 operational MCP servers

**Key Integration Points** (using `./devqai/mcp/mcp-servers.json`):
1. **ptolemies-mcp** - Production knowledge base with 597 documents (1 day)
2. **surrealdb-mcp** - Database operations with existing schemas (0.5 days)
3. **bayes-mcp** - Bayesian inference and probabilistic modeling (0.5 days)
4. **darwin-mcp** - Genetic algorithm optimization (0.5 days)
5. **Core MCP tools** - filesystem, git, memory, fetch, sequentialthinking (1 day)
6. **Specialized tools** - crawl4ai-mcp, github-mcp, logfire-mcp (1.5 days)

#### Phase 2: Tool Coordination Layer (Week 3)
**Priority**: High
**Target**: Agent-to-tool routing and authorization

**Coordination Components**:
1. **Tool Discovery** - Query existing MCP registry for capabilities
2. **Authorization Layer** - Role-based access to existing tools
3. **Routing Engine** - Intelligent tool selection for agent tasks
4. **State Management** - Tool execution tracking via existing SurrealDB

#### Phase 3: NO ADDITIONAL TOOL DEVELOPMENT
**Priority**: N/A
**Target**: Use existing infrastructure

**Existing Tools Available**:
- **22 MCP Servers**: All operational and tested
- **Security Tools**: Available through existing MCP servers
- **Data Processing**: Handled by existing specialized servers
- **Communication**: External integrations through existing tools

### Tool Development Standards

#### MCP Tool Implementation
```python
# tools/mcp/{tool_name}.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

class {ToolName}Server:
    """MCP server for {tool_description}"""
    
    def __init__(self):
        self.server = Server("agentical-{tool_name}")
        self._register_tools()
    
    def _register_tools(self):
        """Register available tools"""
        @self.server.list_tools()
        async def list_tools():
            return [
                Tool(
                    name="{tool_name}",
                    description="{tool_description}",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "parameter": {"type": "string"}
                        },
                        "required": ["parameter"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name == "{tool_name}":
                return await self._execute_operation(arguments)
    
    async def _execute_operation(self, args: dict) -> List[TextContent]:
        """Execute tool operation"""
        # Implementation logic
        return [TextContent(type="text", text=result)]
```

#### Tool Testing Framework
```python
# tests/tools/test_{tool_name}.py
import pytest
from agentical.tools.{tool_name} import {ToolName}

class Test{ToolName}:
    @pytest.fixture
    async def tool(self):
        """Create tool instance"""
        return {ToolName}()
    
    async def test_tool_registration(self, tool):
        """Test tool registers correctly"""
        assert tool.metadata.name == "{tool_name}"
    
    async def test_tool_execution_success(self, tool):
        """Test successful tool execution"""
        result = await tool.execute(valid_parameters)
        assert result["success"] is True
    
    async def test_tool_dependency_check(self, tool):
        """Test dependency validation"""
        deps = await tool.check_dependencies()
        assert all(deps.values())
```

---

## 🔄 Workflow Development Strategy

### Workflow Engine Architecture

#### Workflow State Machine
```python
from enum import Enum
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class WorkflowState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class WorkflowStep(BaseModel):
    """Individual workflow step definition"""
    step_id: str
    type: str
    description: str
    agent: Optional[str] = None
    operation: Optional[str] = None
    parameters: Dict[str, Any] = {}
    next: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None

class WorkflowExecution(BaseModel):
    """Workflow execution context"""
    workflow_id: str
    state: WorkflowState
    current_step: Optional[str] = None
    steps_completed: List[str] = []
    step_results: Dict[str, Any] = {}
    error_info: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class BaseWorkflow(ABC):
    """Foundation for all workflow patterns"""
    
    def __init__(self, definition: Dict[str, Any]):
        self.definition = definition
        self.execution = WorkflowExecution(workflow_id=str(uuid4()))
    
    @abstractmethod
    async def execute(self) -> WorkflowExecution:
        """Execute workflow pattern"""
        pass
    
    async def pause(self) -> bool:
        """Pause workflow execution"""
        pass
    
    async def resume(self) -> bool:
        """Resume paused workflow"""
        pass
    
    async def rollback(self, target_step: str) -> bool:
        """Rollback to previous step"""
        pass
```

### Workflow Development Priorities

#### Phase 1: Standard Workflows (Week 4)
**Priority**: Critical
**Target**: 3 basic patterns operational

1. **StandardWorkflow** (Linear execution)
   - **Pattern**: Sequential single-agent operation
   - **Use Cases**: Simple task execution, basic automation
   - **Implementation**: Direct agent calls with error handling
   - **Development Effort**: 1 day

2. **ParallelWorkflow** (Concurrent execution)
   - **Pattern**: Multiple agents working simultaneously
   - **Use Cases**: Independent parallel tasks, result aggregation
   - **Implementation**: asyncio concurrent execution with result collection
   - **Development Effort**: 2 days

3. **ProcessWorkflow** (Validation checkpoints)
   - **Pattern**: Sequential steps with validation gates
   - **Use Cases**: Multi-step processes, approval workflows
   - **Implementation**: Step validation, conditional branching
   - **Development Effort**: 2 days

#### Phase 2: Pydantic-Graph Workflows (Weeks 7-8)
**Priority**: High
**Target**: 5 advanced patterns operational

4. **AgentFeedbackWorkflow** (Collaborative refinement)
   - **Pattern**: Two-agent feedback loop with iterative improvement
   - **Use Cases**: Code review, content editing, quality improvement
   - **Implementation**: Pydantic-Graph state machine with feedback tracking
   - **Development Effort**: 3 days

5. **HandoffWorkflow** (Dynamic routing)
   - **Pattern**: Conditional agent handoff based on classification
   - **Use Cases**: Task routing, specialist delegation
   - **Implementation**: Dynamic agent selection with context transfer
   - **Development Effort**: 2 days

6. **HumanLoopWorkflow** (Human intervention)
   - **Pattern**: Agent-human collaboration with approval gates
   - **Use Cases**: Quality assurance, approval workflows
   - **Implementation**: Pause/resume with human interface
   - **Development Effort**: 3 days

7. **SelfFeedbackWorkflow** (Iterative improvement)
   - **Pattern**: Single agent self-evaluation and refinement
   - **Use Cases**: Autonomous quality improvement, optimization
   - **Implementation**: Internal evaluation cycles with improvement tracking
   - **Development Effort**: 2 days

8. **VersusWorkflow** (Competitive evaluation)
   - **Pattern**: Multiple agents competing with comparative analysis
   - **Use Cases**: Solution comparison, best result selection
   - **Implementation**: Parallel execution with judge agent evaluation
   - **Development Effort**: 2 days

### Workflow Development Standards

#### Implementation Template
```python
# workflows/{workflow_name}.py
from agentical.core.base_workflow import BaseWorkflow, WorkflowExecution
from agentical.agents import AgentRegistry
from typing import Dict, Any

class {WorkflowName}(BaseWorkflow):
    """Implementation of {workflow_pattern} pattern"""
    
    def __init__(self, definition: Dict[str, Any]):
        super().__init__(definition)
        self.agent_registry = AgentRegistry()
    
    async def execute(self) -> WorkflowExecution:
        """Execute {workflow_pattern} workflow"""
        try:
            self.execution.state = WorkflowState.RUNNING
            self.execution.started_at = datetime.utcnow()
            
            # Workflow-specific execution logic
            await self._execute_workflow_logic()
            
            self.execution.state = WorkflowState.COMPLETED
            self.execution.completed_at = datetime.utcnow()
            
        except Exception as e:
            self.execution.state = WorkflowState.FAILED
            self.execution.error_info = {"error": str(e)}
            
        return self.execution
    
    async def _execute_workflow_logic(self):
        """Implement specific workflow pattern"""
        pass
```

#### Testing Framework
```python
# tests/workflows/test_{workflow_name}.py
import pytest
from agentical.workflows.{workflow_name} import {WorkflowName}

class Test{WorkflowName}:
    @pytest.fixture
    async def workflow(self):
        """Create workflow instance"""
        definition = {
            "steps": [{"step_id": "test", "agent": "test_agent"}]
        }
        return {WorkflowName}(definition)
    
    async def test_workflow_execution_success(self, workflow):
        """Test successful workflow execution"""
        result = await workflow.execute()
        assert result.state == WorkflowState.COMPLETED
    
    async def test_workflow_error_handling(self, workflow):
        """Test workflow error handling"""
        # Test error scenarios
        pass
    
    async def test_workflow_state_persistence(self, workflow):
        """Test workflow state save and restore"""
        # Test pause/resume functionality
        pass
```

---

## 🎮 Playbook Development Strategy

### Playbook System Architecture

#### Schema and Validation
```python
# playbooks/schema.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum

class StepType(str, Enum):
    STANDARD = "standard"
    PARALLEL = "work_in_parallel"
    PROCESS = "process"
    AGENT_FEEDBACK = "agent_feedback"
    HANDOFF = "handoff"
    HUMAN_LOOP = "human_loop"
    SELF_FEEDBACK = "self_feedback"
    VERSUS = "versus"

class PlaybookStep(BaseModel):
    """Validated playbook step definition"""
    step_id: str = Field(..., description="Unique step identifier")
    type: StepType = Field(..., description="Workflow pattern type")
    description: str = Field(..., description="Step description")
    agent: Optional[str] = Field(None, description="Primary agent")
    agents: Optional[Dict[str, str]] = Field(None, description="Multiple agents")
    operation: Optional[str] = Field(None, description="Agent operation")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    next: Optional[str] = Field(None, description="Next step")
    
    @validator('agent')
    def validate_agent_for_standard(cls, v, values):
        if values.get('type') == StepType.STANDARD and not v:
            raise ValueError("agent required for standard steps")
        return v

class Playbook(BaseModel):
    """Complete playbook definition"""
    name: str = Field(..., description="Playbook name")
    description: str = Field(..., description="Playbook description")
    version: str = Field(default="1.0", description="Playbook version")
    steps: List[PlaybookStep] = Field(..., description="Workflow steps")
    tools: List[str] = Field(default_factory=list, description="Available tools")
    agents: List[str] = Field(default_factory=list, description="Required agents")
    agent_llms: Dict[str, str] = Field(default_factory=dict, description="Agent LLM mappings")
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

#### Execution Engine
```python
# playbooks/executor.py
from agentical.workflows import WorkflowFactory
from agentical.playbooks.schema import Playbook, PlaybookStep

class PlaybookExecutor:
    """Execute playbooks with comprehensive monitoring"""
    
    def __init__(self):
        self.workflow_factory = WorkflowFactory()
        self.execution_history = []
    
    async def execute_playbook(self, playbook: Playbook) -> Dict[str, Any]:
        """Execute complete playbook"""
        execution_id = str(uuid4())
        
        try:
            # Validate playbook
            await self._validate_playbook(playbook)
            
            # Execute steps sequentially
            results = {}
            current_step = playbook.steps[0].step_id
            
            while current_step:
                step = self._find_step(playbook.steps, current_step)
                result = await self._execute_step(step, results)
                results[current_step] = result
                current_step = step.next
                
            return {
                "execution_id": execution_id,
                "success": True,
                "results": results
            }
            
        except Exception as e:
            return {
                "execution_id": execution_id,
                "success": False,
                "error": str(e)
            }
    
    async def _execute_step(self, step: PlaybookStep, context: Dict[str, Any]):
        """Execute individual playbook step"""
        workflow = self.workflow_factory.create_workflow(step.type, step.dict())
        return await workflow.execute()
```

### Playbook Development Priorities - REVISED

#### Phase 1: Infrastructure-Aware Playbooks (Week 4)
**Priority**: High
**Target**: Playbooks that coordinate existing infrastructure

1. **Infrastructure Schema** (1 day)
   - Schema that references existing MCP tools by name
   - Ptolemies knowledge base integration specifications
   - Agent-tool-knowledge coordination definitions

2. **Coordination Executor** (2 days)
   - Execute steps using existing MCP servers
   - Integrate with Ptolemies knowledge for agent context
   - Real-time monitoring via existing Logfire infrastructure

3. **Template System** (1 day)
   - Templates for common agent + tool + knowledge patterns
   - Pre-built workflows using existing infrastructure
   - Configuration inheritance from existing services

#### Phase 2: Advanced Coordination (Week 6)
**Priority**: Medium
**Target**: Complex orchestration patterns

4. **Knowledge-Augmented Logic** (2 days)
   - Conditional logic using Ptolemies knowledge base
   - Dynamic tool selection based on agent context
   - Semantic routing using existing RAG capabilities

5. **Infrastructure Recovery** (1 day)
   - Retry mechanisms leveraging existing tool reliability
   - State recovery using existing SurrealDB persistence
   - Graceful degradation with existing monitoring

### Example Playbooks

#### Simple Code Generation Playbook
```yaml
# playbooks/examples/simple_code_generation.yaml
name: "Simple Code Generation"
description: "Generate Python code using CodeAgent"
version: "1.0"

agents:
  - CodeAgent

tools:
  - code_generation
  - code_execution

agent_llms:
  CodeAgent: "claude-3-7-sonnet-20250219"

steps:
  - step_id: generate_code
    type: standard
    description: "Generate Python function"
    agent: CodeAgent
    operation: "generate_function"
    parameters:
      language: "python"
      function_name: "calculate_fibonacci"
      requirements: "Generate a function that calculates Fibonacci numbers"
    next: execute_code

  - step_id: execute_code
    type: standard
    description: "Execute generated code"
    agent: CodeAgent
    operation: "execute_code"
    parameters:
      test_cases: ["fibonacci(10)", "fibonacci(20)"]
```

#### Multi-Agent Feedback Playbook
```yaml
# playbooks/examples/code_review_workflow.yaml
name: "Code Review Workflow"
description: "Multi-agent code review with feedback loop"
version: "1.0"

agents:
  - CodeAgent
  - InspectorAgent

steps:
  - step_id: code_review_loop
    type: agent_feedback
    description: "Iterative code review and improvement"
    agents:
      creator: CodeAgent
      reviewer: InspectorAgent
    operations:
      - role: creator
        name: "generate_code"
      - role: reviewer
        name: "review_code"
      - role: creator
        name: "improve_code"
    iterations: 3
    parameters:
      code_requirements: "Create a REST API endpoint"
      quality_standards: ["PEP8", "type_hints", "docstrings"]
```

---

## 🔧 Implementation Standards

### Code Quality Requirements

#### Type Safety and Validation
```python
# Every component must use Pydantic for validation
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union

class ComponentConfig(BaseModel):
    """All configuration classes inherit from BaseModel"""
    name: str = Field(..., description="Component name")
    version: str = Field(default="1.0", description="Version")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
```

#### Error Handling Pattern
```python
# Standardized error handling across all components
from agentical.core.exceptions import AgenticalError

class ComponentError(AgenticalError):
    """Component-specific error"""
    pass

async def operation_with_error_handling():
    try:
        result = await risky_operation()
        return {"success": True, "data": result}
    except ComponentError as e:
        logger.error(f"Component error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.exception("Unexpected error")
        return {"success": False, "error": "Internal error"}
```

#### Logging and Observability
```python
# Logfire integration pattern for all components
import logfire
from functools import wraps

def log_operation(operation_name: str):
    """Decorator for operation logging"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with logfire.span(operation_name, **kwargs):
                try:
                    result = await func(*args, **kwargs)
                    logfire.info(f"{operation_name} completed", result=result)
                    return result
                except Exception as e:
                    logfire.error(f"{operation_name} failed", error=str(e))
                    raise
        return wrapper
    return decorator
```

### Testing Integration

#### Test Structure Standard
```python
# tests/{component_type}/test_{component_name}.py
import pytest
import asyncio
from agentical.{component_type}.{component_name} import {ComponentName}

class Test{ComponentName}:
    """Comprehensive test suite for {ComponentName}"""
    
    @pytest.fixture
    async def component(self):
        """Create component instance for testing"""
        return {ComponentName}(test_config)
    
    # Unit tests
    async def test_initialization(self, component):
        """Test component initializes correctly"""
        
    async def test_primary_operation_success(self, component):
        """Test successful operation execution"""
        
    async def test_error_handling(self, component):
        """Test error handling scenarios"""
        
    # Integration tests
    @pytest.mark.integration
    async def test_integration_with_dependencies(self, component):
        """Test integration with external dependencies"""
        
    # Performance tests
    @pytest.mark.performance
    async def test_performance_benchmarks(self, component):
        """Test performance meets SLA requirements"""
```

### Documentation Requirements

#### Component Documentation Template
```python
class ComponentName:
    """Brief description of component purpose.
    
    This component provides {functionality} for {use_case}.
    It integrates with {dependencies} and supports {features}.
    
    Example:
        ```python
        component = ComponentName(config)
        result = await component.primary_operation(parameters)
        ```
    
    Attributes:
        attribute_name: Description of attribute
        
    Note:
        Any important usage notes or limitations
    """
```

---

## 📊 Development Metrics and Monitoring - REVISED

### Integration Quality Metrics
- **Infrastructure Integration**: 100% connectivity to Ptolemies + MCP
- **Knowledge Query Performance**: <200ms via existing Ptolemies
- **Tool Coordination**: <100ms routing to existing MCP servers
- **Orchestration Coverage**: >90% test coverage for coordination layer

### Infrastructure Leverage Metrics
- **Ptolemies Utilization**: Knowledge base query frequency and success rate
- **MCP Server Usage**: Tool execution success rate across 22 servers
- **Existing Monitoring**: Leverage established Logfire dashboards
- **Performance Baseline**: Use existing infrastructure benchmarks

### Quality Gates - Infrastructure Focused
```python
# Integration-focused quality gates
quality_gates = {
    "ptolemies_integration": {"connectivity": 100, "query_performance": "<200ms"},
    "mcp_integration": {"servers_operational": 22, "response_time": "<100ms"},
    "orchestration_tests": {"pass_rate": 100, "coverage": 90},
    "infrastructure_health": {"existing_services": 100, "new_layer": 99},
    "coordination_quality": {"maintainability": "A", "reliability": "A"}
}
```

---

## 🎯 Success Criteria and Milestones

### Phase 1 Success Criteria (Week 2) - REVISED
- [ ] Integration with existing Ptolemies knowledge base (597 documents accessible)
- [ ] Connection to existing 22 MCP servers operational
- [ ] FastAPI orchestration layer with health endpoints for all services
- [ ] Logfire monitoring for coordination layer integrated
- [ ] Test framework for integration testing configured

### Phase 2 Success Criteria (Week 4) - REVISED
- [ ] 5 foundational orchestrator agents operational with existing tools
- [ ] 3 standard workflow patterns coordinating existing infrastructure
- [ ] Agent-knowledge integration using existing Ptolemies RAG
- [ ] Basic playbook system leveraging existing services
- [ ] >90% integration test coverage maintained

### Phase 3 Success Criteria (Week 6) - REVISED
- [ ] Advanced workflow patterns using existing infrastructure
- [ ] Complete agent catalog (27 agents as orchestrators)
- [ ] Production-ready coordination layer
- [ ] Performance benchmarks met leveraging existing optimizations
- [ ] Documentation for orchestration patterns published

### Production Readiness Criteria - REVISED
- [ ] 99.9% orchestration layer uptime (leveraging existing infrastructure reliability)
- [ ] Security integration with existing MCP authorization
- [ ] Performance SLAs met using existing optimized services
- [ ] User acceptance testing for coordination workflows completed
- [ ] Integration with existing production monitoring dashboards

---

## 📞 Development Team Organization

### Team Structure
- **Lead Engineer**: Architecture, critical component development
- **Agent Developer**: Agent implementation and testing
- **Workflow Engineer**: Workflow patterns and orchestration
- **Tool Developer**: Tool integration and MCP implementation