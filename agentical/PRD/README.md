# Agentical Framework

Agentical is an agentic framework built on Pydantic AI, designed to create powerful AI agents and workflows. The framework provides a modular approach to building AI systems with agents (who do the work), workflows (how agents interact), tools (what agents can use), and playbooks (configuration files that define objectives, success criteria, agents, tools, and workflows).

## 🚀 Features

- **Hybrid Agent Architecture**: Flexible agent design with core capabilities and specialized extensions
- **Workflow Patterns**: Multiple workflow patterns including parallel execution, feedback loops, and human-in-the-loop
- **Knowledge Base Integration**: SurrealDB-powered knowledge store for both system operations and agent tools
- **Graph-Based Workflows**: Complex workflows using Pydantic-Graph for state management
- **Type Safety**: Leveraging Pydantic for robust type validation throughout the system
- **FastAPI Integration**: Modern API layer with WebSockets, background tasks, and OpenAPI documentation
- **Observability**: Comprehensive monitoring and evaluation framework

## 📦 Installation

```bash
pip install agentical
```

## 🏗️ Quick Start

### Create an Agent

```python
from agentical import create_agent
from agentical.agents.capabilities import TextGenerationCapability

# Create a simple agent
agent = create_agent(
    name="Research Assistant",
    description="An agent that helps with research tasks",
    system_prompts=["You are a helpful research assistant."],
    tools=["web_search", "knowledge_retrieve"],
    model="gpt-4"
)
```

### Define a Workflow

```python
from agentical import create_workflow
from agentical.workflows.patterns import FeedbackLoopWorkflow

# Create a feedback loop workflow
workflow = FeedbackLoopWorkflow(
    name="Research and Summarize",
    description="Research a topic and create a summary"
)

# Add agents to the workflow
workflow.add_agent("researcher", researcher_agent)
workflow.add_agent("writer", writer_agent)
workflow.add_agent("editor", editor_agent)

# Run the workflow
result = await workflow.run({
    "topic": "Advances in quantum computing",
    "max_length": 500
})

print(result.output)
```

### Create a Playbook

```python
from agentical import Playbook

# Define a playbook
playbook = Playbook.from_config({
    "name": "Research Project",
    "objective": "Research and create a comprehensive report on a topic",
    "success_criteria": [
        "Covers key aspects of the topic",
        "Includes recent developments",
        "Well-structured and coherent"
    ],
    "agents": [
        {"id": "researcher", "type": "research_agent"},
        {"id": "writer", "type": "content_writer"},
        {"id": "editor", "type": "content_editor"}
    ],
    "workflows": [
        {
            "id": "research_workflow",
            "type": "partner_feedback_loop",
            "agents": {
                "researcher": "researcher",
                "writer": "writer",
                "editor": "editor"
            }
        }
    ],
    "tools": ["web_search", "knowledge_base", "document_generator"]
})

# Execute the playbook
result = await playbook.execute({
    "topic": "Sustainable energy solutions",
    "depth": "comprehensive",
    "format": "report"
})
```

## 🧠 Knowledge Base Integration

Agentical includes a powerful knowledge base built on SurrealDB:

```python
from agentical.knowledge import KnowledgeService
from agentical.knowledge.models import KnowledgeItem

# Store information in the knowledge base
knowledge_service = KnowledgeService()
await knowledge_service.store(
    KnowledgeItem(
        title="Quantum Computing Basics",
        content="Quantum computing leverages quantum mechanics principles...",
        tags=["quantum", "computing", "technology"]
    )
)

# Retrieve information using semantic search
results = await knowledge_service.search("How do quantum computers work?")
```

## 📋 Components

- **Agents**: The entities that do the work
- **Workflows**: Define how agents interact to solve problems
- **Tools**: Components that agents can use to perform tasks
- **Playbooks**: Configuration files that define objectives, success criteria, agents, tools, and workflows
- **Knowledge Base**: SurrealDB-powered store for both system operations and agent tools

## 🔧 Advanced Features

### Graph-Based Workflows

For complex workflows, Agentical supports Pydantic-Graph integration:

```python
from agentical.workflows.graphs import GraphWorkflow, AgentNode, End
from pydantic import BaseModel

class ResearchState(BaseModel):
    topic: str
    research_results: str = ""
    draft: str = ""
    final_document: str = ""

class ResearchGraph(GraphWorkflow):
    # Implementation of a complex research workflow
    ...
```

### Human-in-the-Loop

```python
from agentical.workflows.patterns import HumanInTheLoopWorkflow

workflow = HumanInTheLoopWorkflow(
    name="Document Approval",
    description="Generate a document and get human approval"
)

# The workflow will pause and wait for human input at certain stages
```

## 📚 Documentation

For more detailed documentation, see the [official documentation](https://agentical.devq.ai/docs).

## 🤝 Contributing

Contributions are welcome! Please see our [contributing guidelines](CONTRIBUTING.md).

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.