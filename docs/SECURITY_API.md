# API Security Documentation

## Overview

This document outlines the security measures implemented in the AI Coder Assistant REST API to address critical vulnerabilities and ensure secure operation.

## Critical Security Fixes

### 1. Authentication System

#### **Problem**: Insecure Authentication
- **Issue**: The `/auth/login` endpoint was accepting any username/password combination
- **Risk**: Anyone could gain unauthorized access to the API

#### **Solution**: Proper User Authentication
- **Implementation**: SQLite-based user database with password hashing
- **Features**:
  - User registration and login with proper credential verification
  - Password hashing using SHA-256
  - JWT token-based authentication
  - User role management (admin/user)
  - Session tracking with last login timestamps

#### **Usage**:
```bash
# Register a new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "securepassword"}'

# Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 2. Path Validation

#### **Problem**: Directory Traversal Vulnerability
- **Issue**: Scan endpoints accepted arbitrary paths without validation
- **Risk**: Malicious users could access sensitive system files using paths like `../../../../etc/passwd`

#### **Solution**: Path Sanitization and Validation
- **Implementation**: 
  - Path resolution using `os.path.realpath()`
  - Whitelist of allowed directories
  - File existence validation
  - Absolute path normalization

#### **Allowed Directories**:
- Current project directory (`.`)
- Source directory (`src/`)
- Data directory (`data/`)
- Tests directory (`tests/`)

#### **Security Features**:
- Prevents access to system directories
- Validates file existence before processing
- Returns clear error messages for invalid paths
- Logs all path validation attempts

## Environment Variables

### Required for Production
```bash
# JWT Configuration
JWT_SECRET_KEY=your-secure-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# User Database
USER_DB_PATH=data/users.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

# CORS Configuration (for production)
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

### Default Values (Development Only)
- `JWT_SECRET_KEY`: Auto-generated secure random key
- `ADMIN_USERNAME`: "admin"
- `ADMIN_PASSWORD`: "admin123" (CHANGE IN PRODUCTION!)
- `USER_DB_PATH`: "data/users.db"

## Security Best Practices

### 1. Password Security
- Passwords are hashed using SHA-256
- No plaintext password storage
- Password verification against stored hashes

### 2. Token Security
- JWT tokens with configurable expiration
- Secure token generation using `secrets.token_urlsafe()`
- Token validation on all protected endpoints

### 3. Path Security
- All file operations validate paths
- Directory traversal prevention
- Whitelist-based access control

### 4. Error Handling
- Generic error messages to prevent information disclosure
- Proper HTTP status codes
- Input validation on all endpoints

## API Endpoints Security

### Public Endpoints
- `GET /health` - Health check (no authentication required)
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication

### Protected Endpoints (Require JWT Token)
- `POST /scan` - Code scanning
- `POST /security-scan` - Security scanning
- `POST /analyze` - File analysis
- `POST /upload-analyze` - File upload and analysis
- `GET /languages` - Supported languages
- `GET /compliance-standards` - Compliance standards
- `GET /stats` - Scan statistics
- All LLM-related endpoints

## Deployment Security Checklist

### Before Production Deployment
- [ ] Change default admin password
- [ ] Set secure JWT secret key
- [ ] Configure CORS for specific domains
- [ ] Use HTTPS in production
- [ ] Set up proper logging
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security audits

### Monitoring
- Monitor failed login attempts
- Track API usage patterns
- Log all file access attempts
- Monitor for suspicious path requests

## Security Headers

The API includes the following security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

## Rate Limiting

Consider implementing rate limiting for:
- Login attempts (prevent brute force)
- API requests per user
- File uploads
- Scan operations

## Incident Response

### Security Breach Response
1. **Immediate Actions**:
   - Revoke all JWT tokens
   - Disable compromised accounts
   - Review access logs
   - Update security measures

2. **Investigation**:
   - Analyze attack vectors
   - Review system logs
   - Identify affected data
   - Document incident

3. **Recovery**:
   - Implement additional security measures
   - Update user passwords if necessary
   - Restore from secure backups
   - Notify affected users

## Compliance

The API security measures align with:
- OWASP Top 10
- CWE/SANS Top 25
- GDPR requirements (if applicable)
- SOC 2 Type II (if applicable)

## Contact

For security issues or questions:
- Create a security issue in the repository
- Contact the development team
- Follow responsible disclosure practices 