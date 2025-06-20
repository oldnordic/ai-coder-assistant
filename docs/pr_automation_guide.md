# PR Automation Guide (Updated v2.6.0)

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

---

# PR Automation System Guide

## Overview
The PR Automation system automates pull request creation, integrates with JIRA/ServiceNow, and supports customizable templates and API usage.

## Features
- Add/manage JIRA and ServiceNow services
- Create/manage PR templates with variables
- Automated PR creation with Git integration
- REST API for external automation
- Connection testing and health monitoring

## Usage
1. Open the **PR Management** tab.
2. Use the **Service Configuration** sub-tab to add/test JIRA/ServiceNow services.
3. Use the **Template Management** sub-tab to create/manage templates.
4. Use the **Create PR** sub-tab to create PRs using templates and service integration.

## API Usage
- Start the API server: `python run_api_server.py`
- Use `/api/services`, `/api/templates`, `/api/pr/create` endpoints for automation.

## Troubleshooting
- Ensure the API server is running and service configs are correct.
- Test connections before creating PRs.
- Check logs for errors.

## Integration
- All features are accessible via the BackendController and REST API.
- For CI/CD, use the API endpoints for PR automation.

## Quick Start

### 1. Start the API Server

```bash
# Run the API server
python run_api_server.py

# Or with custom host/port
python run_api_server.py --host 0.0.0.0 --port 8000 --debug
```

### 2. Access the API Documentation

Open your browser and navigate to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. Configure Services

#### Add JIRA Service

```bash
curl -X POST "http://localhost:8000/api/services" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "jira",
    "name": "JIRA-Prod",
    "base_url": "https://company.atlassian.net",
    "username": "your-email@company.com",
    "api_token": "your-api-token",
    "project_key": "PROJ",
    "is_enabled": true
  }'
```

#### Add ServiceNow Service

```bash
curl -X POST "http://localhost:8000/api/services" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "servicenow",
    "name": "ServiceNow-Dev",
    "base_url": "https://company.service-now.com",
    "username": "your-username",
    "api_token": "your-api-token",
    "is_enabled": true
  }'
```

### 4. Create PR Templates

```bash
curl -X POST "http://localhost:8000/api/templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Feature Template",
    "title_template": "feat: {title}",
    "body_template": "## Description\n{description}\n\n## JIRA Ticket\n{jira_ticket}\n\n## ServiceNow Ticket\n{servicenow_ticket}\n\n## Branch\n{branch_name} -> {base_branch}",
    "branch_prefix": "feature/",
    "auto_assign": true,
    "labels": ["feature", "enhancement"],
    "reviewers": ["reviewer1", "reviewer2"],
    "is_default": true
  }'
```

### 5. Create a PR

```bash
curl -X POST "http://localhost:8000/api/pr/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add new authentication feature",
    "description": "Implement OAuth2 authentication for the API",
    "base_branch": "main",
    "template_name": "Feature Template",
    "auto_create_tickets": true,
    "labels": ["security", "api"],
    "reviewers": ["security-team"],
    "repo_path": "/path/to/your/repo"
  }'
```

## GUI Usage

### PR Management Tab

The PR Management tab in the main application provides a user-friendly interface for:

1. **Service Configuration**
   - Add/edit/remove JIRA and ServiceNow services
   - Test service connections
   - View service status

2. **Template Management**
   - Create and edit PR templates
   - Set default templates
   - Preview template variables

3. **PR Creation**
   - Select repository
   - Choose template
   - Configure PR settings
   - Create PR with linked tickets

### Service Configuration Dialog

Configure external services with:
- **Service Type**: JIRA or ServiceNow
- **Service Name**: Unique identifier
- **Base URL**: Service instance URL
- **Username**: API username/email
- **API Token**: Authentication token
- **Project Key**: JIRA project key (JIRA only)
- **Enabled**: Enable/disable service

### PR Template Dialog

Create templates with:
- **Template Name**: Unique template identifier
- **Title Template**: PR title with variables
- **Body Template**: PR description with variables
- **Branch Prefix**: Automatic branch naming
- **Labels**: Default labels to apply
- **Reviewers**: Default reviewers
- **Default Template**: Set as default

