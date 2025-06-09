# Agent Workflows Documentation

## Overview

This document outlines different workflow patterns for agent orchestration, categorized into **Pydantic-Graph** workflows (complex, state-based patterns) and **Standard** workflows (simpler, linear patterns). Each workflow type provides specific capabilities for different use cases and complexity levels.

---

## Pydantic-Graph Workflows (count=5)

Pydantic-Graph workflows leverage state machines and complex routing logic for sophisticated agent interactions. These patterns support conditional branching, state persistence, and dynamic agent selection.

### 1. Agent Feedback
- **Name**: `agent_feedback`
- **Description**: Collaborative feedback loop between two specialized agents with iterative refinement
- **Status**: `enabled: false`

**Technical Implementation:**
```python
class AgentFeedbackWorkflow:
    def __init__(self, primary_agent: Agent, reviewer_agent: Agent):
        self.primary = primary_agent
        self.reviewer = reviewer_agent
        self.max_iterations = 3
        self.feedback_history = []
    
    async def execute(self, task: str) -> WorkflowResult:
        for iteration in range(self.max_iterations):
            # Primary agent produces output
            output = await self.primary.run(task, context=self.feedback_history)
            
            # Reviewer evaluates and provides feedback
            feedback = await self.reviewer.run(
                f"Review and provide feedback: {output}",
                schema=FeedbackSchema
            )
            
            if feedback.approved:
                return WorkflowResult(output=output, iterations=iteration+1)
            
            self.feedback_history.append({
                "iteration": iteration,
                "output": output,
                "feedback": feedback.comments
            })
```

**Use Cases:**
- Code review workflows (developer + reviewer agents)
- Content creation with editorial oversight
- Research paper peer review simulation
- Quality assurance processes

**State Transitions:**
```
Initial → Primary_Work → Review → [Approved|Rejected] → [Complete|Iterate]
```

### 2. Handoff
- **Name**: `handoff`
- **Description**: Dynamic transfer to specialized agents based on conditional routing and task classification
- **Status**: `enabled: false`

**Technical Implementation:**
```python
class HandoffWorkflow:
    def __init__(self, router_agent: Agent, specialist_agents: Dict[str, Agent]):
        self.router = router_agent
        self.specialists = specialist_agents
        self.handoff_chain = []
    
    async def execute(self, task: str) -> WorkflowResult:
        current_task = task
        
        while True:
            # Router determines next agent
            routing_decision = await self.router.run(
                f"Route this task: {current_task}",
                schema=RoutingDecision
            )
            
            if routing_decision.action == "complete":
                break
                
            # Execute with specialist agent
            specialist = self.specialists[routing_decision.agent_type]
            result = await specialist.run(current_task)
            
            self.handoff_chain.append({
                "agent": routing_decision.agent_type,
                "input": current_task,
                "output": result,
                "reasoning": routing_decision.reasoning
            })
            
            current_task = routing_decision.next_task or result
```

**Use Cases:**
- Customer support escalation (L1 → L2 → L3)
- Medical diagnosis workflow (triage → specialist → treatment)
- Legal case routing (intake → research → litigation)
- Technical incident response

**Routing Conditions:**
- Task complexity assessment
- Domain expertise requirements
- Resource availability
- Priority levels

### 3. Human Loop
- **Name**: `human_loop`
- **Description**: Agent-human collaboration with explicit human intervention points and approval gates
- **Status**: `enabled: false`

**Technical Implementation:**
```python
class HumanLoopWorkflow:
    def __init__(self, agent: Agent, human_interface: HumanInterface):
        self.agent = agent
        self.human = human_interface
        self.intervention_points = []
    
    async def execute(self, task: str) -> WorkflowResult:
        # Agent performs initial work
        initial_output = await self.agent.run(task)
        
        # Check if human intervention required
        intervention_check = await self.agent.run(
            f"Does this output require human review? {initial_output}",
            schema=InterventionDecision
        )
        
        if intervention_check.requires_human:
            # Present to human with context
            human_feedback = await self.human.request_feedback(
                output=initial_output,
                context=task,
                required_actions=intervention_check.required_actions
            )
            
            # Agent incorporates human feedback
            final_output = await self.agent.run(
                f"Incorporate human feedback: {human_feedback.comments}",
                context={"original": initial_output, "feedback": human_feedback}
            )
            
            return WorkflowResult(
                output=final_output,
                human_intervention=True,
                feedback_incorporated=human_feedback
            )
        
        return WorkflowResult(output=initial_output, human_intervention=False)
```

**Human Intervention Triggers:**
- Quality thresholds not met
- High-risk decisions required
- Regulatory compliance checkpoints
- Creative approval needed
- Ethical considerations

**Interface Requirements:**
- Real-time notification system
- Context presentation
- Structured feedback collection
- Approval/rejection workflows

