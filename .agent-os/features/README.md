# RecomAMP Features Documentation

This directory contains detailed technical documentation for each feature and system component of the RecomAMP platform. Each document explains the implementation, data flow, API interactions, and interconnections with other features.

## 📚 Documentation Structure

### Core Systems
- [AMC API Integration](./amc-api-integration.md) - How we interact with Amazon Marketing Cloud
- [Authentication System](./authentication-system.md) - OAuth flow and token management
- [Instance Management](./instance-management.md) - Multi-instance configuration and brand associations

### Query & Execution
- [Query Builder](./query-builder.md) - SQL editor and parameter management
- [Workflow Execution](./workflow-execution.md) - Query execution lifecycle
- [Execution Monitoring](./execution-monitoring.md) - Status polling and result retrieval

### Automation & Scheduling
- [Scheduling System](./scheduling-system.md) - Automated query execution
- [Data Collections](./data-collections.md) - Historical backfill and continuous collection
- [Background Services](./background-services.md) - Token refresh, polling, and executors

### Data Management
- [Campaign Management](./campaign-management.md) - Campaign import and filtering
- [ASIN Management](./asin-management.md) - Product tracking and analysis
- [Database Schema](./database-schema.md) - Supabase tables and relationships

### User Experience
- [Build Guides](./build-guides.md) - Step-by-step query tutorials
- [Query Templates](./query-templates.md) - Pre-built query library
- [Dashboard System](./dashboard-system.md) - Visualization and reporting

### System Architecture
- [Service Layer](./service-layer.md) - Backend service architecture
- [Frontend Architecture](./frontend-architecture.md) - React patterns and state management
- [API Routes](./api-routes.md) - Endpoint documentation
- [System Interconnections](./system-interconnections.md) - How everything connects

## 🔄 Reading Order

For AI systems trying to understand the platform, we recommend this reading order:

1. **System Interconnections** - Get the big picture
2. **AMC API Integration** - Understand the core external dependency
3. **Authentication System** - How users access the platform
4. **Instance Management** - Multi-tenant architecture
5. **Workflow Execution** - Core query processing
6. **Data Collections** - Primary feature focus
7. **Database Schema** - Data structure and relationships

## 🎯 Key Concepts

### Instance ID Duality
Throughout the documentation, you'll see references to two ID systems:
- `instance_id`: AMC's actual instance identifier (string like "amcibersblt")
- `id`: Internal database UUID

### AMC SQL Specifics
AMC uses a modified SQL dialect with:
- Required date format: `YYYY-MM-DDTHH:MM:SS` (no timezone)
- Mandatory aggregations (privacy threshold of 50 users)
- Specific table prefixes and field types

### Service Pattern
All backend services inherit from `DatabaseService` and use:
- Retry decorators for resilience
- Async/await patterns
- Structured logging
- Error handling with specific exception types

## 🔗 Quick Links

- [Product Mission](./../product/mission.md)
- [Technical Roadmap](./../product/roadmap.md)
- [AMC Specifics](./../product/amc-specifics.md)
- [Tech Stack](./../product/tech-stack.md)