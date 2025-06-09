# Agent Workflows

## Overview
This document catalogs available workflow patterns for agent orchestration, divided into standard and pydantic-graph categories.

## Standard Workflows

### Parallel
- **Type**: `standard`
- **Description**: Concurrent execution across multiple independent agents with result aggregation
- **Components**: 
  - Task distributor
  - Agent pool manager
  - Result aggregator
  - Synchronization controller
  - Timeout handler

**Key Features:**
- Horizontal scaling across multiple agents
- Configurable aggregation strategies (collect, consensus, best)
- Resource optimization and load balancing
- Fault tolerance with partial failure handling

---

### Process
- **Type**: `standard`
- **Description**: Structured workflow with validation checkpoints, conditional branching, and state management
- **Components**:
  - Process step executor
  - Validation engine
  - State manager
  - Condition evaluator
  - Branch router

**Key Features:**
- Sequential step execution with validation
- Conditional branching and retry logic
- State persistence across steps
- Error recovery and rollback capabilities

---

### Standard
- **Type**: `standard`
- **Description**: Sequential single-agent operation with optional tool integration and linear execution flow
- **Components**:
  - Single agent executor
  - Tool integration layer
  - Context manager
  - Result formatter
  - Error handler

**Key Features:**
- Simple linear execution model
- Optional tool enhancement
- Minimal overhead and latency
- Straightforward debugging and monitoring

---

## Pydantic-Graph Workflows

### Agent Feedback
- **Type**: `pydantic-graph`
- **Description**: Collaborative feedback loop between two specialized agents with iterative refinement
- **Components**:
  - Primary agent (task executor)
  - Reviewer agent (feedback provider)
  - Iteration controller
  - Feedback aggregator
  - Convergence detector

**Key Features:**
- Iterative quality improvement
- Specialized agent roles
- Feedback history tracking
- Convergence criteria evaluation

---

### Handoff
- **Type**: `pydantic-graph`
- **Description**: Dynamic transfer to specialized agents based on conditional routing and task classification
- **Components**:
  - Router agent (task classifier)
  - Specialist agent pool
  - Handoff coordinator
  - Context transfer manager
  - Chain tracker

**Key Features:**
- Intelligent task routing
- Specialist agent utilization
- Context preservation across handoffs
- Dynamic agent selection

---

### Human Loop
- **Type**: `pydantic-graph`
- **Description**: Agent-human collaboration with explicit human intervention points and approval gates
- **Components**:
  - Agent executor
  - Human interface layer
  - Intervention detector
  - Approval workflow
  - Feedback incorporator

**Key Features:**
- Human-in-the-loop processing
- Configurable intervention triggers
- Structured feedback collection
- Quality assurance gates

---

### Self Feedback
- **Type**: `pydantic-graph`
- **Description**: Iterative self-improvement with internal evaluation and refinement cycles
- **Components**:
  - Task executor
  - Self-evaluator
  - Improvement tracker
  - Quality scorer
  - Iteration controller

**Key Features:**
- Autonomous quality improvement
- Internal evaluation metrics
- Progressive refinement
- Performance tracking

---

### Versus
- **Type**: `pydantic-graph`
- **Description**: Competitive evaluation between multiple agents with comparative analysis and best solution selection
- **Components**:
  - Competing agent pool
  - Judge agent
  - Competition controller
  - Solution evaluator
  - Ranking system

**Key Features:**
- Multi-agent competition
- Objective solution evaluation
- Comparative analysis
- Best solution selection