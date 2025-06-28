/**
 * Agentical VS Code Extension
 *
 * Main extension entry point for VS Code integration with the Agentical
 * AI Agent Framework. Provides seamless integration for multi-agent workflows,
 * code generation, and intelligent automation directly within VS Code.
 *
 * Features:
 * - Real-time connection to Agentical server
 * - Multi-agent workflow execution
 * - Code generation and optimization
 * - DevOps automation integration
 * - GitHub repository management
 * - Research and UX analysis capabilities
 * - Comprehensive UI panels and views
 */

import * as vscode from 'vscode';
import { AgenticalClient } from './client/agenticalClient';
import { AgentPoolProvider } from './providers/agentPoolProvider';
import { WorkflowProvider } from './providers/workflowProvider';
import { HistoryProvider } from './providers/historyProvider';
import { MetricsProvider } from './providers/metricsProvider';
import { PlaybookManager } from './managers/playbookManager';
import { CodeAnalyzer } from './analyzers/codeAnalyzer';
import { StatusBarManager } from './ui/statusBarManager';
import { NotificationManager } from './ui/notificationManager';
import { WebviewManager } from './ui/webviewManager';
import { ConfigurationManager } from './config/configurationManager';
import { LoggingManager } from './utils/loggingManager';

// Global extension context
let extensionContext: vscode.ExtensionContext;
let agenticalClient: AgenticalClient;
let statusBarManager: StatusBarManager;
let notificationManager: NotificationManager;
let loggingManager: LoggingManager;

// Data providers
let agentPoolProvider: AgentPoolProvider;
let workflowProvider: WorkflowProvider;
let historyProvider: HistoryProvider;
let metricsProvider: MetricsProvider;

// Managers
let playbookManager: PlaybookManager;
let codeAnalyzer: CodeAnalyzer;
let webviewManager: WebviewManager;
let configManager: ConfigurationManager;

/**
 * Extension activation entry point
 */
export async function activate(context: vscode.ExtensionContext) {
    extensionContext = context;

    // Initialize logging first
    loggingManager = new LoggingManager(context);
    loggingManager.info('Activating Agentical VS Code Extension...');

    try {
        // Initialize configuration
        configManager = new ConfigurationManager();

        // Initialize UI managers
        statusBarManager = new StatusBarManager(context);
        notificationManager = new NotificationManager();
        webviewManager = new WebviewManager(context);

        // Initialize client
        agenticalClient = new AgenticalClient(configManager, loggingManager);

        // Initialize data providers
        agentPoolProvider = new AgentPoolProvider(agenticalClient);
        workflowProvider = new WorkflowProvider(agenticalClient);
        historyProvider = new HistoryProvider(agenticalClient);
        metricsProvider = new MetricsProvider(agenticalClient);

        // Initialize managers
        playbookManager = new PlaybookManager(agenticalClient, context);
        codeAnalyzer = new CodeAnalyzer(agenticalClient);

        // Register tree data providers
        vscode.window.registerTreeDataProvider('agentical-agents', agentPoolProvider);
        vscode.window.registerTreeDataProvider('agentical-workflows', workflowProvider);
        vscode.window.registerTreeDataProvider('agentical-history', historyProvider);
        vscode.window.registerTreeDataProvider('agentical-metrics', metricsProvider);

        // Register all commands
        registerCommands(context);

        // Set up event listeners
        setupEventListeners();

        // Auto-connect if configured
        if (configManager.getAutoConnect()) {
            await connectToServer();
        }

        loggingManager.info('Agentical VS Code Extension activated successfully');
        notificationManager.showInfo('Agentical extension activated successfully!');

    } catch (error) {
        loggingManager.error('Failed to activate extension', error);
        notificationManager.showError(`Failed to activate Agentical extension: ${error}`);
    }
}

/**
 * Extension deactivation
 */
export async function deactivate() {
    loggingManager?.info('Deactivating Agentical VS Code Extension...');

    try {
        // Disconnect from server
        if (agenticalClient?.isConnected()) {
            await agenticalClient.disconnect();
        }

        // Clean up managers
        statusBarManager?.dispose();
        webviewManager?.dispose();

        loggingManager?.info('Agentical VS Code Extension deactivated');
    } catch (error) {
        loggingManager?.error('Error during deactivation', error);
    }
}

