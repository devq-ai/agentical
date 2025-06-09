## workflows (count=8)

### pydantic-graph (count=5)
- name: agent_feedback 
  description: Collaborative feedback loop between two agents 
  enabled: false
- name: handoff 
  description: Transfer to specialized agents based on conditions 
  enabled: false
- name: human_loop 
  description: Agent performs some operation with or without a {tool} to return some output that requires human interaction to meet some condition 
  enabled: false
- name: self_feedback 
  description: Agent will perform a task with or without a {tool} and before the end of the task or upon completion will evaluate the output and choose to run the task again or complete; iterative self-improvement by a single agent 
  enabled: false
- name: versus 
  description: Competition between agents to find the best solution 
  enabled: false

### standard (count=3) 
- name: parallel 
  description: Two or more agents execute tasks independent of each other; concurrent execution across multiple agents 
  enabled: false
- name: process 
  description: Structured process with validation steps and conditions, usually consists of input, process, condition, output 
  enabled: false
- name: standard 
  description: Sequential, single-agent operation Agent performs some task with or without a {tool}, results in some output 
  enabled: false

