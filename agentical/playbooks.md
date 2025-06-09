# Playbook Template
# Replace placeholder values with your specific configuration

name: "PLAYBOOK_NAME"  # Required: A unique name for your playbook
description: "Detailed description of what this playbook accomplishes"  # Required: Explain the playbook's purpose

# Playbook Ideas
1. Create an agent to build the following playbooks
2. Build a Panel dashboard only using MCP servers
3. Build portfolio from your GitHub organization in Docusaurus
4. Design am deploy an analytics pipeline in GCP using Pulumi
5. Build python MCP server to count tokens

# Basic Structure
1. A {Playbook} is a set of instructure to achieve some goal
2. A {Playbook} consists of one or steps
3. Each step is assigned one or more {Agents}
4. Each {Agent} can use one or more {Tools} to complete one or more steps
5. Each {Agent} is required to perform some activity in a {Workflow}
6. An {Agent} can follow one exactly one workflow at a step but can use one or more {Toosl} at a given step
7. The {Playbook} is finished when the goal is achieved

# Define the workflow steps in sequence
workflow:
  # First step example - standard operation
  - step_id: first_step_name  # Required: Unique identifier for this step
    type: standard  # Required: One of standard, work_in_parallel, self_feedback_loop, partner_feedback_loop, process, versus, handoff
    description: "Description of what this step does"  # Required: Human-readable description
    agent: AgentName  # Required: The agent that performs this step
    operation: "operation_name"  # Required: The operation the agent should perform
    next: second_step_name  # Required unless this is the final step: The next step to execute
    
  # Second step example - parallel processing
  - step_id: second_step_name
    type: work_in_parallel
    description: "Process data concurrently with multiple agents"
    agents:
      - FirstAgent:operation_one
      - SecondAgent:operation_two
    input_distribution:  # Optional: How to distribute input across agents
      type: split
      field: "input_field_name"
    output_aggregation:  # Optional: How to combine agent outputs
      type: merge
      strategy: "aggregation_strategy"
    next: third_step_name
    
  # Third step example - feedback loop
  - step_id: third_step_name
    type: partner_feedback_loop
    description: "Collaborative refinement process"
    agents:
      creator: CreatorAgent
      reviewer: ReviewerAgent
    operations:
      - role: creator
        name: "create_content"
      - role: reviewer
        name: "review_content"
      - role: creator
        name: "revise_content"
    iterations: 2  # Number of feedback cycles
    next: final_step
    
  # Final step example - process with conditions
  - step_id: final_step
    type: process
    description: "Final processing with validation"
    agent: FinalAgent
    input:
      source: "previous_step_output"
    process:
      - operation: "validate"
        condition: "validation_passed == true"
      - operation: "finalize"
    output:
      destination: "final_result"
    # No 'next' parameter since this is the final step

# Tools that can be used in this playbook
tools_allowed:
  - tool_one
  - tool_two
  - tool_three

# Agents that participate in this playbook
agents:
  - AgentName
  - FirstAgent
  - SecondAgent
  - CreatorAgent
  - ReviewerAgent
  - FinalAgent