/**
 * Register all extension commands
 */
function registerCommands(context: vscode.ExtensionContext) {
    const commands = [
        // Connection commands
        vscode.commands.registerCommand('agentical.connect', connectToServer),
        vscode.commands.registerCommand('agentical.disconnect', disconnectFromServer),

        // Playbook and workflow commands
        vscode.commands.registerCommand('agentical.createPlaybook', createPlaybook),
        vscode.commands.registerCommand('agentical.executeWorkflow', executeWorkflow),

        // Code generation commands
        vscode.commands.registerCommand('agentical.generateCode', generateCode),
        vscode.commands.registerCommand('agentical.reviewCode', reviewCode),
        vscode.commands.registerCommand('agentical.optimizeCode', optimizeCode),
        vscode.commands.registerCommand('agentical.generateTests', generateTests),

        // Agent-specific commands
        vscode.commands.registerCommand('agentical.deployApplication', deployApplication),
        vscode.commands.registerCommand('agentical.manageRepository', manageRepository),
        vscode.commands.registerCommand('agentical.researchTopic', researchTopic),
        vscode.commands.registerCommand('agentical.uxAnalysis', uxAnalysis),

        // UI commands
        vscode.commands.registerCommand('agentical.showAgentPool', showAgentPool),
        vscode.commands.registerCommand('agentical.showWorkflowHistory', showWorkflowHistory),
        vscode.commands.registerCommand('agentical.showSystemMetrics', showSystemMetrics),
        vscode.commands.registerCommand('agentical.openDashboard', openDashboard),

        // Tree view commands
        vscode.commands.registerCommand('agentical.refreshAgents', () => agentPoolProvider.refresh()),
        vscode.commands.registerCommand('agentical.refreshWorkflows', () => workflowProvider.refresh()),
        vscode.commands.registerCommand('agentical.refreshHistory', () => historyProvider.refresh()),
        vscode.commands.registerCommand('agentical.refreshMetrics', () => metricsProvider.refresh()),
    ];

    commands.forEach(command => context.subscriptions.push(command));
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Configuration change listener
    vscode.workspace.onDidChangeConfiguration(event => {
        if (event.affectsConfiguration('agentical')) {
            configManager.reload();
            loggingManager.info('Agentical configuration reloaded');
        }
    });

    // Document save listener for auto-review
    vscode.workspace.onDidSaveTextDocument(async document => {
        if (configManager.getAutoReview() && agenticalClient.isConnected()) {
            await codeAnalyzer.analyzeDocument(document);
        }
    });

    // Selection change listener
    vscode.window.onDidChangeTextEditorSelection(event => {
        // Update context for selected text
        const hasSelection = !event.textEditor.selection.isEmpty;
        vscode.commands.executeCommand('setContext', 'agentical.hasSelection', hasSelection);
    });
}

/**
 * Connect to Agentical server
 */
async function connectToServer(): Promise<void> {
    try {
        statusBarManager.setConnecting();
        loggingManager.info('Connecting to Agentical server...');

        await agenticalClient.connect();

        // Update UI state
        vscode.commands.executeCommand('setContext', 'agentical.connected', true);
        statusBarManager.setConnected();

        // Refresh all providers
        agentPoolProvider.refresh();
        workflowProvider.refresh();
        historyProvider.refresh();
        metricsProvider.refresh();

        notificationManager.showInfo('Successfully connected to Agentical server!');
        loggingManager.info('Connected to Agentical server successfully');

    } catch (error) {
        statusBarManager.setDisconnected();
        vscode.commands.executeCommand('setContext', 'agentical.connected', false);

        const errorMessage = `Failed to connect to Agentical server: ${error}`;
        notificationManager.showError(errorMessage);
        loggingManager.error('Connection failed', error);

        throw error;
    }
}

/**
 * Disconnect from Agentical server
 */
