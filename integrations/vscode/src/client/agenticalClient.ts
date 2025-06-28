/**
 * Agentical Client for VS Code Extension
 *
 * Handles communication with the Agentical server API, providing a clean
 * interface for all agent operations, workflow management, and real-time
 * updates via WebSocket connections.
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import * as WebSocket from 'ws';
import { ConfigurationManager } from '../config/configurationManager';
import { LoggingManager } from '../utils/loggingManager';

export interface AgentInfo {
    id: string;
    name: string;
    type: string;
    status: 'active' | 'inactive' | 'busy' | 'error';
    capabilities: string[];
    last_activity: string;
    performance_score: number;
}

export interface WorkflowInfo {
    id: string;
    name: string;
    description: string;
    type: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
    created_at: string;
    updated_at: string;
    steps: WorkflowStep[];
}

export interface WorkflowStep {
    id: string;
    name: string;
    type: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
    agent_id?: string;
    configuration: any;
}

export interface WorkflowExecution {
    id: string;
    workflow_id: string;
    status: string;
    started_at: string;
    progress: number;
    current_step?: string;
    error_message?: string;
}

export interface CodeGenerationRequest {
    prompt: string;
    language: string;
    context?: string;
    framework?: string;
    style?: 'clean' | 'optimized' | 'documented';
}

export interface CodeGenerationResult {
    code: string;
    explanation: string;
    suggestions: string[];
    confidence_score: number;
}

export interface CodeReviewRequest {
    code: string;
    language: string;
    filename?: string;
    review_type?: 'security' | 'performance' | 'style' | 'comprehensive';
}

export interface CodeReviewResult {
    overall_score: number;
    issues: CodeIssue[];
    suggestions: string[];
    summary: string;
    metrics: {
        complexity: number;
        maintainability: number;
        security_score: number;
        performance_score: number;
    };
}

export interface CodeIssue {
    type: 'error' | 'warning' | 'info' | 'suggestion';
    severity: 'critical' | 'high' | 'medium' | 'low';
    message: string;
    line?: number;
    column?: number;
    rule?: string;
    fix_suggestion?: string;
}

export interface CodeOptimizationRequest {
    code: string;
    language: string;
    optimizationType: 'performance' | 'memory' | 'readability' | 'size';
}

export interface CodeOptimizationResult {
    optimizedCode: string;
    explanation: string;
    improvements: string[];
    performance_gain: number;
}

export interface TestGenerationRequest {
    code: string;
    language: string;
    testFramework: string;
    coverage: 'basic' | 'comprehensive' | 'edge_cases';
}

export interface TestGenerationResult {
    tests: string;
    coverage_analysis: {
        estimated_coverage: number;
        test_cases: number;
        edge_cases: number;
    };
    explanation: string;
}

export interface DeploymentRequest {
    platform: string;
    environment: string;
    source: string;
    config?: any;
}

export interface DeploymentResult {
    jobId: string;
    status: string;
    estimated_duration: number;
    deployment_url?: string;
}

export interface ResearchRequest {
    topic: string;
    depth: 'basic' | 'comprehensive' | 'expert';
    sources: string[];
    focus_areas?: string[];
}

export interface ResearchResult {
    summary: string;
    key_findings: string[];
    sources: ResearchSource[];
    related_topics: string[];
    confidence_score: number;
}

export interface ResearchSource {
    title: string;
    url: string;
    type: 'academic' | 'web' | 'documentation' | 'news';
    relevance_score: number;
    excerpt: string;
}

export interface SystemMetrics {
    agents: {
        total: number;
        active: number;
        average_performance: number;
    };
    workflows: {
        total_executions: number;
        success_rate: number;
        average_duration: number;
    };
    system: {
        cpu_usage: number;
        memory_usage: number;
        response_time: number;
        uptime: number;
    };
}

export class AgenticalClient {
    private httpClient: AxiosInstance;
    private wsClient: WebSocket | null = null;
    private isConnectedState = false;
    private connectionPromise: Promise<void> | null = null;
    private eventListeners: Map<string, Function[]> = new Map();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectInterval = 5000;

    constructor(
        private configManager: ConfigurationManager,
        private loggingManager: LoggingManager
    ) {
        this.httpClient = axios.create({
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'Agentical-VSCode-Extension/1.0.0'
            }
        });

        this.setupHttpInterceptors();
    }

    /**
     * Set up HTTP request and response interceptors
     */
    private setupHttpInterceptors(): void {
        // Request interceptor
        this.httpClient.interceptors.request.use(
            (config) => {
                const serverUrl = this.configManager.getServerUrl();
                const apiKey = this.configManager.getApiKey();

                config.baseURL = serverUrl;

                if (apiKey) {
                    config.headers['Authorization'] = `Bearer ${apiKey}`;
                }

                this.loggingManager.debug(`HTTP Request: ${config.method?.toUpperCase()} ${config.url}`);
                return config;
            },
            (error) => {
                this.loggingManager.error('HTTP Request Error', error);
                return Promise.reject(error);
            }
        );

        // Response interceptor
        this.httpClient.interceptors.response.use(
            (response) => {
                this.loggingManager.debug(`HTTP Response: ${response.status} ${response.config.url}`);
                return response;
            },
            (error) => {
                this.loggingManager.error('HTTP Response Error', error);
                return Promise.reject(error);
            }
        );
    }

    /**
     * Connect to Agentical server
     */
    async connect(): Promise<void> {
        if (this.isConnectedState) {
            return;
        }

        if (this.connectionPromise) {
            return this.connectionPromise;
        }

        this.connectionPromise = this.performConnection();

        try {
            await this.connectionPromise;
        } finally {
            this.connectionPromise = null;
        }
    }

    /**
     * Perform the actual connection
     */
    private async performConnection(): Promise<void> {
        try {
            // Test HTTP connection
            const response = await this.httpClient.get('/api/v1/health');

            if (response.status !== 200) {
                throw new Error(`Server returned status ${response.status}`);
            }

            this.loggingManager.info('HTTP connection to Agentical server established');

            // Establish WebSocket connection
            await this.connectWebSocket();

            this.isConnectedState = true;
            this.reconnectAttempts = 0;
            this.emit('connected');

        } catch (error) {
            this.loggingManager.error('Failed to connect to Agentical server', error);
            throw error;
        }
    }

    /**
     * Connect WebSocket for real-time updates
     */
    private async connectWebSocket(): Promise<void> {
        return new Promise((resolve, reject) => {
            try {
                const serverUrl = this.configManager.getServerUrl();
                const wsUrl = serverUrl.replace(/^http/, 'ws') + '/ws';

                this.wsClient = new WebSocket(wsUrl);

                this.wsClient.on('open', () => {
                    this.loggingManager.info('WebSocket connection established');
                    resolve();
                });

                this.wsClient.on('message', (data: WebSocket.Data) => {
                    try {
                        const message = JSON.parse(data.toString());
                        this.handleWebSocketMessage(message);
                    } catch (error) {
                        this.loggingManager.error('Failed to parse WebSocket message', error);
                    }
                });

                this.wsClient.on('close', () => {
                    this.loggingManager.warn('WebSocket connection closed');
                    this.handleWebSocketClose();
                });

                this.wsClient.on('error', (error) => {
                    this.loggingManager.error('WebSocket error', error);
                    reject(error);
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Handle WebSocket messages
     */
    private handleWebSocketMessage(message: any): void {
        const { type, data } = message;

        switch (type) {
            case 'agent_status_updated':
                this.emit('agentStatusUpdated', data);
                break;
            case 'workflow_progress':
                this.emit('workflowProgress', data);
                break;
            case 'workflow_completed':
                this.emit('workflowCompleted', data);
                break;
            case 'system_metrics':
                this.emit('systemMetrics', data);
                break;
            default:
                this.loggingManager.debug(`Unknown WebSocket message type: ${type}`);
        }
    }

    /**
     * Handle WebSocket connection close
     */
    private handleWebSocketClose(): void {
        this.wsClient = null;

        if (this.isConnectedState && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.loggingManager.info(`Attempting to reconnect WebSocket (attempt ${this.reconnectAttempts + 1})`);

            setTimeout(async () => {
                try {
                    this.reconnectAttempts++;
                    await this.connectWebSocket();
                    this.reconnectAttempts = 0;
                } catch (error) {
                    this.loggingManager.error('WebSocket reconnection failed', error);
                }
            }, this.reconnectInterval);
        }
    }

    /**
     * Disconnect from server
     */
    async disconnect(): Promise<void> {
        this.isConnectedState = false;

        if (this.wsClient) {
            this.wsClient.close();
            this.wsClient = null;
        }

        this.emit('disconnected');
        this.loggingManager.info('Disconnected from Agentical server');
    }

    /**
     * Check if client is connected
     */
    isConnected(): boolean {
        return this.isConnectedState;
    }

    /**
     * Get available agents
     */
    async getAvailableAgents(): Promise<AgentInfo[]> {
        const response = await this.httpClient.get('/api/v1/agents');
        return response.data.agents;
    }

    /**
     * Get available workflows
     */
    async getAvailableWorkflows(): Promise<WorkflowInfo[]> {
        const response = await this.httpClient.get('/api/v1/workflows');
        return response.data.workflows;
    }

    /**
     * Execute workflow
     */
    async executeWorkflow(workflowId: string, inputData?: any): Promise<WorkflowExecution> {
        const response = await this.httpClient.post('/api/v1/workflows/execute', {
            workflow_id: workflowId,
            input_data: inputData || {}
        });
        return response.data;
    }

    /**
     * Generate code
     */
    async generateCode(request: CodeGenerationRequest): Promise<CodeGenerationResult> {
        const response = await this.httpClient.post('/api/v1/agents/code/generate', request);
        return response.data;
    }

    /**
     * Review code
     */
    async reviewCode(request: CodeReviewRequest): Promise<CodeReviewResult> {
        const response = await this.httpClient.post('/api/v1/agents/code/review', request);
        return response.data;
    }

    /**
     * Optimize code
     */
    async optimizeCode(request: CodeOptimizationRequest): Promise<CodeOptimizationResult> {
        const response = await this.httpClient.post('/api/v1/agents/code/optimize', request);
        return response.data;
    }

    /**
     * Generate tests
     */
    async generateTests(request: TestGenerationRequest): Promise<TestGenerationResult> {
        const response = await this.httpClient.post('/api/v1/agents/code/tests', request);
        return response.data;
    }

    /**
     * Deploy application
     */
    async deployApplication(request: DeploymentRequest): Promise<DeploymentResult> {
        const response = await this.httpClient.post('/api/v1/agents/devops/deploy', request);
        return response.data;
    }

    /**
     * Research topic
     */
    async researchTopic(request: ResearchRequest): Promise<ResearchResult> {
        const response = await this.httpClient.post('/api/v1/agents/research/topic', request);
        return response.data;
    }

    /**
     * Get system metrics
     */
    async getSystemMetrics(): Promise<SystemMetrics> {
        const response = await this.httpClient.get('/api/v1/analytics/metrics');
        return response.data;
    }

    /**
     * Get workflow history
     */
    async getWorkflowHistory(limit: number = 50): Promise<WorkflowExecution[]> {
        const response = await this.httpClient.get(`/api/v1/workflows/history?limit=${limit}`);
        return response.data.executions;
    }

    /**
     * Get workflow execution details
     */
    async getWorkflowExecution(executionId: string): Promise<WorkflowExecution> {
        const response = await this.httpClient.get(`/api/v1/workflows/executions/${executionId}`);
        return response.data;
    }

    /**
     * Pause workflow execution
     */
    async pauseWorkflow(executionId: string): Promise<void> {
        await this.httpClient.post(`/api/v1/workflows/executions/${executionId}/pause`);
    }

    /**
     * Resume workflow execution
     */
    async resumeWorkflow(executionId: string): Promise<void> {
        await this.httpClient.post(`/api/v1/workflows/executions/${executionId}/resume`);
    }

    /**
     * Cancel workflow execution
     */
    async cancelWorkflow(executionId: string): Promise<void> {
        await this.httpClient.post(`/api/v1/workflows/executions/${executionId}/cancel`);
    }

    /**
     * Create new workflow
     */
    async createWorkflow(workflow: Partial<WorkflowInfo>): Promise<WorkflowInfo> {
        const response = await this.httpClient.post('/api/v1/workflows', workflow);
        return response.data;
    }

    /**
     * Update workflow
     */
    async updateWorkflow(workflowId: string, workflow: Partial<WorkflowInfo>): Promise<WorkflowInfo> {
        const response = await this.httpClient.put(`/api/v1/workflows/${workflowId}`, workflow);
        return response.data;
    }

    /**
     * Delete workflow
     */
    async deleteWorkflow(workflowId: string): Promise<void> {
        await this.httpClient.delete(`/api/v1/workflows/${workflowId}`);
    }

    /**
     * Event handling
     */
    on(event: string, listener: Function): void {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event)!.push(listener);
    }

    off(event: string, listener: Function): void {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const index = listeners.indexOf(listener);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    private emit(event: string, data?: any): void {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(listener => {
                try {
                    listener(data);
                } catch (error) {
                    this.loggingManager.error(`Event listener error for ${event}`, error);
                }
            });
        }
    }

    /**
     * Send WebSocket message
     */
    private sendWebSocketMessage(message: any): void {
        if (this.wsClient && this.wsClient.readyState === WebSocket.OPEN) {
            this.wsClient.send(JSON.stringify(message));
        }
    }

    /**
     * Subscribe to real-time updates
     */
    subscribeToUpdates(types: string[]): void {
        this.sendWebSocketMessage({
            type: 'subscribe',
            data: { event_types: types }
        });
    }

    /**
     * Unsubscribe from real-time updates
     */
    unsubscribeFromUpdates(types: string[]): void {
        this.sendWebSocketMessage({
            type: 'unsubscribe',
            data: { event_types: types }
        });
    }
}
