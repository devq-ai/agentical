/**
 * Agent Pool Provider for VS Code Tree View
 *
 * Provides tree data for the Agentical agent pool view, showing available
 * agents, their status, capabilities, and performance metrics in a hierarchical
 * tree structure within the VS Code sidebar.
 */

import * as vscode from 'vscode';
import { AgenticalClient, AgentInfo } from '../client/agenticalClient';

export class AgentPoolProvider implements vscode.TreeDataProvider<AgentTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<AgentTreeItem | undefined | null | void> = new vscode.EventEmitter<AgentTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AgentTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private agents: AgentInfo[] = [];
    private groupBy: 'type' | 'status' | 'none' = 'type';

    constructor(private agenticalClient: AgenticalClient) {
        // Listen for agent status updates
        this.agenticalClient.on('agentStatusUpdated', (data: any) => {
            this.handleAgentStatusUpdate(data);
        });

        // Subscribe to real-time agent updates
        this.agenticalClient.subscribeToUpdates(['agent_status_updated', 'agent_registered', 'agent_unregistered']);
    }

    /**
     * Refresh the tree view
     */
    refresh(): void {
        this.loadAgents();
        this._onDidChangeTreeData.fire();
    }

    /**
     * Clear the tree view
     */
    clear(): void {
        this.agents = [];
        this._onDidChangeTreeData.fire();
    }

    /**
     * Set grouping mode
     */
    setGroupBy(groupBy: 'type' | 'status' | 'none'): void {
        this.groupBy = groupBy;
        this.refresh();
    }

    /**
     * Get tree item
     */
    getTreeItem(element: AgentTreeItem): vscode.TreeItem {
        return element;
    }

    /**
     * Get children for tree item
     */
    getChildren(element?: AgentTreeItem): Thenable<AgentTreeItem[]> {
        if (!this.agenticalClient.isConnected()) {
            return Promise.resolve([
                new AgentTreeItem(
                    'Not Connected',
                    'Click to connect to Agentical server',
                    vscode.TreeItemCollapsibleState.None,
                    'disconnected',
                    {
                        command: 'agentical.connect',
                        title: 'Connect to Agentical'
                    }
                )
            ]);
        }

        if (!element) {
            // Root level
            return this.getRootItems();
        } else {
            // Children of a group or agent
            return this.getChildItems(element);
        }
    }

    /**
     * Load agents from server
     */
    private async loadAgents(): Promise<void> {
        try {
            if (this.agenticalClient.isConnected()) {
                this.agents = await this.agenticalClient.getAvailableAgents();
            }
        } catch (error) {
            console.error('Failed to load agents:', error);
            this.agents = [];
        }
    }

    /**
     * Get root level items
     */
    private async getRootItems(): Promise<AgentTreeItem[]> {
        await this.loadAgents();

        if (this.agents.length === 0) {
            return [
                new AgentTreeItem(
                    'No Agents Available',
                    'No agents are currently registered',
                    vscode.TreeItemCollapsibleState.None,
                    'empty'
                )
            ];
        }

        switch (this.groupBy) {
            case 'type':
                return this.getAgentsByType();
            case 'status':
                return this.getAgentsByStatus();
            case 'none':
            default:
                return this.getAgentsFlat();
        }
    }

    /**
     * Get child items for a tree item
     */
    private getChildItems(element: AgentTreeItem): Promise<AgentTreeItem[]> {
        if (element.contextValue === 'group') {
            // Return agents in this group
            const groupAgents = this.agents.filter(agent => {
                if (this.groupBy === 'type') {
                    return agent.type === element.groupKey;
                } else if (this.groupBy === 'status') {
                    return agent.status === element.groupKey;
                }
                return false;
            });

            return Promise.resolve(groupAgents.map(agent => this.createAgentTreeItem(agent)));
        } else if (element.contextValue === 'agent') {
            // Return agent details/capabilities
            return this.getAgentDetails(element.agentInfo!);
        }

        return Promise.resolve([]);
    }

    /**
     * Group agents by type
     */
    private getAgentsByType(): AgentTreeItem[] {
        const typeGroups = new Map<string, AgentInfo[]>();

        this.agents.forEach(agent => {
            if (!typeGroups.has(agent.type)) {
                typeGroups.set(agent.type, []);
            }
            typeGroups.get(agent.type)!.push(agent);
        });

        const items: AgentTreeItem[] = [];

        for (const [type, agents] of typeGroups) {
            const activeCount = agents.filter(a => a.status === 'active').length;
            const totalCount = agents.length;

            items.push(new AgentTreeItem(
                `${this.formatAgentType(type)} (${activeCount}/${totalCount})`,
                `${totalCount} ${type} agent${totalCount !== 1 ? 's' : ''}, ${activeCount} active`,
                vscode.TreeItemCollapsibleState.Collapsed,
                'group',
                undefined,
                type
            ));
        }

        return items.sort((a, b) => a.label!.toString().localeCompare(b.label!.toString()));
    }

    /**
     * Group agents by status
     */
    private getAgentsByStatus(): AgentTreeItem[] {
        const statusGroups = new Map<string, AgentInfo[]>();

        this.agents.forEach(agent => {
            if (!statusGroups.has(agent.status)) {
                statusGroups.set(agent.status, []);
            }
            statusGroups.get(agent.status)!.push(agent);
        });

        const statusOrder = ['active', 'busy', 'inactive', 'error'];
        const items: AgentTreeItem[] = [];

        for (const status of statusOrder) {
            const agents = statusGroups.get(status);
            if (agents && agents.length > 0) {
                items.push(new AgentTreeItem(
                    `${this.formatStatus(status)} (${agents.length})`,
                    `${agents.length} agent${agents.length !== 1 ? 's' : ''} with ${status} status`,
                    vscode.TreeItemCollapsibleState.Collapsed,
                    'group',
                    undefined,
                    status
                ));
            }
        }

        return items;
    }

    /**
     * Get agents in flat list
     */
    private getAgentsFlat(): AgentTreeItem[] {
        return this.agents.map(agent => this.createAgentTreeItem(agent));
    }

    /**
     * Create tree item for agent
     */
    private createAgentTreeItem(agent: AgentInfo): AgentTreeItem {
        const statusIcon = this.getStatusIcon(agent.status);
        const performanceText = agent.performance_score ? ` (${Math.round(agent.performance_score * 100)}%)` : '';

        return new AgentTreeItem(
            `${statusIcon} ${agent.name}${performanceText}`,
            `${this.formatAgentType(agent.type)} • ${this.formatStatus(agent.status)} • ${agent.capabilities.length} capabilities`,
            vscode.TreeItemCollapsibleState.Collapsed,
            'agent',
            {
                command: 'agentical.showAgentDetails',
                title: 'Show Agent Details',
                arguments: [agent]
            },
            undefined,
            agent
        );
    }

    /**
     * Get agent details/capabilities
     */
    private getAgentDetails(agent: AgentInfo): Promise<AgentTreeItem[]> {
        const items: AgentTreeItem[] = [];

        // Basic info
        items.push(new AgentTreeItem(
            `ID: ${agent.id}`,
            'Agent identifier',
            vscode.TreeItemCollapsibleState.None,
            'info'
        ));

        items.push(new AgentTreeItem(
            `Type: ${this.formatAgentType(agent.type)}`,
            'Agent type classification',
            vscode.TreeItemCollapsibleState.None,
            'info'
        ));

        items.push(new AgentTreeItem(
            `Status: ${this.formatStatus(agent.status)}`,
            'Current agent status',
            vscode.TreeItemCollapsibleState.None,
            'info'
        ));

        if (agent.performance_score) {
            items.push(new AgentTreeItem(
                `Performance: ${Math.round(agent.performance_score * 100)}%`,
                'Agent performance score',
                vscode.TreeItemCollapsibleState.None,
                'info'
            ));
        }

        if (agent.last_activity) {
            const lastActivity = new Date(agent.last_activity);
            items.push(new AgentTreeItem(
                `Last Activity: ${lastActivity.toLocaleString()}`,
                'Last recorded activity timestamp',
                vscode.TreeItemCollapsibleState.None,
                'info'
            ));
        }

        // Capabilities
        if (agent.capabilities.length > 0) {
            items.push(new AgentTreeItem(
                `Capabilities (${agent.capabilities.length})`,
                'Agent capabilities and features',
                vscode.TreeItemCollapsibleState.Collapsed,
                'capabilities'
            ));

            // Add capability items
            agent.capabilities.forEach(capability => {
                items.push(new AgentTreeItem(
                    `• ${this.formatCapability(capability)}`,
                    `Capability: ${capability}`,
                    vscode.TreeItemCollapsibleState.None,
                    'capability'
                ));
            });
        }

        return Promise.resolve(items);
    }

    /**
     * Handle agent status updates
     */
    private handleAgentStatusUpdate(data: any): void {
        const { agent_id, status, performance_score } = data;

        const agentIndex = this.agents.findIndex(a => a.id === agent_id);
        if (agentIndex >= 0) {
            this.agents[agentIndex].status = status;
            if (performance_score !== undefined) {
                this.agents[agentIndex].performance_score = performance_score;
            }
            this.refresh();
        }
    }

    /**
     * Format agent type for display
     */
    private formatAgentType(type: string): string {
        return type.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    /**
     * Format status for display
     */
    private formatStatus(status: string): string {
        switch (status) {
            case 'active': return 'Active';
            case 'inactive': return 'Inactive';
            case 'busy': return 'Busy';
            case 'error': return 'Error';
            default: return status.charAt(0).toUpperCase() + status.slice(1);
        }
    }

    /**
     * Format capability for display
     */
    private formatCapability(capability: string): string {
        return capability.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    /**
     * Get status icon
     */
    private getStatusIcon(status: string): string {
        switch (status) {
            case 'active': return '🟢';
            case 'busy': return '🟡';
            case 'inactive': return '⚪';
            case 'error': return '🔴';
            default: return '⚫';
        }
    }
}

/**
 * Tree item for agent pool
 */
export class AgentTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly tooltip: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly contextValue: string,
        public readonly command?: vscode.Command,
        public readonly groupKey?: string,
        public readonly agentInfo?: AgentInfo
    ) {
        super(label, collapsibleState);
        this.tooltip = tooltip;
        this.contextValue = contextValue;
        this.command = command;

        // Set appropriate icons
        this.iconPath = this.getIcon();
    }

    private getIcon(): vscode.ThemeIcon | undefined {
        switch (this.contextValue) {
            case 'agent':
                return new vscode.ThemeIcon('robot');
            case 'group':
                return new vscode.ThemeIcon('folder');
            case 'capability':
                return new vscode.ThemeIcon('gear');
            case 'capabilities':
                return new vscode.ThemeIcon('tools');
            case 'info':
                return new vscode.ThemeIcon('info');
            case 'disconnected':
                return new vscode.ThemeIcon('debug-disconnect');
            case 'empty':
                return new vscode.ThemeIcon('circle-slash');
            default:
                return undefined;
        }
    }
}
