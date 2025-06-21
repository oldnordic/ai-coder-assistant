# AI Coder Assistant

**AI-powered code analysis, security, and automation for modern development.**

---

## 🚀 Quick Start

- **[Installation Guide](docs/installation_guide.md)**
- **[User Manual](docs/user_manual.md)**
- **[Architecture Overview](docs/ARCHITECTURE.md)**
- **[Unified API Documentation](api/README.md)**

---

## 🧩 Core Features

- **AI Code Analysis** ([User Manual](docs/user_manual.md#core-features))
- **Security Intelligence** ([Guide](docs/security_intelligence_guide.md))
- **Code Standards Enforcement** ([Guide](docs/code_standards_guide.md))
- **Performance Optimization** ([User Manual](docs/user_manual.md#performance-optimization))
- **PR Automation** ([Guide](docs/pr_automation_guide.md))
- **Advanced Refactoring** ([Guide](docs/advanced_refactoring_guide.md))
- **Continuous Learning** ([User Manual](docs/user_manual.md#advanced-features))
- **Multi-Provider LLMs** ([Cloud Model Guide](docs/cloud_model_integration_guide.md))
- **Collaboration & Analytics** ([User Manual](docs/user_manual.md#advanced-features))
- **Unified API & CLI** ([API Documentation](api/README.md), [Migration Guide](docs/API_MIGRATION_GUIDE.md))

---

## 🏗️ Architecture

### Unified API Server
The AI Coder Assistant now features a **unified FastAPI server** that consolidates all backend functionality into a single, enterprise-grade API:

- **Single API Server**: All functionality in one FastAPI application
- **Two-Stage Analysis**: Quick scan + AI enhancement workflow
- **JWT Authentication**: Modern, secure authentication
- **Real-time Support**: WebSocket endpoints for live updates
- **Auto-generated Documentation**: Interactive Swagger UI and ReDoc
- **Production Ready**: Docker support, health checks, monitoring

**Quick API Start:**
```bash
# Start the unified API server
docker-compose up api

# Access interactive documentation
open http://localhost:8000/docs

# Test the API
python api/test_unified_api.py
```

---

## 📚 Documentation

- [Full Documentation Index](docs/)
- [Unified API Implementation](docs/UNIFIED_API_IMPLEMENTATION.md)
- [API Migration Guide](docs/API_MIGRATION_GUIDE.md)
- [Build System & Dependency Management](docs/ENHANCED_BUILD_SYSTEM_SUMMARY.md)
- [Test Suite Guide](docs/test_suite_guide.md)
- [Provider System Guide](docs/provider_system_guide.md)
- [Ollama Remote Guide](docs/ollama_remote_guide.md)
- [Cloud Model Integration](docs/cloud_model_integration_guide.md)
- [Web Scraping Guide](docs/web_scraping_guide.md)
- [UI Inventory](docs/ui_inventory.md)
- [Quick Reference Bugfixes](docs/QUICK_REFERENCE_BUGFIXES.md)

---

## 💡 Contributing & Support

- [Setup & Configuration](docs/setup_and_configuration_guide.md)
- [Code Quality Improvements](docs/CODE_QUALITY_IMPROVEMENTS.md)
- [Import Best Practices](docs/IMPORT_BEST_PRACTICES.md)
- [Security](docs/SECURITY.md)
- [Changelog](CHANGELOG.md)

---

**License:** GPL-3.0  
**Docs last updated:** January 2025
