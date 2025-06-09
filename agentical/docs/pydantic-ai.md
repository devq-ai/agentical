### Agents
    The Agent class has full API documentation, but conceptually you can think of an agent as a container for:
    System prompt(s)	A set of instructions for the LLM written by the developer.
    Function tool(s)	Functions that the LLM may call to get information while generating a response.
    Structured output type	The structured datatype the LLM must return at the end of a run, if specified.
    Dependency type constraint	System prompt functions, tools, and output validators may all use dependencies when they're run.
    LLM model	Optional default LLM model associated with the agent. Can also be specified when running the agent.
    Model Settings	Optional default model settings to help fine tune requests. Can also be specified when running the agent.
### Function Tools
    There are a number of ways to register tools with an agent:
    via the @agent.tool decorator — for tools that need access to the agent context
    via the @agent.tool_plain decorator — for tools that do not need access to the agent context
    via the tools keyword argument to Agent which can take either plain functions, or instances of Output
### Messages and chat history
    PydanticAI provides access to messages exchanged during an agent run. These messages can be used both to continue a coherent conversation, and to understand how an agent performed.
    Accessing Messages from Results
        After running an agent, you can access the messages exchanged during that run from the result object.
    Both RunResult (returned by Agent.run, Agent.run_sync) and StreamedRunResult (returned by Agent.run_stream) have the following methods:
        all_messages(): returns all messages, including messages from prior runs. There's also a variant that returns JSON bytes, all_messages_json().
        new_messages(): returns only the messages from the current run. There's also a variant that returns JSON bytes, new_messages_json().
### Unit testing
    Use pytest as your test harness
    If you find yourself typing out long assertions, use inline-snapshot
    Similarly, dirty-equals can be useful for comparing large data structures
    Use TestModel or FunctionModel in place of your actual model to avoid the usage, latency and variability of real LLM calls
    Use Agent.override to replace your model inside your application logic
    Set ALLOW_MODEL_REQUESTS=False globally to block any requests from being made to non-test models accidentally   
### Debugging and Monitoring
    Pydantic Logfire is an observability platform developed by the team who created and maintain Pydantic and PydanticAI. Logfire aims to let you understand your entire application: Gen AI, classic predictive AI, HTTP traffic, database queries and everything else a modern application needs, all using OpenTelemetry.
### Multi-agent Applications
    There are roughly four levels of complexity when building applications with PydanticAI:
    Single agent workflows — what most of the pydantic_ai documentation covers
    Agent delegation — agents using another agent via tools
    Programmatic agent hand-off — one agent runs, then application code calls another agent
    Graph based control flow — for the most complex cases, a graph-based state machine can be used to control the execution of multiple agents 
### Graphs
    Graphs and finite state machines (FSMs) are a powerful abstraction to model, execute, control and visualize complex workflows.
    Alongside PydanticAI, we've developed pydantic-graph — an async graph and state machine library for Python where nodes and edges are defined using type hints.
    While this library is developed as part of PydanticAI; it has no dependency on pydantic-ai and can be considered as a pure graph-based state machine library. You may find it useful whether or not you're using PydanticAI or even building with GenAI.
    pydantic-graph is designed for advanced users and makes heavy use of Python generics and type hints. It is not designed to be as beginner-friendly as PydanticAI.
### Evals
    Pydantic Evals is a powerful evaluation framework designed to help you systematically test and evaluate the performance and accuracy of the systems you build, especially when working with LLMs.
    You can send these traces to any OpenTelemetry-compatible backend, including Pydantic Logfire.
### Image, Audio, Video & Document Input
    If you have a direct URL for the image, you can use ImageUrl
    If you have the image locally, you can also use BinaryContent
    You can provide audio input using either AudioUrl or BinaryContent
    You can provide video input using either VideoUrl or BinaryContent
    You can provide document input using either DocumentUrl or BinaryContent
    If you have a direct URL for the document, you can use DocumentUrl
    You can also use BinaryContent to pass document data directly
### MCP
    Agents act as an MCP Client, connecting to MCP servers to use their tools
### A2A
    The Agent2Agent (A2A) Protocol is an open standard introduced by Google that enables communication and interoperability between AI agents, regardless of the framework or vendor they are built on. At Pydantic, we built the FastA2A library to make it easier to implement the A2A protocol in Python.