async function disconnectFromServer(): Promise<void> {
    try {
        loggingManager.info('Disconnecting from Agentical server...');

        await agenticalClient.disconnect();

        // Update UI state
        vscode.commands.executeCommand('setContext', 'agentical.connected', false);
        statusBarManager.setDisconnected();

        // Clear providers
        agentPoolProvider.clear();
        workflowProvider.clear();
        historyProvider.clear();
        metricsProvider.clear();

        notificationManager.showInfo('Disconnected from Agentical server');
        loggingManager.info('Disconnected from Agentical server successfully');

    } catch (error) {
        const errorMessage = `Failed to disconnect from Agentical server: ${error}`;
        notificationManager.showError(errorMessage);
        loggingManager.error('Disconnection failed', error);
    }
}

/**
 * Create new playbook
 */
async function createPlaybook(uri?: vscode.Uri): Promise<void> {
    try {
        const workspaceFolder = uri ? vscode.workspace.getWorkspaceFolder(uri) :
                               vscode.workspace.workspaceFolders?.[0];

        if (!workspaceFolder) {
            notificationManager.showError('No workspace folder selected');
            return;
        }

        await playbookManager.createPlaybook(workspaceFolder.uri);

    } catch (error) {
        notificationManager.showError(`Failed to create playbook: ${error}`);
        loggingManager.error('Playbook creation failed', error);
    }
}

/**
 * Execute workflow
 */
async function executeWorkflow(): Promise<void> {
    try {
        if (!agenticalClient.isConnected()) {
            notificationManager.showError('Not connected to Agentical server');
            return;
        }

        const workflows = await agenticalClient.getAvailableWorkflows();

        if (workflows.length === 0) {
            notificationManager.showInfo('No workflows available');
            return;
        }

        const selectedWorkflow = await vscode.window.showQuickPick(
            workflows.map(w => ({ label: w.name, description: w.description, workflow: w })),
            { placeHolder: 'Select a workflow to execute' }
        );

        if (selectedWorkflow) {
            const execution = await agenticalClient.executeWorkflow(selectedWorkflow.workflow.id);
            notificationManager.showInfo(`Workflow "${selectedWorkflow.label}" started. Execution ID: ${execution.id}`);
            workflowProvider.refresh();
        }

    } catch (error) {
        notificationManager.showError(`Failed to execute workflow: ${error}`);
        loggingManager.error('Workflow execution failed', error);
    }
}

/**
 * Generate code with AI
 */
async function generateCode(): Promise<void> {
    try {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            notificationManager.showError('No active editor');
            return;
        }

        const prompt = await vscode.window.showInputBox({
            placeHolder: 'Describe what code you want to generate...',
            prompt: 'Code Generation Prompt'
        });

        if (!prompt) return;

        const selection = editor.selection;
        const context = selection.isEmpty ? '' : editor.document.getText(selection);

        const result = await agenticalClient.generateCode({
            prompt,
            language: editor.document.languageId,
            context,
            framework: await detectFramework(editor.document)
        });

        if (result.code) {
            await editor.edit(editBuilder => {
                if (selection.isEmpty) {
                    editBuilder.insert(editor.selection.active, result.code);
                } else {
                    editBuilder.replace(selection, result.code);
                }
            });

            notificationManager.showInfo('Code generated successfully!');
        }

    } catch (error) {
        notificationManager.showError(`Failed to generate code: ${error}`);
        loggingManager.error('Code generation failed', error);
    }
}

/**
 * Review code with AI
 */
async function reviewCode(): Promise<void> {
    try {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            notificationManager.showError('No active editor');
            return;
        }

        const selection = editor.selection;
        const code = selection.isEmpty ? editor.document.getText() : editor.document.getText(selection);

        if (!code.trim()) {
            notificationManager.showError('No code selected for review');
            return;
        }

        const review = await agenticalClient.reviewCode({
            code,
            language: editor.document.languageId,
            filename: editor.document.fileName
        });

        // Show review results in webview
        await webviewManager.showCodeReview(review);

    } catch (error) {
        notificationManager.showError(`Failed to review code: ${error}`);
        loggingManager.error('Code review failed', error);
    }
}

/**
 * Optimize code with AI
 */
