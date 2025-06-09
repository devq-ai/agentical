# Workflows in Agentical Framework

## Overview

The `workflows` directory contains the implementation of workflow patterns that orchestrate how agents interact to solve problems in the Agentical framework. Workflows define the coordination, communication, and execution flow between agents, enabling complex multi-agent systems that can tackle sophisticated tasks.

## Directory Structure

```
workflows/
├── __init__.py             # Package initialization
├── base.py                 # Base workflow classes
├── registry.py             # Workflow discovery and registration
├── patterns/               # Standard workflow patterns
│   ├── __init__.py
│   ├── parallel.py         # Work-in-Parallel pattern
│   ├── feedback_loop.py    # Self and Partner Feedback Loops
│   ├── conditional.py      # Conditional Process pattern
│   ├── competitive.py      # Agent-versus-Agent pattern
│   ├── handoff.py          # Handoff Pattern
│   └── human_loop.py       # Human-in-the-Loop pattern
└── graphs/                 # Complex graph-based workflows
    ├── __init__.py
    ├── base.py             # Base graph nodes and utilities
    ├── transitions.py      # State transition definitions
    └── visualizer.py       # Graph visualization utilities
```

## Core Components

### Base Workflow

The `base.py` file defines the foundational workflow classes:

- **Workflow**: The core class for all workflows
- **WorkflowContext**: Contains the state and execution context of a workflow
- **WorkflowResult**: Container for workflow execution results
- **AgentRole**: Defines agent roles and their required capabilities
- **WorkflowConfig**: Configuration for workflow execution

### Workflow Registry

The `registry.py` file implements a registry for workflow discovery:

- **WorkflowRegistry**: Central registry for all workflows
- **WorkflowCategory**: Classification of workflows by purpose
- **WorkflowMetadata**: Information about workflow capabilities
- **WorkflowDiscovery**: Automatic discovery of available workflows

### Workflow Patterns

The `patterns/` directory contains implementations of standard workflow patterns:

#### Work-in-Parallel

The `parallel.py` file implements patterns where multiple agents work concurrently:

- **ParallelWorkflow**: Execute multiple agents in parallel and aggregate results
- **MapReduceWorkflow**: Distribute tasks to multiple agents and combine results
- **TeamWorkflow**: Coordinate a team of agents with different roles

#### Feedback Loops

The `feedback_loop.py` file implements iterative improvement patterns:

- **SelfFeedbackLoop**: Agent improves its own output through iteration
- **PartnerFeedbackLoop**: Agents collaborate by refining each other's work
- **CritiqueRefineWorkflow**: One agent critiques, another refines

#### Conditional Processing

The `conditional.py` file implements branching workflow patterns:

- **ConditionalWorkflow**: Choose execution path based on conditions
- **DecisionTreeWorkflow**: Navigate a tree of decision points
- **RuleBasedWorkflow**: Apply predefined rules to determine flow

#### Competitive Patterns

The `competitive.py` file implements patterns with competing agents:

- **DebateWorkflow**: Agents debate different perspectives
- **CompetitiveEvaluation**: Agents compete to provide the best solution
- **AdversarialTesting**: One agent challenges another's outputs

#### Sequential Patterns

The `handoff.py` file implements sequential workflow patterns:

- **HandoffWorkflow**: Sequential workflow with clear transitions
- **PipelineWorkflow**: Process inputs through a series of specialized agents
- **AssemblyLineWorkflow**: Each agent adds to a growing output

#### Human Interaction

The `human_loop.py` file implements human-in-the-loop patterns:

- **HumanReviewWorkflow**: Pause for human approval of results
- **HumanFeedbackWorkflow**: Incorporate human feedback into the process
- **HumanCollaborationWorkflow**: Collaborative work between agents and humans

### Graph-Based Workflows

The `graphs/` directory leverages Pydantic-Graph for complex workflow orchestration:

- **BaseNode**: Building block for graph-based workflows
- **GraphWorkflow**: Workflow implementation using directed graphs
- **StateTransitions**: Define transitions between workflow states
- **GraphVisualizer**: Visualize workflow execution as a graph