## API Reference

### Service Management

#### List Services
```http
GET /api/services
```

#### Add Service
```http
POST /api/services
Content-Type: application/json

{
  "service_type": "jira|servicenow",
  "name": "service-name",
  "base_url": "https://service-url.com",
  "username": "username",
  "api_token": "token",
  "project_key": "PROJ",  // JIRA only
  "is_enabled": true
}
```

#### Remove Service
```http
DELETE /api/services/{service_name}
```

#### Test Service Connection
```http
POST /api/services/{service_name}/test
```

### Template Management

#### List Templates
```http
GET /api/templates
```

#### Add Template
```http
POST /api/templates
Content-Type: application/json

{
  "name": "template-name",
  "title_template": "Title with {variables}",
  "body_template": "Body with {variables}",
  "branch_prefix": "feature/",
  "auto_assign": true,
  "labels": ["label1", "label2"],
  "reviewers": ["reviewer1", "reviewer2"],
  "is_default": false
}
```

#### Remove Template
```http
DELETE /api/templates/{template_name}
```

#### Get Default Template
```http
GET /api/templates/default
```

### PR Creation

#### Create PR
```http
POST /api/pr/create
Content-Type: application/json

{
  "title": "PR Title",
  "description": "PR Description",
  "base_branch": "main",
  "source_branch": "feature/branch",  // Optional
  "template_name": "template-name",   // Optional
  "jira_ticket": "PROJ-123",         // Optional
  "servicenow_ticket": "CHG0001234", // Optional
  "labels": ["label1", "label2"],
  "reviewers": ["reviewer1", "reviewer2"],
  "auto_create_tickets": true,
  "repo_path": "/path/to/repo"
}
```

### Direct Service Integration

#### Create JIRA Issue
```http
POST /api/jira/issues?summary=Issue Summary&description=Issue Description&issue_type=Task&service_name=JIRA-Prod
```

#### Create ServiceNow Change Request
```http
POST /api/servicenow/change-requests?short_description=Change Summary&description=Change Description&service_name=ServiceNow-Dev
```

## Template Variables

### Available Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{title}` | PR title | "Add authentication feature" |
| `{description}` | PR description | "Implement OAuth2..." |
| `{jira_ticket}` | JIRA ticket key | "PROJ-123" |
| `{servicenow_ticket}` | ServiceNow ticket | "CHG0001234" |
| `{branch_name}` | Source branch | "feature/auth-oauth2" |
| `{base_branch}` | Target branch | "main" |

### Template Examples

#### Feature Template
```markdown
## Description
{description}

## JIRA Ticket
{jira_ticket}

## ServiceNow Ticket
{servicenow_ticket}

## Branch
{branch_name} -> {base_branch}

## Type of Change
- [ ] Bug fix
- [x] New feature
- [ ] Breaking change
- [ ] Documentation update
```

#### Bug Fix Template
```markdown
## Bug Description
{description}

## Fix Details
- **Issue**: {jira_ticket}
- **Root Cause**: [Describe root cause]
- **Solution**: [Describe solution]

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Related Tickets
- JIRA: {jira_ticket}
- ServiceNow: {servicenow_ticket}
```

## Configuration Files

### PR Automation Config

The system stores configuration in `config/pr_automation_config.json`:

```json
{
  "services": [
    {
      "service_type": "jira",
      "name": "JIRA-Prod",
      "base_url": "https://company.atlassian.net",
      "username": "user@company.com",
      "api_token": "encrypted-token",
      "project_key": "PROJ",
      "is_enabled": true
    }
  ],
  "templates": [
    {
      "name": "Feature Template",
      "title_template": "feat: {title}",
      "body_template": "## Description\n{description}",
      "branch_prefix": "feature/",
      "auto_assign": true,
      "labels": ["feature"],
      "reviewers": ["reviewer1"],
      "is_default": true
    }
  ]
}
```

## Security Considerations

### API Token Management
- Store API tokens securely
- Use environment variables for sensitive data
- Rotate tokens regularly
- Use least-privilege access

### Service Access
- Limit service access to required projects
- Use service accounts where possible
- Monitor API usage and rate limits
- Implement proper error handling