async function optimizeCode(): Promise<void> {
    try {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            notificationManager.showError('No active editor');
            return;
        }

        const selection = editor.selection;
        const code = selection.isEmpty ? editor.document.getText() : editor.document.getText(selection);

        if (!code.trim()) {
            notificationManager.showError('No code selected for optimization');
            return;
        }

        const result = await agenticalClient.optimizeCode({
            code,
            language: editor.document.languageId,
            optimizationType: 'performance' // Could be made configurable
        });

        if (result.optimizedCode) {
            const action = await vscode.window.showInformationMessage(
                'Code optimization complete. Apply changes?',
                'Apply', 'Show Diff', 'Cancel'
            );

            if (action === 'Apply') {
                await editor.edit(editBuilder => {
                    if (selection.isEmpty) {
                        const fullRange = new vscode.Range(
                            editor.document.positionAt(0),
                            editor.document.positionAt(editor.document.getText().length)
                        );
                        editBuilder.replace(fullRange, result.optimizedCode);
                    } else {
                        editBuilder.replace(selection, result.optimizedCode);
                    }
                });
            } else if (action === 'Show Diff') {
                await webviewManager.showCodeDiff(code, result.optimizedCode, result.explanation);
            }
        }

    } catch (error) {
        notificationManager.showError(`Failed to optimize code: ${error}`);
        loggingManager.error('Code optimization failed', error);
    }
}

/**
 * Generate unit tests
 */
async function generateTests(): Promise<void> {
    try {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            notificationManager.showError('No active editor');
            return;
        }

        const selection = editor.selection;
        const code = selection.isEmpty ? editor.document.getText() : editor.document.getText(selection);

        if (!code.trim()) {
            notificationManager.showError('No code selected for test generation');
            return;
        }

        const result = await agenticalClient.generateTests({
            code,
            language: editor.document.languageId,
            testFramework: await detectTestFramework(editor.document),
            coverage: 'comprehensive'
        });

        if (result.tests) {
            // Create new test file or update existing one
            const testFileName = generateTestFileName(editor.document.fileName);
            const testFileUri = vscode.Uri.file(testFileName);

            await vscode.workspace.fs.writeFile(testFileUri, Buffer.from(result.tests));
            await vscode.window.showTextDocument(testFileUri);

            notificationManager.showInfo('Unit tests generated successfully!');
        }

    } catch (error) {
        notificationManager.showError(`Failed to generate tests: ${error}`);
        loggingManager.error('Test generation failed', error);
    }
}

/**
 * Deploy application with DevOps agent
 */
async function deployApplication(): Promise<void> {
    try {
        if (!agenticalClient.isConnected()) {
            notificationManager.showError('Not connected to Agentical server');
            return;
        }

        const deploymentConfig = await getDeploymentConfiguration();
        if (!deploymentConfig) return;

        const result = await agenticalClient.deployApplication(deploymentConfig);

        notificationManager.showInfo(`Deployment started. Job ID: ${result.jobId}`);
        await webviewManager.showDeploymentProgress(result.jobId);

    } catch (error) {
        notificationManager.showError(`Failed to deploy application: ${error}`);
        loggingManager.error('Deployment failed', error);
    }
}

/**
 * Manage GitHub repository
 */
async function manageRepository(): Promise<void> {
    try {
        if (!agenticalClient.isConnected()) {
            notificationManager.showError('Not connected to Agentical server');
            return;
        }

        const actions = [
            'Create Pull Request',
            'Manage Issues',
            'Repository Analytics',
            'Branch Management',
            'Release Management'
        ];

        const selectedAction = await vscode.window.showQuickPick(actions, {
            placeHolder: 'Select GitHub action'
        });

        if (selectedAction) {
            await webviewManager.showGitHubManager(selectedAction);
        }

    } catch (error) {
        notificationManager.showError(`Failed to manage repository: ${error}`);
        loggingManager.error('Repository management failed', error);
    }
}

/**
 * Research topic with Research agent
 */