### 4. Self Feedback
- **Name**: `self_feedback`
- **Description**: Iterative self-improvement with internal evaluation and refinement cycles
- **Status**: `enabled: false`

**Technical Implementation:**
```python
class SelfFeedbackWorkflow:
    def __init__(self, agent: Agent, evaluator_prompt: str):
        self.agent = agent
        self.evaluator_prompt = evaluator_prompt
        self.max_iterations = 5
        self.improvement_threshold = 0.8
    
    async def execute(self, task: str) -> WorkflowResult:
        best_output = None
        best_score = 0
        iteration_history = []
        
        for iteration in range(self.max_iterations):
            # Agent performs task
            output = await self.agent.run(task, context=iteration_history)
            
            # Self-evaluation
            evaluation = await self.agent.run(
                f"{self.evaluator_prompt}\nEvaluate: {output}",
                schema=SelfEvaluationSchema
            )
            
            iteration_history.append({
                "iteration": iteration,
                "output": output,
                "score": evaluation.score,
                "feedback": evaluation.feedback
            })
            
            if evaluation.score > best_score:
                best_output = output
                best_score = evaluation.score
            
            # Check if improvement threshold met
            if evaluation.score >= self.improvement_threshold:
                break
                
        return WorkflowResult(
            output=best_output,
            final_score=best_score,
            iterations=len(iteration_history),
            improvement_history=iteration_history
        )
```

**Evaluation Criteria:**
- Task completion accuracy
- Output quality metrics
- Efficiency measurements
- Constraint adherence

### 5. Versus
- **Name**: `versus`
- **Description**: Competitive evaluation between multiple agents with comparative analysis and best solution selection
- **Status**: `enabled: false`

**Technical Implementation:**
```python
class VersusWorkflow:
    def __init__(self, competing_agents: List[Agent], judge_agent: Agent):
        self.competitors = competing_agents
        self.judge = judge_agent
        self.evaluation_criteria = []
    
    async def execute(self, task: str) -> WorkflowResult:
        # Collect solutions from all competing agents
        solutions = []
        for i, agent in enumerate(self.competitors):
            solution = await agent.run(task)
            solutions.append({
                "agent_id": i,
                "agent_name": agent.name,
                "solution": solution,
                "timestamp": datetime.now()
            })
        
        # Judge evaluates all solutions
        evaluation = await self.judge.run(
            f"Compare these solutions: {solutions}",
            schema=CompetitiveEvaluationSchema
        )
        
        # Rank solutions
        ranked_solutions = sorted(
            solutions, 
            key=lambda x: evaluation.scores[x["agent_id"]], 
            reverse=True
        )
        
        return WorkflowResult(
            winning_solution=ranked_solutions[0],
            all_solutions=ranked_solutions,
            evaluation_details=evaluation,
            competition_metrics={
                "total_competitors": len(self.competitors),
                "evaluation_criteria": evaluation.criteria_used,
                "winning_margin": evaluation.scores[ranked_solutions[0]["agent_id"]] - 
                                evaluation.scores[ranked_solutions[1]["agent_id"]]
            }
        )
```

**Competition Types:**
- Algorithm optimization challenges
- Creative content generation
- Problem-solving contests
- A/B testing scenarios

---

## Standard Workflows (count=3)

Standard workflows provide straightforward, linear execution patterns suitable for common automation tasks and simple agent interactions.

### 1. Parallel
- **Name**: `parallel`
- **Description**: Concurrent execution across multiple independent agents with result aggregation
- **Status**: `enabled: false`

**Technical Implementation:**
```python
class ParallelWorkflow:
    def __init__(self, agents: List[Agent], aggregation_strategy: str = "collect"):
        self.agents = agents
        self.aggregation_strategy = aggregation_strategy
        self.timeout = 300  # 5 minutes default
    
    async def execute(self, tasks: Union[str, List[str]]) -> WorkflowResult:
        # Prepare tasks for each agent
        if isinstance(tasks, str):
            agent_tasks = [tasks] * len(self.agents)
        else:
            agent_tasks = tasks
            
        # Execute tasks concurrently
        async with asyncio.TaskGroup() as tg:
            futures = [
                tg.create_task(agent.run(task)) 
                for agent, task in zip(self.agents, agent_tasks)
            ]
        
        # Collect results
        results = [await future for future in futures]
        
        # Apply aggregation strategy
        aggregated_result = self._aggregate_results(results)
        
        return WorkflowResult(
            individual_results=results,
            aggregated_result=aggregated_result,
            execution_time=time.time() - start_time,
            agents_used=len(self.agents)
        )
    
    def _aggregate_results(self, results: List[Any]) -> Any:
        if self.aggregation_strategy == "collect":
            return results
        elif self.aggregation_strategy == "consensus":
            return self._find_consensus(results)
        elif self.aggregation_strategy == "best":
            return max(results, key=self._quality_score)
```