## Workflow Patterns

### 1. Work-in-Parallel

**Description**: Multiple agents working concurrently on different aspects of a problem.

**Implementation**:
```python
# Create a parallel workflow
workflow = ParallelWorkflow(
    name="Research Analysis",
    description="Research different aspects of a topic in parallel"
)

# Add agents with different roles
workflow.add_agent("researcher", researcher_agent)
workflow.add_agent("analyst", analyst_agent)
workflow.add_agent("fact_checker", fact_checker_agent)
```

### 2. Self-Feedback Loop

**Description**: Agent improves its output through iteration.

**Implementation**:
```python
# Create a self-feedback loop workflow
workflow = SelfFeedbackLoop(
    name="Content Improvement",
    description="Iteratively improve content quality",
    max_iterations=3
)

# Add the agent
workflow.add_agent("improver", content_agent)
```

### 3. Partner-Feedback Loop

**Description**: Agents collaborate by iteratively refining each other's work.

**Implementation**:
```python
# Create a partner feedback loop workflow
workflow = PartnerFeedbackLoop(
    name="Document Creation",
    description="Collaborative document creation with feedback",
    max_iterations=5
)

# Add the agents
workflow.add_agent("writer", writer_agent)
workflow.add_agent("editor", editor_agent)
```

### 4. Conditional Process

**Description**: Workflow with conditional branching based on intermediate results.

**Implementation**:
```python
# Create a conditional workflow
workflow = ConditionalWorkflow(
    name="Customer Support",
    description="Route customer queries based on content"
)

# Define the conditions and agents
workflow.add_condition(
    "is_technical_query",
    lambda result: "technical" in result["category"],
    "tech_support",
    "general_support"
)

workflow.add_agent("classifier", classifier_agent)
workflow.add_agent("tech_support", tech_support_agent)
workflow.add_agent("general_support", general_support_agent)
```

### 5. Agent-versus-Agent

**Description**: Competitive agent interactions for debate or evaluation.

**Implementation**:
```python
# Create a debate workflow
workflow = DebateWorkflow(
    name="Policy Debate",
    description="Debate pros and cons of a policy",
    rounds=3
)

# Add the competing agents
workflow.add_agent("pro_side", pro_agent)
workflow.add_agent("con_side", con_agent)
workflow.add_agent("moderator", moderator_agent)
```

### 6. Handoff Pattern

**Description**: Sequential workflow with clear transitions between agents.

**Implementation**:
```python
# Create a handoff workflow
workflow = HandoffWorkflow(
    name="Content Pipeline",
    description="Sequential content creation pipeline"
)

# Define the sequence of agents
workflow.add_sequence([
    ("researcher", researcher_agent),
    ("writer", writer_agent),
    ("editor", editor_agent),
    ("formatter", formatter_agent)
])
```

### 7. Human-in-the-Loop

**Description**: Workflow that requires user approval to continue.

**Implementation**:
```python
# Create a human-in-the-loop workflow
workflow = HumanReviewWorkflow(
    name="Document Approval",
    description="Generate document with human approval steps"
)

# Add agents and review points
workflow.add_agent("generator", document_agent)
workflow.add_human_review_point("initial_draft", "Review the initial draft")
workflow.add_agent("reviser", revision_agent)
workflow.add_human_review_point("final_document", "Approve the final document")
```

## Best Practices

1. Choose the appropriate workflow pattern for the problem
2. Ensure agents have the capabilities required for their roles
3. Define clear transitions between workflow states
4. Include error handling and fallback mechanisms
5. Consider adding human review for critical decisions
6. Test workflows with a variety of inputs
7. Document workflow behavior and requirements

## Related Components

- **Agents**: The actors orchestrated by workflows
- **Tools**: Capabilities available to agents within workflows
- **Playbooks**: Use workflows as building blocks for solutions
- **Knowledge Base**: Source of information for workflow execution