async function researchTopic(): Promise<void> {
    try {
        if (!agenticalClient.isConnected()) {
            notificationManager.showError('Not connected to Agentical server');
            return;
        }

        const topic = await vscode.window.showInputBox({
            placeHolder: 'Enter research topic...',
            prompt: 'Research Topic'
        });

        if (!topic) return;

        const result = await agenticalClient.researchTopic({
            topic,
            depth: 'comprehensive',
            sources: ['academic', 'web', 'documentation']
        });

        await webviewManager.showResearchResults(result);

    } catch (error) {
        notificationManager.showError(`Failed to research topic: ${error}`);
        loggingManager.error('Research failed', error);
    }
}

/**
 * UX Analysis
 */
async function uxAnalysis(): Promise<void> {
    try {
        if (!agenticalClient.isConnected()) {
            notificationManager.showError('Not connected to Agentical server');
            return;
        }

        const analysisType = await vscode.window.showQuickPick([
            'Usability Analysis',
            'Accessibility Audit',
            'User Journey Mapping',
            'Interface Review'
        ], {
            placeHolder: 'Select UX analysis type'
        });

        if (analysisType) {
            await webviewManager.showUXAnalysis(analysisType);
        }

    } catch (error) {
        notificationManager.showError(`Failed to perform UX analysis: ${error}`);
        loggingManager.error('UX analysis failed', error);
    }
}

/**
 * Show agent pool
 */
async function showAgentPool(): Promise<void> {
    vscode.commands.executeCommand('agentical-agents.focus');
}

/**
 * Show workflow history
 */
async function showWorkflowHistory(): Promise<void> {
    vscode.commands.executeCommand('agentical-history.focus');
}

/**
 * Show system metrics
 */
async function showSystemMetrics(): Promise<void> {
    vscode.commands.executeCommand('agentical-metrics.focus');
}

/**
 * Open Agentical dashboard
 */
async function openDashboard(): Promise<void> {
    const serverUrl = configManager.getServerUrl();
    const dashboardUrl = `${serverUrl}/dashboard`;

    await vscode.env.openExternal(vscode.Uri.parse(dashboardUrl));
}

// Helper functions

/**
 * Detect framework from document
 */
async function detectFramework(document: vscode.TextDocument): Promise<string> {
    const content = document.getText();
    const language = document.languageId;

    // Simple framework detection logic
    if (language === 'python') {
        if (content.includes('from fastapi') || content.includes('import fastapi')) return 'fastapi';
        if (content.includes('from flask') || content.includes('import flask')) return 'flask';
        if (content.includes('from django') || content.includes('import django')) return 'django';
        return 'python';
    }

    if (language === 'javascript' || language === 'typescript') {
        if (content.includes('import React') || content.includes('from "react"')) return 'react';
        if (content.includes('import Vue') || content.includes('from "vue"')) return 'vue';
        if (content.includes('import { Component }') && content.includes('@angular')) return 'angular';
        if (content.includes('import express') || content.includes('require("express")')) return 'express';
        return language;
    }

    return language;
}

/**
 * Detect test framework
 */
async function detectTestFramework(document: vscode.TextDocument): Promise<string> {
    const language = document.languageId;

    if (language === 'python') return 'pytest';
    if (language === 'javascript' || language === 'typescript') return 'jest';
    if (language === 'java') return 'junit';
    if (language === 'csharp') return 'nunit';

    return 'default';
}

/**
 * Generate test file name
 */
function generateTestFileName(sourceFileName: string): string {
    const path = require('path');
    const ext = path.extname(sourceFileName);
    const base = path.basename(sourceFileName, ext);
    const dir = path.dirname(sourceFileName);

    return path.join(dir, `${base}.test${ext}`);
}

/**
 * Get deployment configuration
 */
async function getDeploymentConfiguration(): Promise<any> {
    const platform = await vscode.window.showQuickPick([
        'AWS',
        'Google Cloud',
        'Azure',
        'Kubernetes',
        'Docker'
    ], {
        placeHolder: 'Select deployment platform'
    });

    if (!platform) return null;

    const environment = await vscode.window.showQuickPick([
        'Development',
        'Staging',
        'Production'
    ], {
        placeHolder: 'Select environment'
    });

    if (!environment) return null;

    return {
        platform: platform.toLowerCase(),
        environment: environment.toLowerCase(),
        source: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath
    };
}
