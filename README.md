# Product Management API

A RESTful API built with FastAPI and SQLAlchemy for managing product information. This project demonstrates modern Python web development practices with automated testing, containerization, and CI/CD integration.

## Table of Contents
1. [Features](#features)
2. [Quick Start](#quick-start)
3. [Development Setup](#development-setup)
4. [Building and Testing](#building-and-testing)
5. [Deployment](#deployment)
6. [API Documentation](#api-documentation)
7. [Contributing](#contributing)

## Features

### Core Features
- RESTful API endpoints for product management
- CRUD operations with input validation
- Comprehensive error handling
- Database agnostic design

### Technical Stack
- FastAPI for modern, async API development
- SQLAlchemy ORM for database operations
- PyBuilder for build automation and testing
- Docker for containerization
- GitLab CI for continuous integration

### Quality Assurance
- 90%+ test coverage
- Automated testing pipeline
- Comprehensive API documentation
- Security best practices

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd product-management

# Install PyBuilder and dependencies
pip install pybuilder
python -m pybuilder.cli install_dependencies

# Build the package
python -m pybuilder.cli publish

# Build and run with Docker
docker build -t product-management .
docker run -d -p 80:80 --env-file .env product-management
```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- PyBuilder
- Docker (for containerized deployment)
- MySQL (for production) or SQLite (for testing)

### Local Setup

1. **Create Python Environment**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```

2. **Install Dependencies**:
```bash
pip install pybuilder
python -m pybuilder.cli install_dependencies
```

3. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Building and Testing

### Build Commands

```bash
# Clean and prepare
python -m pybuilder.cli clean

# Build package
python -m pybuilder.cli publish

# Run tests
python -m pybuilder.cli verify
```

The wheel package will be available at:
`target/dist/dist/product_management-1.0.0-py3-none-any.whl`

### Testing

```bash
# Run unit tests
python -m pybuilder.cli run_unit_tests

# Generate coverage report
python -m pybuilder.cli verify
```

View coverage report at: `htmlcov/index.html`

### Configuration

#### Database Settings
```ini
# .env file
ENVIRONMENT=development     # local, development, test, production
TEST_MODE=false            # true for in-memory SQLite

# MySQL Configuration
MYSQL_URI=mysql://user:password@host:3306/dbname
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_ECHO=false

# PostgreSQL Configuration (optional)
POSTGRES_URI=postgresql://user:password@host:5432/dbname
```

#### Environment Types
- `local` - SQLite file-based database (default)
- `development` - MySQL database
- `test` - In-memory SQLite
- `production` - MySQL or PostgreSQL

## Deployment

### Docker Deployment

```bash
# Build Docker image (after PyBuilder publish)
docker build -t product-management .

# Run container
docker run -d \
  --name product-api \
  -p 80:80 \
  --env-file .env \
  product-management
```

### CI/CD Pipeline

This project uses GitLab CI for automated deployment:

1. **Build Stage**
   - Runs PyBuilder tasks
   - Creates wheel package
   - Builds Docker image

2. **Test Stage**
   - Runs unit tests
   - Generates coverage reports
   - Validates API endpoints

3. **Deploy Stage**
   - Deploys to staging/production
   - Runs health checks
   - Updates documentation

## API Documentation

### Endpoints

#### Product Operations
```
GET    /products           # List all products
GET    /products/{id}      # Get product by ID
POST   /products          # Create product
PUT    /products/{id}     # Update product
DELETE /products/{id}     # Delete product
```

#### Health Check
```
GET    /health            # Service health check
```

### Request Examples

#### Create Product
```json
POST /products
{
    "name": "Sample Product",
    "description": "Product description",
    "price": 29.99
}
```

### Response Examples

#### Success Response
```json
{
    "id": 1,
    "name": "Sample Product",
    "description": "Product description",
    "price": 29.99,
    "created_at": "2025-07-14T13:45:00Z"
}
```

#### Error Response
```json
{
    "error": "Product not found",
    "status_code": 404,
    "detail": "No product found with ID 1"
}
```

### Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `409` - Conflict
- `422` - Validation Error
- `500` - Server Error

## Project Structure

```
product-management/
├── src/
│   ├── main/
│   │   └── python/
│   │       ├── app.py          # FastAPI application
│   │       ├── models.py       # SQLAlchemy models
│   │       └── schemas.py      # Pydantic schemas
│   └── unittest/
│       └── python/
│           └── test_app.py     # Unit tests
├── build.py                    # PyBuilder config
├── Dockerfile                  # Container config
└── requirements.txt           # Dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) file