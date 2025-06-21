# AI Coder Assistant - Unified API Server

## Overview

The AI Coder Assistant Unified API Server is a modern, enterprise-grade FastAPI application that consolidates all backend services into a single, robust API. This replaces the previous dual-server setup (Flask + FastAPI) with a unified approach that provides better performance, maintainability, and developer experience.

## Architecture

### Unified Design
- **Single API Server**: All functionality consolidated into one FastAPI application
- **BackendController Integration**: Uses the existing `BackendController` for unified business logic
- **Two-Stage Analysis**: Implements the decoupled quick scan + AI enhancement approach
- **Modern FastAPI**: Built on Starlette and Pydantic for performance and data validation
- **Production Ready**: Includes authentication, CORS, health checks, and monitoring

### Key Features
- **Interactive API Documentation**: Automatic Swagger UI and ReDoc generation
- **JWT Authentication**: Secure token-based authentication
- **Real-time Communication**: WebSocket support for live updates
- **Data Validation**: Pydantic models for request/response validation
- **Async Support**: Full asynchronous operation for better performance
- **Health Monitoring**: Built-in health checks and metrics

## Quick Start

### Using Docker (Recommended)

```bash
# Start the unified API server
docker-compose up api

# Or start with GUI
docker-compose --profile gui up

# Or start all services
docker-compose up
```

### Local Development

```bash
# Install dependencies
pip install -r api/requirements.txt

# Set environment variables
export JWT_SECRET_KEY="your-secret-key"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="admin123"

# Run the server
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /auth/login` - Login with username/password
- `POST /auth/register` - Register new user
- `POST /auth/verify` - Verify JWT token

### Core Analysis
- `POST /api/v1/quick-scan` - Perform quick static analysis
- `POST /api/v1/ai-enhancement` - Start AI enhancement for specific issues
- `GET /api/v1/enhancement-status/{task_id}` - Check enhancement status
- `DELETE /api/v1/enhancement/{task_id}` - Cancel enhancement task
- **Export Scan Report:** Now supports `JSON`, `CSV`, `Markdown (.md)`, and `PDF` formats.

### Code Standards
- `GET /api/v1/code-standards` - Get configured code standards
- `POST /api/v1/code-standards` - Add new code standard
- `DELETE /api/v1/code-standards/{name}` - Remove code standard

### Security Intelligence
- `GET /api/v1/security-feeds` - Get security intelligence feeds
- `GET /api/v1/security-vulnerabilities` - Get security vulnerabilities
- `POST /api/v1/security-feeds` - Add security feed

### Model Management
- `GET /api/v1/available-models` - List available AI models
- `POST /api/v1/switch-model` - Switch to different model

### Real-time Communication
- `WS /ws` - WebSocket endpoint for real-time updates

### System
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

## Two-Stage Analysis Workflow

### Stage 1: Quick Scan
```bash
curl -X POST "http://localhost:8000/api/v1/quick-scan" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/your/code",
    "language": "python",
    "type_filter": ["*.py", "*.js"],
    "severity_filter": ["high", "medium"]
  }'
```

### Stage 2: AI Enhancement
```bash
# Start AI enhancement for a specific issue
curl -X POST "http://localhost:8000/api/v1/ai-enhancement" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_data": {
      "file": "src/main.py",
      "line": 42,
      "issue": "Unused variable detected",
      "severity": "medium"
    },
    "enhancement_type": "code_improvement"
  }'

# Check enhancement status
curl -X GET "http://localhost:8000/api/v1/enhancement-status/TASK_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Authentication

### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### Using JWT Token
```bash
# Include the token in subsequent requests
curl -X GET "http://localhost:8000/api/v1/code-standards" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## WebSocket Usage

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Send quick scan request
ws.send(JSON.stringify({
  type: 'quick_scan',
  directory_path: '/path/to/code'
}));

