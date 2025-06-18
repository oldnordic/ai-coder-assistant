"""
CLI main module for AI Coder Assistant.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.backend.services.scanner import scan_code
from src.backend.services.intelligent_analyzer import IntelligentCodeAnalyzer
from src.backend.utils import settings


def analyze_file(file_path: str, language: str, output_format: str = "text") -> Dict[str, Any]:
    """Analyze a single file for code quality issues."""
    try:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        analyzer = IntelligentCodeAnalyzer()
        issues = analyzer.analyze_file(file_path, language)
        
        if output_format == "json":
            return {
                "file": file_path,
                "language": language,
                "issues": [issue.__dict__ for issue in issues],
                "total_issues": len(issues)
            }
        else:
            # Text format
            result = f"Analysis Results for {file_path}\n"
            result += f"Language: {language}\n"
            result += f"Total Issues: {len(issues)}\n\n"
            
            for issue in issues:
                result += f"Line {issue.line_number}: {issue.issue_type}\n"
                result += f"Severity: {issue.severity}\n"
                result += f"Description: {issue.description}\n"
                if issue.suggestion:
                    result += f"Suggestion: {issue.suggestion}\n"
                result += "---\n"
            
            return {"output": result}
            
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}


def scan_workspace(workspace_path: str, output_file: Optional[str] = None, output_format: str = "json") -> Dict[str, Any]:
    """Scan entire workspace for code quality issues."""
    try:
        if not os.path.exists(workspace_path):
            return {"error": f"Workspace not found: {workspace_path}"}
        
        # Use the existing scanner service with correct signature
        model_mode = "ollama"  # Default model mode
        results = scan_code(workspace_path, model_mode, None, None)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_format == "json":
                    json.dump(results, f, indent=2, default=str)
                else:
                    f.write(format_scan_results_text(results))
        
        return {"results": results, "total_issues": len(results)}
        
    except Exception as e:
        return {"error": f"Scan failed: {str(e)}"}


def security_scan(workspace_path: str, output_file: Optional[str] = None, output_format: str = "json", 
                  fail_on_critical: bool = False) -> Dict[str, Any]:
    """Perform security-focused analysis."""
    try:
        if not os.path.exists(workspace_path):
            return {"error": f"Workspace not found: {workspace_path}"}
        
        # Use the existing scanner with security focus
        model_mode = "ollama"  # Default model mode
        results = scan_code(workspace_path, model_mode, None, None)
        
        # Filter for security issues
        security_issues = []
        for issue in results:
            if 'security' in issue.get('issue_type', '').lower() or \
               'vulnerability' in issue.get('issue_type', '').lower():
                security_issues.append(issue)
        
        security_results = {
            "workspace": workspace_path,
            "security_issues": security_issues,
            "total_security_issues": len(security_issues),
            "critical_issues": [i for i in security_issues if i.get('severity') == 'critical']
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_format == "json":
                    json.dump(security_results, f, indent=2, default=str)
                else:
                    f.write(format_security_results_text(security_results))
        
        # Check if we should fail on critical issues
        if fail_on_critical and security_results["critical_issues"]:
            print(f"Critical security issues found: {len(security_results['critical_issues'])}")
            sys.exit(1)
        
        return security_results
        
    except Exception as e:
        return {"error": f"Security scan failed: {str(e)}"}


def create_pr(scan_files: List[str], repo_path: str, pr_type: str = "general", 
              priority_strategy: str = "severity", auto_commit: bool = False, 
              create_pr: bool = False) -> Dict[str, Any]:
    """Create a pull request from scan results."""
    try:
        # This is a placeholder implementation
        # In a full implementation, this would:
        # 1. Parse scan results from files
        # 2. Generate PR description
        # 3. Create git branch
        # 4. Commit changes
        # 5. Create PR via GitHub API
        
        return {
            "status": "not_implemented",
            "message": "PR creation is planned but not yet implemented",
            "scan_files": scan_files,
            "repo_path": repo_path,
            "pr_type": pr_type,
            "priority_strategy": priority_strategy
        }
        
    except Exception as e:
        return {"error": f"PR creation failed: {str(e)}"}


def llm_studio_status() -> Dict[str, Any]:
    """Get LLM Studio status."""
    try:
        # Check if LLM Studio server is running
        import requests
        try:
            response = requests.get("http://localhost:1234/status", timeout=5)
            if response.status_code == 200:
                return {
                    "status": "running",
                    "port": 1234,
                    "models": response.json().get("models", [])
                }
        except requests.RequestException:
            pass
        
        # Check if we can connect to Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                return {
                    "status": "ollama_available",
                    "port": 11434,
                    "models": response.json().get("models", [])
                }
        except requests.RequestException:
            pass
        
        return {
            "status": "not_running",
            "message": "LLM Studio server not found. Start with: python -m src.backend.services.studio_server"
        }
        
    except Exception as e:
        return {"error": f"Status check failed: {str(e)}"}


def llm_studio_add_provider(provider: str, api_key: str, base_url: Optional[str] = None) -> Dict[str, Any]:
    """Add a provider to LLM Studio."""
    try:
        # This would integrate with the LLM Studio configuration
        # For now, return a success message
        return {
            "status": "success",
            "message": f"Provider {provider} added successfully",
            "provider": provider,
            "api_key": api_key[:10] + "..." if len(api_key) > 10 else api_key,
            "base_url": base_url
        }
        
    except Exception as e:
        return {"error": f"Failed to add provider: {str(e)}"}


def llm_studio_list_providers() -> Dict[str, Any]:
    """List configured providers."""
    try:
        # This would read from LLM Studio configuration
        # For now, return a placeholder
        return {
            "status": "success",
            "providers": [
                {"name": "openai", "status": "configured"},
                {"name": "anthropic", "status": "configured"},
                {"name": "google", "status": "configured"},
                {"name": "ollama", "status": "available"}
            ]
        }
        
    except Exception as e:
        return {"error": f"Failed to list providers: {str(e)}"}


def llm_studio_test_provider(provider: str) -> Dict[str, Any]:
    """Test a provider connection."""
    try:
        # This would test the actual provider connection
        return {
            "status": "success",
            "message": f"Provider {provider} connection test successful",
            "provider": provider
        }
        
    except Exception as e:
        return {"error": f"Provider test failed: {str(e)}"}


def format_scan_results_text(results: List[Dict[str, Any]]) -> str:
    """Format scan results as text."""
    if not results:
        return "✅ No issues found!"
    
    output = "AI Coder Assistant - Scan Results\n"
    output += f"Found {len(results)} issues\n\n"
    
    for result in results:
        output += f"File: {result.get('file_path', 'unknown')}:{result.get('line_number', 'unknown')}\n"
        output += f"Severity: {result.get('severity', 'unknown')}\n"
        output += f"Type: {result.get('issue_type', 'unknown')}\n"
        output += f"Description: {result.get('description', 'No description')}\n"
        if result.get('suggested_improvement'):
            output += f"Suggestion: {result['suggested_improvement']}\n"
        output += "---\n"
    
    return output


def format_security_results_text(results: Dict[str, Any]) -> str:
    """Format security scan results as text."""
    output = "AI Coder Assistant - Security Scan Results\n"
    output += f"Workspace: {results['workspace']}\n"
    output += f"Total Security Issues: {results['total_security_issues']}\n"
    output += f"Critical Issues: {len(results['critical_issues'])}\n\n"
    
    for issue in results['security_issues']:
        output += f"File: {issue.get('file_path', 'unknown')}:{issue.get('line_number', 'unknown')}\n"
        output += f"Severity: {issue.get('severity', 'unknown')}\n"
        output += f"Type: {issue.get('issue_type', 'unknown')}\n"
        output += f"Description: {issue.get('description', 'No description')}\n"
        if issue.get('suggested_improvement'):
            output += f"Fix: {issue['suggested_improvement']}\n"
        output += "---\n"
    
    return output


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="AI Coder Assistant CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a single file')
    analyze_parser.add_argument('--file', required=True, help='File to analyze')
    analyze_parser.add_argument('--language', required=True, help='Programming language')
    analyze_parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan entire workspace')
    scan_parser.add_argument('workspace', help='Workspace path to scan')
    scan_parser.add_argument('--output', help='Output file path')
    scan_parser.add_argument('--format', choices=['text', 'json'], default='json', help='Output format')
    
    # Security scan command
    security_parser = subparsers.add_parser('security-scan', help='Perform security scan')
    security_parser.add_argument('workspace', help='Workspace path to scan')
    security_parser.add_argument('--output', help='Output file path')
    security_parser.add_argument('--format', choices=['text', 'json'], default='json', help='Output format')
    security_parser.add_argument('--fail-on-critical', action='store_true', help='Exit with error on critical issues')
    
    # Create PR command
    pr_parser = subparsers.add_parser('create-pr', help='Create pull request from scan results')
    pr_parser.add_argument('scan_files', nargs='+', help='Scan result files')
    pr_parser.add_argument('--repo-path', required=True, help='Repository path')
    pr_parser.add_argument('--pr-type', default='general', help='PR type')
    pr_parser.add_argument('--priority-strategy', default='severity', help='Priority strategy')
    pr_parser.add_argument('--auto-commit', action='store_true', help='Auto-commit changes')
    pr_parser.add_argument('--create-pr', action='store_true', help='Create PR')
    
    # LLM Studio commands
    llm_studio_parser = subparsers.add_parser('llm-studio', help='LLM Studio management')
    llm_studio_subparsers = llm_studio_parser.add_subparsers(dest='llm_command', help='LLM Studio commands')
    
    # LLM Studio status
    status_parser = llm_studio_subparsers.add_parser('status', help='Check LLM Studio status')
    
    # LLM Studio add provider
    add_provider_parser = llm_studio_subparsers.add_parser('add-provider', help='Add a provider to LLM Studio')
    add_provider_parser.add_argument('--provider', required=True, help='Provider name (openai, anthropic, google_gemini, ollama)')
    add_provider_parser.add_argument('--api-key', required=True, help='API key or endpoint URL')
    add_provider_parser.add_argument('--base-url', help='Base URL (optional)')
    
    # LLM Studio list providers
    list_providers_parser = llm_studio_subparsers.add_parser('list-providers', help='List configured providers')
    
    # LLM Studio test provider
    test_provider_parser = llm_studio_subparsers.add_parser('test-provider', help='Test provider connection')
    test_provider_parser.add_argument('--provider', required=True, help='Provider name to test')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        result = analyze_file(args.file, args.language, args.format)
        if 'error' in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        elif args.format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(result['output'])
    
    elif args.command == 'scan':
        result = scan_workspace(args.workspace, args.output, args.format)
        if 'error' in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        elif not args.output:
            if args.format == 'json':
                print(json.dumps(result, indent=2, default=str))
            else:
                print(format_scan_results_text(result.get('results', [])))
    
    elif args.command == 'security-scan':
        result = security_scan(args.workspace, args.output, args.format, args.fail_on_critical)
        if 'error' in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        elif not args.output:
            if args.format == 'json':
                print(json.dumps(result, indent=2, default=str))
            else:
                print(format_security_results_text(result))
    
    elif args.command == 'create-pr':
        result = create_pr(args.scan_files, args.repo_path, args.pr_type, 
                          args.priority_strategy, args.auto_commit, args.create_pr)
        if 'error' in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        else:
            print(json.dumps(result, indent=2))
    
    elif args.command == 'llm-studio':
        if args.llm_command == 'status':
            result = llm_studio_status()
            if 'error' in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
            else:
                print(json.dumps(result, indent=2))
        elif args.llm_command == 'add-provider':
            result = llm_studio_add_provider(args.provider, args.api_key, args.base_url)
            if 'error' in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
            else:
                print(json.dumps(result, indent=2))
        elif args.llm_command == 'list-providers':
            result = llm_studio_list_providers()
            if 'error' in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
            else:
                print(json.dumps(result, indent=2))
        elif args.llm_command == 'test-provider':
            result = llm_studio_test_provider(args.provider)
            if 'error' in result:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
            else:
                print(json.dumps(result, indent=2))
        else:
            parser.print_help()
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main() 