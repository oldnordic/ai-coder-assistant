# Setup and Configuration Guide v2.6.0

This comprehensive guide covers the setup and configuration of all AI Coder Assistant features, including the latest security intelligence, code standards enforcement, PR automation, and performance optimization capabilities.

## Table of Contents

1. [Basic Installation](#basic-installation)
2. [LLM Provider Configuration](#llm-provider-configuration)
3. [Security Intelligence Setup](#security-intelligence-setup)
4. [Code Standards Configuration](#code-standards-configuration)
5. [PR Automation Setup](#pr-automation-setup)
6. [Ollama Remote Management](#ollama-remote-management)
7. [Performance Optimization](#performance-optimization)
8. [Web Server Mode](#web-server-mode)
9. [Collaboration Features](#collaboration-features)
10. [Advanced Analytics](#advanced-analytics)
11. [Configuration Files](#configuration-files)
12. [Troubleshooting](#troubleshooting)

## Basic Installation

### Prerequisites
- Python 3.8 or higher
- Git
- pip (Python package manager)

### Step 1: Clone the Repository
```bash
git clone https://github.com/oldnordic/ai-coder-assistant.git
cd ai-coder-assistant
```

### Step 2: Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python main.py
```

## LLM Provider Configuration

### OpenAI Configuration
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### Anthropic Configuration
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Google AI Configuration
```bash
export GOOGLE_API_KEY="your-google-api-key"
```

### Configuration via GUI
1. Open the **Cloud Models** tab
2. Click **Add Provider**
3. Select provider type (OpenAI, Anthropic, Google)
4. Enter API key and configuration
5. Test connection
6. Save configuration

## Security Intelligence Setup

### Default Configuration
The security intelligence system comes with pre-configured feeds:

- **NVD CVE Feed**: National Vulnerability Database
- **SecurityWeek**: Security news and breach reports
- **The Hacker News**: Security updates and vulnerabilities
- **CISA Alerts**: Government security advisories

### Adding Custom Security Feeds

#### Via GUI
1. Open the **Security Intelligence** tab
2. Go to the **Security Feeds** sub-tab
3. Click **Add Feed**
4. Enter feed details:
   - **Name**: Descriptive name for the feed
   - **URL**: RSS/Atom feed URL
   - **Feed Type**: RSS, Atom, or API
   - **Tags**: Relevant tags (cve, breach, security-news, etc.)
   - **Enabled**: Check to enable the feed

#### Via Configuration File
Edit `security_intelligence_config.json`:
```json
{
  "feeds": [
    {
      "name": "Custom Security Feed",
      "url": "https://example.com/security-feed.xml",
      "feed_type": "rss",
      "enabled": true,
      "fetch_interval": 3600,
      "tags": ["cve", "security-news"]
    }
  ]
}
```

### Monitoring Security Data
1. **Vulnerabilities Tab**: View CVE data with severity filtering
2. **Breaches Tab**: Monitor security breaches and incidents
3. **Patches Tab**: Track security patches and updates
4. **Training Data Tab**: Export security data for AI training

### Fetching Security Feeds
- Click **Fetch Feeds** button to manually update
- Feeds are automatically refreshed every 5 minutes
- Use **Refresh** button to update all data

## Code Standards Configuration

### Creating Company Standards

#### Via GUI
1. Open the **Code Standards** tab
2. Go to the **Standards** sub-tab
3. Click **Add Standard**
4. Configure standard details:
   - **Name**: Company standard name
   - **Description**: Standard description
   - **Company**: Company name
   - **Version**: Standard version
   - **Languages**: Supported programming languages
   - **Rules**: Code quality rules

#### Example Standard Configuration
```json
{
  "name": "Company Python Standard",
  "description": "Python coding standards for our company",
  "company": "Your Company",
  "version": "1.0.0",
  "languages": ["python"],
  "rules": [
    {
      "id": "naming_convention",
      "name": "Function Naming Convention",
      "description": "Functions should use snake_case",
      "language": "python",
      "severity": "warning",
      "pattern": "^[a-z_][a-z0-9_]*$",
      "message": "Function names should use snake_case",
      "category": "naming",
      "enabled": true,
      "auto_fix": false
    }
  ]
}
```

### Analyzing Code
1. **File Analysis**: Select individual files for analysis
2. **Directory Analysis**: Analyze entire directories
3. **Auto-fix**: Automatically fix common violations
4. **Export Results**: Export analysis reports

### Supported Languages
- Python
- JavaScript
- TypeScript
- Java
- C++
- C#
- Go
- Rust
- PHP
- Ruby

## PR Automation Setup

### Starting the API Server
```bash
python run_api_server.py
```

### Configuring JIRA Integration

#### Via API
```bash
curl -X POST "http://localhost:8000/api/services" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "jira",
    "name": "JIRA-Prod",
    "base_url": "https://company.atlassian.net",
    "username": "your-email@company.com",
    "api_token": "your-api-token",
    "project_key": "PROJ"
  }'
```

#### Via GUI
1. Open the **PR Management** tab
2. Go to **Service Configuration**
3. Click **Add JIRA Service**
4. Enter service details and test connection

### Configuring ServiceNow Integration

#### Via API
```bash
curl -X POST "http://localhost:8000/api/services" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "servicenow",
    "name": "ServiceNow-Prod",
    "base_url": "https://company.service-now.com",
    "username": "your-username",
    "password": "your-password",
    "table": "change_request"
  }'
```

### Creating PR Templates

#### Via API
```bash
curl -X POST "http://localhost:8000/api/templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Feature Template",
    "title_template": "feat: {title}",
    "body_template": "## Description\n{description}\n\n## JIRA Ticket\n{jira_ticket}",
    "branch_prefix": "feature/",
    "is_default": true
  }'
```

#### Via GUI
1. Open the **PR Management** tab
2. Go to **Template Management**
3. Click **Add Template**
4. Configure template variables and content

### Creating Pull Requests

#### Via API
```bash
curl -X POST "http://localhost:8000/api/pr/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add authentication feature",
    "description": "Implement OAuth2 authentication",
    "repo_path": "/path/to/repo",
    "auto_create_tickets": true
  }'
```

#### Via GUI
1. Open the **PR Management** tab
2. Go to **Create PR**
3. Fill in PR details
4. Select repository and template
5. Click **Create PR**

## Ollama Remote Management

### Adding Remote Ollama Instances

#### Via GUI
1. Open the **Ollama Manager** tab
2. Click **Add Instance**
3. Configure instance details:
   - **Instance Name**: Descriptive name
   - **Base URL**: Ollama server URL
   - **Authentication**: Bearer token (if required)
   - **Custom Headers**: Additional headers
   - **SSL Verification**: Enable/disable SSL verification

#### Example Configuration
```json
{
  "instance_name": "Remote Ollama",
  "base_url": "https://ollama.company.com",
  "auth_token": "your-bearer-token",
  "custom_headers": {
    "X-Custom-Header": "value"
  },
  "verify_ssl": true
}
```

### Health Monitoring
- **Health Check**: Test instance connectivity
- **Model Listing**: View available models
- **Test Chat**: Test model functionality
- **Status Monitoring**: Real-time status updates

### Managing Multiple Instances
- Add multiple remote instances
- Switch between instances
- Monitor all instances simultaneously
- Configure instance-specific settings

## Performance Optimization

### System Metrics Monitoring
The Performance Optimization tab provides real-time monitoring of:

- **CPU Usage**: Current and historical CPU utilization
- **Memory Usage**: RAM usage and availability
- **Disk I/O**: Read/write operations and throughput
- **Network**: Network traffic and bandwidth usage

### Code Performance Analysis
1. **Select Files**: Choose files for performance analysis
2. **Run Analysis**: Execute performance profiling
3. **View Results**: Review performance metrics and recommendations
4. **Export Reports**: Export detailed performance reports

### Optimization Features
- **Performance Scoring**: Calculate optimization scores
- **Issue Detection**: Identify performance bottlenecks
- **Recommendations**: Get optimization suggestions
- **Benchmarking**: Compare performance across versions

## Web Server Mode

### Starting Web Server
```bash
python run_api_server.py --web-server
```

### Configuration Options
```bash
python run_api_server.py \
  --host 0.0.0.0 \
  --port 8080 \
  --web-server \
  --debug
```

### Web Interface Features
- **Cross-platform Access**: Access from any device with a browser
- **Real-time Collaboration**: WebSocket-based real-time features
- **API Documentation**: Auto-generated API docs at `/docs`
- **Multi-user Support**: Support for multiple concurrent users

### Security Configuration
- **SSL/TLS**: Configure SSL certificates for HTTPS
- **Authentication**: Implement user authentication
- **CORS**: Configure cross-origin resource sharing
- **Rate Limiting**: Implement API rate limiting

## Collaboration Features

### Team Management
1. **Add Team Members**: Add team members with roles
2. **Project Management**: Create and manage projects
3. **Task Tracking**: Track project tasks and status
4. **Communication**: Real-time team chat

### File Sharing
- **Code Snippets**: Share code snippets with team
- **File Upload**: Upload and share files
- **Version Control**: Track file versions
- **Comments**: Add comments and feedback

### Real-time Features
- **Live Chat**: Real-time team communication
- **Status Updates**: Live status updates
- **Notifications**: Real-time notifications
- **Activity Feed**: Team activity tracking

## Advanced Analytics

### Developer Metrics
- **Code Quality**: Track code quality metrics
- **Performance**: Monitor performance trends
- **Security**: Track security metrics
- **Productivity**: Measure team productivity

### Custom Reports
1. **Select Metrics**: Choose metrics to include
2. **Set Time Range**: Define report time period
3. **Generate Report**: Create custom reports
4. **Export Data**: Export reports in various formats

### Trend Analysis
- **Historical Data**: View historical trends
- **Predictions**: Get trend predictions
- **Comparisons**: Compare metrics over time
- **Insights**: Get actionable insights

## Configuration Files

### Main Configuration Files

#### `llm_studio_config.json`
```json
{
  "default_provider": "openai",
  "providers": {
    "openai": {
      "provider_type": "openai",
      "api_key": "your-api-key",
      "base_url": "https://api.openai.com/v1",
      "enabled": true
    }
  },
  "models": {
    "gpt-4": {
      "name": "gpt-4",
      "provider": "openai",
      "model_type": "chat",
      "max_tokens": 4096,
      "temperature": 0.7
    }
  },
  "ollama_instances": [
    {
      "instance_name": "Local Ollama",
      "base_url": "http://localhost:11434",
      "enabled": true
    }
  ]
}
```

#### `security_intelligence_config.json`
```json
{
  "feeds": [
    {
      "name": "NVD CVE Feed",
      "url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss-analyzed.xml",
      "feed_type": "rss",
      "enabled": true,
      "fetch_interval": 3600,
      "tags": ["cve", "vulnerability"]
    }
  ]
}
```

#### `code_standards_config.json`
```json
{
  "current_standard": "Company Python Standard",
  "standards": [
    {
      "name": "Company Python Standard",
      "description": "Python coding standards",
      "company": "Your Company",
      "version": "1.0.0",
      "languages": ["python"],
      "enabled": true
    }
  ]
}
```

#### `pr_automation_config.json`
```json
{
  "services": [
    {
      "service_type": "jira",
      "name": "JIRA-Prod",
      "base_url": "https://company.atlassian.net",
      "username": "your-email@company.com",
      "api_token": "your-api-token",
      "project_key": "PROJ"
    }
  ],
  "templates": [
    {
      "name": "Feature Template",
      "title_template": "feat: {title}",
      "body_template": "## Description\n{description}",
      "branch_prefix": "feature/",
      "is_default": true
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### Security Intelligence Data Not Displaying
1. **Check Feed Configuration**: Verify feed URLs are accessible
2. **Check Network**: Ensure internet connectivity
3. **Check Logs**: Review application logs for errors
4. **Refresh Data**: Use refresh button to reload data

#### Code Standards Analysis Failing
1. **Check File Permissions**: Ensure read access to files
2. **Verify Language Support**: Check if language is supported
3. **Check Configuration**: Verify standards configuration
4. **Review Logs**: Check for analysis errors

#### PR Automation Issues
1. **Check API Server**: Ensure API server is running
2. **Verify Service Configuration**: Check JIRA/ServiceNow settings
3. **Test Connections**: Use connection test features
4. **Check Git Configuration**: Verify Git is properly configured

#### Ollama Connection Issues
1. **Check URL**: Verify Ollama server URL
2. **Test Network**: Ensure network connectivity
3. **Check Authentication**: Verify credentials if required
4. **Check SSL**: Verify SSL configuration

### Debug Mode
Enable debug mode for detailed logging:
```bash
python main.py --debug
```

### Log Files
Check log files for detailed error information:
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Debug logs: `logs/debug.log`

### Support
For additional support:
1. Check the [User Manual](user_manual.md)
2. Review [Architecture Documentation](ARCHITECTURE.md)
3. Check [GitHub Issues](https://github.com/oldnordic/ai-coder-assistant/issues)
4. Review [Test Suite Guide](test_suite_guide.md)

---

This guide covers all major features and configurations for AI Coder Assistant v2.6.0. For detailed information about specific features, refer to the individual feature guides in the `docs/` directory. 