# README_wrenchai

## Wrench AI

This repository contains the code for Wrench AI, an open-source agentic AI framework. The framework allows you to define and orchestrate intelligent agents to perform complex tasks by combining the power of Large Language Models (LLMs) with Bayesian reasoning and a flexible tool integration system. This MVP focuses on a Python framework for agent definition and execution using configuration files. with a foundational design considering future integration with the ZED IDE via the Model Context Protocol (MCP).

### Getting Started

1. Clone the Repository:
    ```bash
    git clone <repository_url>
    cd wrenchai
    ```
2. Install Dependencies:
    ```bash
    pip install -r requirements.txt # Placeholder - add your requirements installation command
    ```
3. Run the Streamlit App:
    ```bash
    streamlit run streamlit_app/main.py # Assuming main.py is your Streamlit entry point
    ```
4. This will open the application in your web browser.

### Project Structure

+ core/: Contains the core logic of the agentic framework, including agent definitions, configuration files, playbooks, and tools.
+ core/agents/: Defines the SuperAgent, InspectorAgent, and JourneyAgent classes.
+ core/configs/: Stores YAML configuration files for agents, playbooks, and pricing data.
+ core/playbooks/: Contains example playbooks in YAML format.
+ core/tools/: Implements the tools that agents can use (e.g., web search, code execution).
+ core/utils.py** : Provides utility functions like cost calculation and logging.
+ streamlit_app/: Contains the code for the Streamlit user interface.
+ docker/:  Will contain Dockerfiles and other Docker-related files for containerization (future).
+ tests/: Will contain unit tests for the framework (future).

## Roadmap

### Generation 1 (MVP)

+ Core agentic framework implementation:
    - SuperAgent: Orchestrates the overall process, analyzes user requests, assigns roles and tools, and creates the execution plan.
    - InspectorAgent: Monitors the progress of Journey agents, evaluates their outputs using Bayesian reasoning, and reports to the SuperAgent.
    - JourneyAgent: Executes specific tasks according to assigned playbooks and utilizes allocated tools.
+ Bayesian reasoning for decision-making and evaluation within the InspectorAgent.
+ Basic tool integration (initial set: web search, code execution).
+ Streamlit UI for basic interaction:
    - Simple user input for requests.
    - Verbose output explaining agent actions and reasoning.
    - Progress indicators.
    - Cost tracking.
+ YAML-based configuration for agents and playbooks.
+ Cost tracking for LLM API usage and (basic) GCP resource usage.
+ Dockerization of agents for isolation and reproducibility.
+ GitHub integration for version control, collaboration, and CI/CD.
+ Foundational design considering ZED IDE integration via the Model Context Protocol (MCP) [based on our conversation history and]. This will allow for potential future integration with Zed's Agent Panel as a Context Server.

### Generation 2 (Post-MVP)

+ Visual Workflow Editor (React-based): Replace YAML playbooks with a drag-and-drop interface for creating and managing agent workflows, inspired by tools like Praison.ai's canvas.
+ Expanded Tool Catalog: Add more pre-built tools to the framework, covering a wider range of functionalities.
+ Advanced Data Connection Management: Implement a more robust and user-friendly system for managing connections to various data sources (databases, cloud storage, APIs).
+ Multiple Trigger Mechanisms: Support different trigger types for agent execution, including schedule triggers, webhook triggers, and data change triggers.
+ Enhanced Agent Communication: Refine and expand the mechanisms for communication between agents.
+ Enhanced ZED IDE Integration: [based on our conversation history and]
    - Develop a Context Server extension for ZED using MCP. This would enable Wrench AI agents to provide context and functionalities within ZED, potentially enhancing the Agent Panel.
    - Explore making Wrench AI agents available as profiles or tools within the Agent Panel.
    - Potentially leverage ZED's Command Palette to access Wrench AI functionalities.
    - Consider developing the extension using Rust and compiling to WebAssembly as per ZED's extension development guidelines.

## Contributing

We welcome contributions to Wrench AI! If you'd like to contribute, please follow these guidelines:

1. Fork the repository.
2. Create a branch.
3. Make your changes.
4. Write tests.
5. Commit your changes.
6. Push your branch.
7. Create a pull request.
8. Code Review.

Please make sure your code adheres to the following guidelines:

- Follow the existing code style.
- Write clear and concise code.
- Comment your code where necessary.
- Write unit tests.
- Keep your pull requests focused on a single feature or bug fix.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Project Structure
Here's the repository tree represented in YAML format, based on the 
```
wrenchai:
  description: "Root directory of the Wrench AI project"
  contents:
    - filename: ".gitignore"
      description: "Files and directories to ignore in Git"
    - filename: "LICENSE"
      description: "Project license (MIT License)"
    - filename: "README.md"
      description: "Project description and instructions"
    - filename: "requirements.txt"
      description: "Python dependencies for the core framework"
    - directory: "streamlit_app"
      description: "Directory for the Streamlit UI"
      contents:
        - filename: "app.py"
          description: "Main Streamlit application file"
        - filename: "requirements.txt"
          description: "Python dependencies for the Streamlit app"
    - directory: "core"
      description: "Core framework logic"
      contents:
        - directory: "agents"
          description: "Agent definitions"
          contents:
            - filename: "super_agent.py"
              description: "Super agent class"
            - filename: "inspector_agent.py"
              description: "Inspector agent class"
            - filename: "journey_agent.py"
              description: "Base class for Journey agents"
            - filename: "__init__.py"
        - directory: "configs"
          description: "YAML configuration files"
          contents:
            - filename: "super_agent_config.yaml"
            - filename: "inspector_agent_config.yaml"
            - filename: "journey_agent_template.yaml"
            - filename: "playbook_template.yaml"
            - filename: "pricing_data.yaml"
        - directory: "playbooks"
          description: "Playbook definitions (YAML)"
          contents:
            - filename: "example_playbook.yaml"
              description: "Example playbook"
        - directory: "tools"
          description: "Tool implementations"
          contents:
            - filename: "web_search.py"
              description: "Example tool: Web search"
            - filename: "code_execution.py"
              description: "Example tool: Code execution"
            - filename: "__init__.py"
            - filename: "..."
              description: "Other tools"
        - filename: "utils.py"
          description: "Utility functions (e.g., cost calculation, logging)"
        - filename: "__init__.py"
    - directory: "docker"
      description: "Docker-related files (future)"
      contents:
        - filename: "..."
    - directory: "tests"
      description: "Unit tests (future)"
      contents:
        - filename: "..."
```

## Key Updates and Explanations

+ MVP Description: The MVP description now explicitly mentions the **Python framework**, **configuration files**, and the foundational consideration for **ZED IDE/MCP integration** based on our previous discussion.
+ Roadmap - MVP: The MVP section remains largely the same but now explicitly notes the consideration for ZED/MCP.
+ Roadmap - Post-MVP: A new section **"Enhanced ZED IDE Integration"** has been added to Generation 2. This section highlights the potential for developing a **Context Server extension using MCP**, which aligns with how Zed interacts with external data and tools to enhance features like the **Agent Panel**. It also mentions leveraging Zed's extension development tools like **Rust** and **WebAssembly**.
+ YAML Repo Tree: The YAML representation accurately reflects the directory structure outlined in the README.
