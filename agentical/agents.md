## Agents (count=18)
Base Agent Classes (count=13)

### code_agent
Model: claude-4
Description: Full-stack development agent with code generation, review, and testing capabilities
Workflow: standard, self_feedback
Tools: code_execution, test_gen, test_run, github-mcp, doc_gen
Status: true

### data_sci_agent
Model: claude-4
Description: Data science and analytics specialist with ML/AI capabilities
Workflow: process, parallel
Tools: process_data, generate_chart, jupyter-mcp, expensive_calc, bayes-mcp
Status: true

### dba_agent
Model: claude-4
Description: Database administration with optimization and maintenance workflows
Workflow: process, human_loop
Tools: execute_query, surrealdb-mcp, usage_monitoring, batch_process
Status: true

### devops_agent
Model: claude-4
Description: DevOps automation with CI/CD, infrastructure, and monitoring
Workflow: process, parallel
Tools: mcp-server-buildkite, mcp-server-grafana, external_api, audit_logging
Status: true

### gcp_agent
Model: claude-4
Description: Google Cloud Platform specialist for cloud architecture and deployment
Workflow: process, handoff
Tools: gcp-mcp, external_api, usage_monitoring, create_report
Status: ❌ false

### github_agent
Model: claude-4
Description: GitHub workflow automation and repository management
Workflow: standard, agent_feedback
Tools: github-mcp, code_execution, test_gen, doc_gen
Status: true

### legal_agent
Model: claude-4
Description: Legal document analysis and compliance checking
Workflow: human_loop, process
Tools: doc_gen, create_report, external_api, memory
Status: true

### infosec_agent
Model: claude-4
Description: Information security analysis and threat assessment
Workflow: process, versus
Tools: audit_logging, external_api, create_report, memory
Status: true

### research_agent
Model: claude-4
Description: Research and information gathering with source validation
Workflow: standard, self_feedback
Tools: web_search, scholarly-mcp, crawl4ai-mcp, create_report, memory
Status: true

### tester_agent
Model: claude-4
Description: Quality assurance and testing automation specialist
Workflow: process, parallel
Tools: test_gen, test_run, evals, browser-tools, unit_test
Status: true

### token_agent
Model: claude-4
Description: Token economy and blockchain analysis specialist
Workflow: process, agent_feedback
Tools: external_api, process_data, generate_chart, expensive_calc
Status: true

### uat_agent
Model: claude-4
Description: User acceptance testing with automated validation workflows
Workflow: human_loop, process
Tools: browser-tools, test_run, evals, create_report
Status: true

### ux_agent
Model: claude-4
Description: User experience design and interface optimization
Workflow: human_loop, versus
Tools: browser-tools, shadcn-ui-mcp-server, generate_chart, create_report
Status: true

## Specialized Agent Classes (count=5)

### codifier (codifier_agent)
Model: claude-4
Description: Code transformation and standardization specialist
Workflow: self_feedback, process
Tools: code_execution, format_text, doc_gen, test_gen
Status: true

### inspector (inspector_agent)
Model: claude-4
Description: Code and system inspection with quality analysis
Workflow: process, versus
Tools: audit_logging, test_run, evals, create_report
Status: true

### observer (observer_agent)
Model: claude-4
Description: System monitoring and behavioral analysis
Workflow: standard, parallel
Tools: usage_monitoring, mcp-server-grafana, audit_logging, memory
Status: true

### playmaker (playbook_agent)
Model: claude-4
Description: Strategic playbook development and execution
Workflow: process, handoff
Tools: plan_gen, plan_run, viz_playbook, create_report
Status: true

### super (super_agent)
Model: claude-4
Description: Meta-agent coordinator with multi-agent orchestration
Workflow: handoff, agent_feedback, versus
Tools: memory, plan_gen, plan_run, audit_logging, usage_monitoring
Status: true