// Send AI enhancement request
ws.send(JSON.stringify({
  type: 'ai_enhancement',
  issue_data: {
    file: 'src/main.py',
    line: 42,
    issue: 'Unused variable'
  },
  enhancement_type: 'code_improvement'
}));

// Handle responses
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## Configuration

### Environment Variables
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- `ADMIN_USERNAME` - Default admin username
- `ADMIN_PASSWORD` - Default admin password
- `USER_DB_PATH` - Path to user database
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

### Docker Environment
```yaml
environment:
  - JWT_SECRET_KEY=your-secret-key-change-in-production
  - ADMIN_USERNAME=admin
  - ADMIN_PASSWORD=admin123
  - USER_DB_PATH=/app/data/users.db
```

## Development

### Running Tests
```bash
# Run API tests
pytest api/tests/

# Run with coverage
pytest --cov=api --cov-report=html
```

### Code Quality
```bash
# Format code
black api/

# Lint code
flake8 api/

# Type checking
mypy api/
```

## Migration from Dual-Server Setup

### What Changed
1. **Consolidated Servers**: Flask and FastAPI servers merged into single FastAPI app
2. **Unified Business Logic**: All endpoints now use `BackendController`
3. **Modern API Design**: RESTful endpoints with proper HTTP methods
4. **Enhanced Documentation**: Automatic OpenAPI/Swagger documentation
5. **Better Error Handling**: Consistent error responses with proper HTTP status codes

### Migration Steps
1. **Update Client Code**: Change API base URL to `http://localhost:8000`
2. **Update Authentication**: Use JWT tokens instead of session-based auth
3. **Update Endpoints**: Use new unified endpoint paths (`/api/v1/...`)
4. **Update Docker**: Use new `docker-compose.yml` configuration

### Backward Compatibility
- Old Flask endpoints are deprecated but may be temporarily available
- Migration guide available in `/docs/migration.md`
- Support for gradual migration with feature flags

## Production Deployment

### Using Docker Compose
```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With monitoring
docker-compose --profile monitoring up -d
```

### Using Kubernetes
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Deploy with Helm
helm install ai-coder-assistant ./helm/
```

### Environment-Specific Configurations
- `docker-compose.dev.yml` - Development environment
- `docker-compose.prod.yml` - Production environment
- `docker-compose.test.yml` - Testing environment

## Monitoring and Health Checks

### Health Endpoint
```bash
curl http://localhost:8000/health
```

### Metrics
- Prometheus metrics available at `/metrics`
- Custom metrics for API usage, response times, errors
- Integration with Grafana dashboards

### Logging
- Structured logging with JSON format
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log rotation and retention policies

## Security Considerations

### Authentication
- JWT tokens with configurable expiration
- Password hashing with SHA-256
- Role-based access control (admin/user)

### CORS Configuration
- Configurable CORS origins for production
- Secure headers and CSP policies
- Rate limiting and request throttling

### Data Protection
- Sensitive data encrypted at rest
- Secure communication with HTTPS
- Input validation and sanitization

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **Database Errors**: Check file permissions for user database
3. **Authentication Errors**: Verify JWT token and expiration
4. **CORS Errors**: Configure allowed origins properly

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug
```

### Support
- API Documentation: `http://localhost:8000/docs`
- Issue Tracker: GitHub Issues
- Community: Discord/Slack channels

## License

This project is licensed under the GNU General Public License v3.0. See the LICENSE file for details.

## Exporting Reports in Markdown and PDF

You can now export scan reports in Markdown and PDF formats for easy sharing and documentation:

### Example: Export as Markdown
```python
controller.export_scan_report(report_data, "Markdown (.md)", "report.md")
```

### Example: Export as PDF
```python
controller.export_scan_report(report_data, "PDF", "report.pdf")
```

- **Markdown (.md):** Well-formatted, readable, and easy to share in code reviews or documentation.
- **PDF:** Professional, fixed-format for archiving or formal distribution. 