**Use Cases:**
- Data processing across multiple sources
- Parallel research on different topics
- Load distribution for heavy computations
- Multi-modal analysis (text, image, audio simultaneously)

**Synchronization Points:**
- Task distribution
- Result collection
- Error handling
- Timeout management

### 2. Process
- **Name**: `process`
- **Description**: Structured workflow with validation checkpoints, conditional branching, and state management
- **Status**: `enabled: false`

**Technical Implementation:**
```python
class ProcessWorkflow:
    def __init__(self, steps: List[ProcessStep], validation_rules: List[ValidationRule]):
        self.steps = steps
        self.validation_rules = validation_rules
        self.state = WorkflowState()
    
    async def execute(self, initial_input: Any) -> WorkflowResult:
        current_input = initial_input
        execution_log = []
        
        for step in self.steps:
            # Pre-step validation
            validation_result = self._validate_input(current_input, step.requirements)
            if not validation_result.passed:
                raise WorkflowValidationError(validation_result.errors)
            
            # Execute step
            step_result = await step.execute(current_input, self.state)
            execution_log.append({
                "step_name": step.name,
                "input": current_input,
                "output": step_result.output,
                "execution_time": step_result.execution_time,
                "metadata": step_result.metadata
            })
            
            # Post-step validation and condition checking
            if step.condition and not step.condition.evaluate(step_result.output):
                if step.condition.action == "retry":
                    current_input = step.condition.modify_input(current_input)
                    continue
                elif step.condition.action == "branch":
                    next_step = step.condition.get_branch_step()
                    current_input = step_result.output
                    continue
                elif step.condition.action == "terminate":
                    break
            
            # Update state and prepare for next step
            self.state.update(step.name, step_result.output)
            current_input = step_result.output
        
        return WorkflowResult(
            final_output=current_input,
            execution_log=execution_log,
            final_state=self.state.snapshot(),
            validation_passed=True
        )
```

**Process Components:**
- **Input Validation**: Schema validation, type checking, business rules
- **Step Execution**: Agent tasks, tool invocations, data transformations
- **Condition Evaluation**: Success criteria, branching logic, retry conditions
- **Output Generation**: Result formatting, state persistence, logging

### 3. Standard
- **Name**: `standard`
- **Description**: Sequential single-agent operation with optional tool integration and linear execution flow
- **Status**: `enabled: false`

**Technical Implementation:**
```python
class StandardWorkflow:
    def __init__(self, agent: Agent, tools: Optional[List[Tool]] = None):
        self.agent = agent
        self.tools = tools or []
        self.execution_context = ExecutionContext()
    
    async def execute(self, task: str, **kwargs) -> WorkflowResult:
        start_time = time.time()
        
        # Prepare agent with tools and context
        if self.tools:
            self.agent.tools.extend(self.tools)
        
        # Execute the task
        try:
            result = await self.agent.run(
                task, 
                context=self.execution_context,
                **kwargs
            )
            
            execution_time = time.time() - start_time
            
            return WorkflowResult(
                output=result,
                execution_time=execution_time,
                tools_used=self._get_tools_used(),
                context_final=self.execution_context.snapshot(),
                success=True
            )
            
        except Exception as e:
            return WorkflowResult(
                output=None,
                error=str(e),
                execution_time=time.time() - start_time,
                success=False
            )
    
    def _get_tools_used(self) -> List[str]:
        return [tool.name for tool in self.agent.tools if tool.was_used]
```

**Execution Flow:**
```
Input → [Tool Selection] → Agent Processing → [Tool Execution] → Output
```

**Features:**
- Simple linear execution
- Optional tool integration
- Context preservation
- Error handling and recovery
- Performance monitoring

---

## Configuration and Usage

### Enabling Workflows

```python
# Enable specific workflows
workflow_config = {
    "pydantic-graph": {
        "agent_feedback": True,
        "handoff": True,
        "human_loop": False,
        "self_feedback": True,
        "versus": False
    },
    "standard": {
        "parallel": True,
        "process": True,
        "standard": True
    }
}

# Initialize workflow manager
workflow_manager = WorkflowManager(config=workflow_config)
```

### Workflow Selection Guidelines

**Choose Pydantic-Graph when:**
- Complex state management required
- Multiple agent coordination needed
- Conditional branching necessary
- Human interaction points required
- Quality assurance workflows

**Choose Standard when:**
- Simple linear execution
- Single agent sufficient
- Minimal state management
- Performance is critical
- Rapid prototyping needed

---

## Performance Considerations

- **Pydantic-Graph**: Higher overhead, complex state management, suited for sophisticated workflows
- **Standard**: Lower latency, minimal overhead, optimal for simple tasks
- **Resource Usage**: Parallel workflows require careful resource management
- **Error Handling**: Each workflow type requires specific error handling strategies