### Repository Security
- Ensure repository access permissions
- Use SSH keys for Git operations
- Validate repository paths
- Implement branch protection rules

## Troubleshooting

### Common Issues

#### Service Connection Failures
1. **Check API Token**: Verify token is valid and not expired
2. **Verify URL**: Ensure base URL is correct and accessible
3. **Check Permissions**: Verify user has required permissions
4. **Network Issues**: Check firewall and proxy settings

#### PR Creation Failures
1. **GitHub CLI**: Ensure `gh` CLI is installed and authenticated
2. **Repository Access**: Verify repository exists and is accessible
3. **Branch Conflicts**: Check for existing branches with same name
4. **Template Issues**: Verify template variables are valid

#### Template Variable Issues
1. **Variable Names**: Use exact variable names with curly braces
2. **Missing Variables**: Provide fallback values for optional variables
3. **Special Characters**: Escape special characters in templates

### Debug Mode

Enable debug mode for detailed logging:

```bash
python run_api_server.py --debug
```

Check the `api_server.log` file for detailed error information.

### Health Checks

Monitor system health:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.3.0"
}
```

## Best Practices

### Service Configuration
1. **Use Descriptive Names**: Choose clear, descriptive service names
2. **Environment Separation**: Use different services for dev/staging/prod
3. **Regular Testing**: Test service connections regularly
4. **Documentation**: Document service configurations

### Template Design
1. **Consistent Structure**: Use consistent template structure
2. **Clear Variables**: Use descriptive variable names
3. **Validation**: Include validation checklists
4. **Documentation**: Document template usage

### PR Creation
1. **Meaningful Titles**: Use clear, descriptive PR titles
2. **Detailed Descriptions**: Provide comprehensive descriptions
3. **Proper Labels**: Apply relevant labels for categorization
4. **Reviewer Assignment**: Assign appropriate reviewers

### API Usage
1. **Rate Limiting**: Respect API rate limits
2. **Error Handling**: Implement proper error handling
3. **Authentication**: Use secure authentication methods
4. **Monitoring**: Monitor API usage and performance

## Integration Examples

### CI/CD Integration

#### GitHub Actions
```yaml
name: Create PR
on:
  push:
    branches: [feature/*]

jobs:
  create-pr:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Create PR
        run: |
          curl -X POST "http://localhost:8000/api/pr/create" \
            -H "Content-Type: application/json" \
            -d '{
              "title": "Auto-generated PR",
              "description": "Automated PR from CI/CD",
              "repo_path": "${{ github.workspace }}",
              "template_name": "CI Template"
            }'
```

#### Jenkins Pipeline
```groovy
pipeline {
    agent any
    stages {
        stage('Create PR') {
            steps {
                script {
                    def response = httpRequest(
                        url: 'http://localhost:8000/api/pr/create',
                        contentType: 'APPLICATION_JSON',
                        httpMode: 'POST',
                        requestBody: '{"title": "Jenkins PR", "description": "Auto PR", "repo_path": "${WORKSPACE}"}'
                    )
                    echo "PR created: ${response.content}"
                }
            }
        }
    }
}
```

### IDE Integration

#### VS Code Extension
```typescript
// Create PR command
vscode.commands.registerCommand('pr-automation.createPR', async () => {
    const title = await vscode.window.showInputBox({ prompt: 'PR Title' });
    const description = await vscode.window.showInputBox({ prompt: 'PR Description' });
    
    const response = await fetch('http://localhost:8000/api/pr/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            title,
            description,
            repo_path: vscode.workspace.rootPath
        })
    });
    
    const result = await response.json();
    vscode.window.showInformationMessage(`PR created: ${result.pr_url}`);
});
```

## Support and Contributing

### Getting Help
1. **Documentation**: Check this guide and API documentation
2. **Logs**: Review application logs for error details
3. **Issues**: Report issues on the project repository
4. **Community**: Join the community discussions

### Contributing
1. **Code Style**: Follow the project's coding standards
2. **Testing**: Add tests for new features
3. **Documentation**: Update documentation for changes
4. **Review Process**: Submit pull requests for review

### License
This project is licensed under the GNU General Public License v3.0. See the LICENSE file for details. 