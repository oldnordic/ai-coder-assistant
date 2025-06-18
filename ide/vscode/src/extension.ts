import * as vscode from 'vscode';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export function activate(context: vscode.ExtensionContext) {
    console.log('AI Coder Assistant extension is now active!');

    let scanFile = vscode.commands.registerCommand('ai-coder-assistant.scanFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const document = editor.document;
        const filePath = document.fileName;
        const language = getLanguageFromExtension(document.languageId);

        try {
            vscode.window.showInformationMessage('Scanning current file...');
            
            const config = vscode.workspace.getConfiguration('ai-coder-assistant');
            const pythonPath = config.get<string>('pythonPath', 'python');
            const projectPath = config.get<string>('projectPath', '');

            if (!projectPath) {
                vscode.window.showErrorMessage('Please set ai-coder-assistant.projectPath in settings');
                return;
            }

            const command = `${pythonPath} -m src.cli.main analyze --file "${filePath}" --language ${language}`;
            const { stdout, stderr } = await execAsync(command, { cwd: projectPath });

            if (stderr) {
                console.error('Error:', stderr);
            }

            // Display results in a new document
            const resultsDoc = await vscode.workspace.openTextDocument({
                content: stdout || 'No issues found',
                language: 'markdown'
            });
            await vscode.window.showTextDocument(resultsDoc);

        } catch (error) {
            vscode.window.showErrorMessage(`Scan failed: ${error}`);
        }
    });

    let scanWorkspace = vscode.commands.registerCommand('ai-coder-assistant.scanWorkspace', async () => {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder');
            return;
        }

        try {
            vscode.window.showInformationMessage('Scanning workspace...');
            
            const config = vscode.workspace.getConfiguration('ai-coder-assistant');
            const pythonPath = config.get<string>('pythonPath', 'python');
            const projectPath = config.get<string>('projectPath', '');

            if (!projectPath) {
                vscode.window.showErrorMessage('Please set ai-coder-assistant.projectPath in settings');
                return;
            }

            const command = `${pythonPath} -m src.cli.main scan "${workspaceFolder.uri.fsPath}" --output /tmp/scan_results.json --format json`;
            const { stdout, stderr } = await execAsync(command, { cwd: projectPath });

            if (stderr) {
                console.error('Error:', stderr);
            }

            // Read and display results
            const fs = require('fs');
            if (fs.existsSync('/tmp/scan_results.json')) {
                const results = JSON.parse(fs.readFileSync('/tmp/scan_results.json', 'utf8'));
                const resultsText = formatResults(results);
                
                const resultsDoc = await vscode.workspace.openTextDocument({
                    content: resultsText,
                    language: 'markdown'
                });
                await vscode.window.showTextDocument(resultsDoc);
            }

        } catch (error) {
            vscode.window.showErrorMessage(`Scan failed: ${error}`);
        }
    });

    let securityScan = vscode.commands.registerCommand('ai-coder-assistant.securityScan', async () => {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder');
            return;
        }

        try {
            vscode.window.showInformationMessage('Running security scan...');
            
            const config = vscode.workspace.getConfiguration('ai-coder-assistant');
            const pythonPath = config.get<string>('pythonPath', 'python');
            const projectPath = config.get<string>('projectPath', '');

            if (!projectPath) {
                vscode.window.showErrorMessage('Please set ai-coder-assistant.projectPath in settings');
                return;
            }

            const command = `${pythonPath} -m src.cli.main security-scan "${workspaceFolder.uri.fsPath}" --output /tmp/security_results.json --format json`;
            const { stdout, stderr } = await execAsync(command, { cwd: projectPath });

            if (stderr) {
                console.error('Error:', stderr);
            }

            // Read and display security results
            const fs = require('fs');
            if (fs.existsSync('/tmp/security_results.json')) {
                const results = JSON.parse(fs.readFileSync('/tmp/security_results.json', 'utf8'));
                const resultsText = formatSecurityResults(results);
                
                const resultsDoc = await vscode.workspace.openTextDocument({
                    content: resultsText,
                    language: 'markdown'
                });
                await vscode.window.showTextDocument(resultsDoc);
            }

        } catch (error) {
            vscode.window.showErrorMessage(`Security scan failed: ${error}`);
        }
    });

    // Register PR creation commands
    let createPRDisposable = vscode.commands.registerCommand('ai-coder.createPR', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        const workspaceFolder = workspaceFolders[0];
        
        // Show PR creation options
        const prType = await vscode.window.showQuickPick([
            { label: '🔒 Security Fix', value: 'security_fix' },
            { label: '🔧 Code Quality', value: 'code_quality' },
            { label: '⚡ Performance', value: 'performance' },
            { label: '📋 Compliance', value: 'compliance' },
            { label: '🔄 Refactoring', value: 'refactoring' },
            { label: '🐛 Bug Fix', value: 'bug_fix' }
        ], {
            placeHolder: 'Select PR type'
        });

        if (!prType) return;

        const priorityStrategy = await vscode.window.showQuickPick([
            { label: '🔴 Severity First', value: 'severity_first' },
            { label: '🎯 Easy Win First', value: 'easy_win_first' },
            { label: '⚖️ Balanced', value: 'balanced' },
            { label: '💼 Impact First', value: 'impact_first' }
        ], {
            placeHolder: 'Select priority strategy'
        });

        if (!priorityStrategy) return;

        // Get scan result files
        const scanFiles = await vscode.window.showOpenDialog({
            canSelectFiles: true,
            canSelectFolders: false,
            canSelectMany: true,
            filters: {
                'Scan Results': ['json']
            },
            title: 'Select scan result files'
        });

        if (!scanFiles || scanFiles.length === 0) return;

        const scanFilePaths = scanFiles.map(file => file.fsPath);

        // Create PR
        try {
            const progressOptions = {
                location: vscode.ProgressLocation.Notification,
                title: 'Creating AI-powered PR...',
                cancellable: false
            };

            await vscode.window.withProgress(progressOptions, async (progress) => {
                progress.report({ message: 'Analyzing scan results...' });

                // Call AI Coder Assistant CLI
                const command = 'python';
                const args = [
                    '-m', 'src.cli.main',
                    'create-pr',
                    ...scanFilePaths,
                    '--repo-path', workspaceFolder.uri.fsPath,
                    '--pr-type', prType.value,
                    '--priority-strategy', priorityStrategy.value,
                    '--auto-commit',
                    '--create-pr'
                ];

                const result = await executeCommand(command, args, workspaceFolder.uri.fsPath);

                if (result.success) {
                    vscode.window.showInformationMessage(
                        `✅ PR created successfully!\nBranch: ${result.branchName}\nTitle: ${result.title}`
                    );

                    // Show PR details
                    if (result.prUrl) {
                        const openPR = await vscode.window.showInformationMessage(
                            `PR created: ${result.title}`,
                            'Open PR',
                            'Copy URL'
                        );

                        if (openPR === 'Open PR') {
                            vscode.env.openExternal(vscode.Uri.parse(result.prUrl));
                        } else if (openPR === 'Copy URL') {
                            vscode.env.clipboard.writeText(result.prUrl);
                        }
                    }
                } else {
                    vscode.window.showErrorMessage(`Failed to create PR: ${result.error}`);
                }
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Error creating PR: ${error}`);
        }
    });

    let createPRFromCurrentScanDisposable = vscode.commands.registerCommand('ai-coder.createPRFromCurrentScan', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        const workspaceFolder = workspaceFolders[0];
        
        // First run a scan
        try {
            const progressOptions = {
                location: vscode.ProgressLocation.Notification,
                title: 'Scanning code for issues...',
                cancellable: false
            };

            await vscode.window.withProgress(progressOptions, async (progress) => {
                progress.report({ message: 'Running code analysis...' });

                // Run scan
                const scanCommand = 'python';
                const scanArgs = [
                    '-m', 'src.cli.main',
                    'scan',
                    workspaceFolder.uri.fsPath,
                    '--output', 'json',
                    '--output-file', 'temp_scan_result.json'
                ];

                const scanResult = await executeCommand(scanCommand, scanArgs, workspaceFolder.uri.fsPath);

                if (!scanResult.success) {
                    throw new Error(`Scan failed: ${scanResult.error}`);
                }

                progress.report({ message: 'Creating PR from scan results...' });

                // Create PR from scan results
                const prCommand = 'python';
                const prArgs = [
                    '-m', 'src.cli.main',
                    'create-pr',
                    'temp_scan_result.json',
                    '--repo-path', workspaceFolder.uri.fsPath,
                    '--auto-commit',
                    '--create-pr'
                ];

                const prResult = await executeCommand(prCommand, prArgs, workspaceFolder.uri.fsPath);

                if (prResult.success) {
                    vscode.window.showInformationMessage(
                        `✅ PR created from scan results!\nBranch: ${prResult.branchName}\nTitle: ${prResult.title}`
                    );

                    // Show PR details
                    if (prResult.prUrl) {
                        const openPR = await vscode.window.showInformationMessage(
                            `PR created: ${prResult.title}`,
                            'Open PR',
                            'Copy URL'
                        );

                        if (openPR === 'Open PR') {
                            vscode.env.openExternal(vscode.Uri.parse(prResult.prUrl));
                        } else if (openPR === 'Copy URL') {
                            vscode.env.clipboard.writeText(prResult.prUrl);
                        }
                    }
                } else {
                    vscode.window.showErrorMessage(`Failed to create PR: ${prResult.error}`);
                }

                // Clean up temporary file
                try {
                    const fs = require('fs');
                    if (fs.existsSync('temp_scan_result.json')) {
                        fs.unlinkSync('temp_scan_result.json');
                    }
                } catch (cleanupError) {
                    // Ignore cleanup errors
                }
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Error creating PR from scan: ${error}`);
        }
    });

    let showPRTemplatesDisposable = vscode.commands.registerCommand('ai-coder.showPRTemplates', async () => {
        const templates = [
            {
                name: '🔒 Security Fix',
                description: 'Fix security vulnerabilities',
                template: `## 🔒 Security Vulnerability Fixes

### 📊 Summary
- **Critical Issues**: {critical_count}
- **High Priority Issues**: {high_count}
- **Total Issues**: {issue_count}

### 🎯 Issues Addressed
{issues_list}

### 🔍 Security Improvements
- **Input Validation**: Enhanced input sanitization
- **Authentication**: Improved authentication mechanisms
- **Authorization**: Strengthened access control
- **Data Protection**: Enhanced sensitive data handling

### 🧪 Testing
- [ ] Security tests have been added/updated
- [ ] Penetration testing completed
- [ ] Vulnerability scanning passed
- [ ] Code review by security team`
            },
            {
                name: '🔧 Code Quality',
                description: 'Improve code quality',
                template: `## 🔧 Code Quality Improvements

### 📊 Summary
- **Total Issues**: {issue_count}
- **Code Smells**: {code_smells_count}
- **Maintainability**: {maintainability_count}

### 🎯 Improvements Made
{issues_list}

### 🔍 Quality Enhancements
- **Code Readability**: Improved code clarity
- **Maintainability**: Enhanced code maintainability
- **Best Practices**: Applied coding best practices
- **Documentation**: Updated code documentation`
            },
            {
                name: '⚡ Performance',
                description: 'Performance optimizations',
                template: `## ⚡ Performance Optimizations

### 📊 Summary
- **Performance Issues**: {performance_count}
- **Memory Issues**: {memory_count}
- **Total Issues**: {issue_count}

### 🎯 Optimizations Made
{issues_list}

### 🔍 Performance Improvements
- **Execution Speed**: Improved algorithm efficiency
- **Memory Usage**: Optimized memory allocation
- **Database Queries**: Enhanced query performance
- **Resource Usage**: Reduced resource consumption`
            }
        ];

        const selectedTemplate = await vscode.window.showQuickPick(
            templates.map(t => ({ label: t.name, description: t.description, template: t.template })),
            {
                placeHolder: 'Select a PR template to view'
            }
        );

        if (selectedTemplate) {
            // Create a new document with the template
            const document = await vscode.workspace.openTextDocument({
                content: selectedTemplate.template,
                language: 'markdown'
            });

            await vscode.window.showTextDocument(document);
        }
    });

    context.subscriptions.push(scanFile, scanWorkspace, securityScan, createPRDisposable, createPRFromCurrentScanDisposable, showPRTemplatesDisposable);
}

function getLanguageFromExtension(languageId: string): string {
    const languageMap: { [key: string]: string } = {
        'python': 'python',
        'javascript': 'javascript',
        'typescript': 'typescript',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'csharp': 'csharp',
        'go': 'go',
        'rust': 'rust',
        'php': 'php',
        'ruby': 'ruby',
        'swift': 'swift',
        'kotlin': 'kotlin',
        'scala': 'scala',
        'dart': 'dart',
        'r': 'r',
        'matlab': 'matlab',
        'shellscript': 'shell',
        'sql': 'sql',
        'html': 'html'
    };
    return languageMap[languageId] || 'unknown';
}

function formatResults(results: any[]): string {
    if (!results || results.length === 0) {
        return '# AI Coder Assistant - Scan Results\n\n✅ No issues found!';
    }

    let output = `# AI Coder Assistant - Scan Results\n\nFound ${results.length} issues\n\n`;
    
    const severityGroups = {
        'critical': [] as any[],
        'high': [] as any[],
        'medium': [] as any[],
        'low': [] as any[]
    };

    results.forEach(result => {
        const severity = result.severity || 'medium';
        severityGroups[severity as keyof typeof severityGroups].push(result);
    });

    ['critical', 'high', 'medium', 'low'].forEach(severity => {
        const group = severityGroups[severity as keyof typeof severityGroups];
        if (group.length > 0) {
            output += `## ${severity.toUpperCase()} (${group.length})\n\n`;
            group.forEach(result => {
                output += `### ${result.file_path}:${result.line_number}\n\n`;
                output += `**Type:** ${result.issue_type}\n\n`;
                output += `**Description:** ${result.description}\n\n`;
                output += `**Suggestion:** ${result.suggestion}\n\n`;
                output += `\`\`\`\n${result.code_snippet}\n\`\`\`\n\n---\n\n`;
            });
        }
    });

    return output;
}

function formatSecurityResults(results: any[]): string {
    if (!results || results.length === 0) {
        return '# AI Coder Assistant - Security Scan Results\n\n✅ No security issues found!';
    }

    let output = `# AI Coder Assistant - Security Scan Results\n\n🔒 Found ${results.length} security issues\n\n`;
    
    const criticalCount = results.filter(r => r.severity === 'critical').length;
    const highCount = results.filter(r => r.severity === 'high').length;

    output += `**Critical:** ${criticalCount}\n`;
    output += `**High:** ${highCount}\n\n`;

    if (criticalCount > 0) {
        output += `## 🚨 CRITICAL SECURITY ISSUES\n\n`;
        results.filter(r => r.severity === 'critical').forEach(result => {
            output += `### ${result.file_path}:${result.line_number}\n\n`;
            output += `**Description:** ${result.description}\n\n`;
            output += `**Suggestion:** ${result.suggestion}\n\n`;
            output += `\`\`\`\n${result.code_snippet}\n\`\`\`\n\n---\n\n`;
        });
    }

    return output;
}

export function deactivate() {} 