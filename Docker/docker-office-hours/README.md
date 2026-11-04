# Docker Office Hours - E-Commerce Product Catalog

## Purpose

This hands-on training is designed to reinforce Docker concepts learned in the previous sessions by building a real-world multi-container application. We will implement a complete e-commerce product catalog system using Docker, Docker Compose, and best practices.

## Learning Outcomes

At the end of this hands-on training, we will be able to:

- Design and implement multi-container applications
- Use Docker Compose to orchestrate multiple services
- Implement container networking and service communication
- Configure persistent data storage with volumes
- Manage environment variables and application configuration
- Build production-ready Docker images
- Implement caching strategies with Redis
- Debug and troubleshoot containerized applications
- Apply Docker best practices and security principles

## Project Overview

### What We're Building

A **Product Catalog System** with the following features:

- View all products
- View single product details
- Add new products
- Update existing products
- Delete products
- Redis caching for improved performance

### Technology Stack

- **Frontend**: React (simple UI for product management)
- **Backend**: Flask (RESTful API)
- **Database**: PostgreSQL (persistent data storage)
- **Cache**: Redis (performance optimization)
- **Orchestration**: Docker Compose

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                        Docker Bridge Network                │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   Frontend   │      │   Backend    │                     │
│  │   (React)    │◄────►│   (Flask)    │                     │
│  │   Port 3000  │      │   Port 5000  │                     │
│  └──────────────┘      └───────┬──────┘                     │
│                                 │                           │
│                        ┌────────┴────────┐                  │
│                        │                 │                  │
│                 ┌──────▼──────┐   ┌─────▼──────┐            │
│                 │  PostgreSQL │   │   Redis    │            │
│                 │  (Database) │   │  (Cache)   │            │
│                 │  Port 5432  │   │  Port 6379 │            │
│                 └─────────────┘   └────────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Service Details

1. **Frontend Service**

   - Technology: React
   - Purpose: User interface for product management
   - Exposed Port: 3000
   - Dependencies: Backend API
2. **Backend Service**

   - Technology: Flask (Python)
   - Purpose: RESTful API for CRUD operations
   - Exposed Port: 5000
   - Dependencies: PostgreSQL, Redis
   - Features:
     - Product CRUD operations
     - Redis caching for GET requests
     - Database connectivity
     - Error handling
3. **PostgreSQL Service**

   - Purpose: Persistent data storage
   - Internal Port: 5432 (not exposed to host)
   - Features:
     - Data persistence with volumes
     - Initial data seeding
     - Connection from backend only
4. **Redis Service**

   - Purpose: Caching layer
   - Internal Port: 6379 (not exposed to host)
   - Features:
     - Cache product listings
     - TTL (Time To Live) configuration
     - Cache invalidation on updates

## API Endpoints for Backend Service

| Method | Endpoint          | Description        | Cache             |
| ------ | ----------------- | ------------------ | ----------------- |
| GET    | /api/products     | Get all products   | Yes               |
| GET    | /api/products/:id | Get single product | Yes               |
| POST   | /api/products     | Create new product | Invalidates cache |
| PUT    | /api/products/:id | Update product     | Invalidates cache |
| DELETE | /api/products/:id | Delete product     | Invalidates cache |
| GET    | /api/health       | Health check       | No                |

## Project Structure

```
docker-office-hours/
├── README.md                           # This file
├── docker-compose.yml                  # Multi-container orchestration
├── .env.example                        # Environment variables template
├── .gitignore                          # Git ignore file
│
├── backend/
│   ├── Dockerfile                      # Backend image definition
│   ├── requirements.txt                # Python dependencies
│   ├── app/
│   │   ├── __init__.py                # Flask app initialization
│   │   ├── main.py                    # Application entry point
│   │   ├── models.py                  # Database models
│   │   ├── routes.py                  # API routes
│   │   └── cache.py                   # Redis cache utilities
│
├── frontend/
│   ├── Dockerfile                      # Frontend image definition
│   ├── package.json                    # Node.js dependencies
│   ├── public/
│   │   └── index.html                 # HTML template
│   └── src/
│       ├── App.js                     # Main React component
│       ├── index.js                   # React entry point
│       ├── ProductList.js             # Product listing component
│       └── ProductForm.js             # Add/Edit product form
│
└── database/
    └── init.sql                        # Database initialization script
```

## Hands-On Implementation Guide

### Session Timeline (3 Hours)

**Hour 1: Setup & Architecture (60 minutes)**

- Part 1: Project Introduction (10 min)
- Part 2: EC2 Instance Setup (10 min)
- Part 3: Project Structure Creation (15 min)
- Part 4: Backend Service Implementation (25 min)

**Hour 2: Integration & Deployment (60 minutes)**

- Part 5: Database Setup (15 min)
- Part 6: Redis Cache Implementation (15 min)
- Part 7: Frontend Development (20 min)
- Part 8: Docker Compose Configuration (10 min)

**Hour 3: Production & Best Practices (60 minutes)**

- Part 9: Running the Application (15 min)
- Part 10: Testing & Debugging (15 min)
- Part 11: Production Best Practices (15 min)
- Part 12: Q&A and Troubleshooting (15 min)

---

## Part 1 - Project Introduction (10 minutes)

### Overview

Explain the architecture and what we're building.

**Key Points to Cover:**

1. Multi-container application concept
2. Microservices architecture basics
3. Why we use each technology
4. Real-world use cases

**Discussion Topics:**

- How this relates to real production applications
- Scalability considerations
- Why separate frontend and backend

---

## Part 2 - Launch EC2 Instance and Setup (10 minutes)

### Launch EC2 Instance

- Launch a Docker-enabled EC2 instance on Amazon Linux 2023 AMI with security group allowing SSH (port 22), HTTP (port 3000), and API (port 5000) connections.

**Security Group Rules:**

```
Type        Protocol    Port Range    Source         Description
SSH         TCP         22           0.0.0.0/0      SSH access
Custom TCP  TCP         3000         0.0.0.0/0      Frontend
Custom TCP  TCP         5000         0.0.0.0/0      Backend API
```

### Connect to Instance

```bash
ssh -i your-key.pem ec2-user@<your-ec2-public-ip>
```

### Install Docker and Docker Compose

**Step 1: Install Docker**

```bash
# Update package manager
sudo dnf update -y

# Install Docker
sudo dnf install docker -y

# Start Docker service
sudo systemctl start docker

# Enable Docker to start on boot
sudo systemctl enable docker

# Add ec2-user to docker group (to run docker without sudo)
sudo usermod -a -G docker ec2-user

# Apply group changes (logout and login, or use this command)
newgrp docker

# Verify Docker installation
docker --version
```

**Step 2: Install Docker Compose**

```bash
# Download Docker Compose
sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

**Verify both are working:**

```bash
docker ps
docker-compose version
```

---

## Part 3 - Create Project Structure (15 minutes)

### Create Base Directory Structure

```bash
# Create project root
mkdir -p ~/ecommerce-docker
cd ~/ecommerce-docker

# Create service directories
mkdir -p backend/app
mkdir -p frontend/src/components
mkdir -p frontend/public
mkdir -p database
```

### Verify Structure

```bash
sudo dnf install tree -y
tree -L 2
```

**Expected Output:**

```
ecommerce-docker/
├── backend
│   └── app
├── database
└── frontend
    ├── public
    └── src
```

---

## Part 4 - Backend Service Implementation (25 minutes)

### Step 1: Create Backend Dependencies

Create `backend/requirements.txt`:

> **What this file does:** Lists all Python packages needed by the Flask backend (web framework, database driver, Redis client, CORS support, and environment variable manager).

```bash
cat > backend/requirements.txt << 'EOF'
Flask==3.0.0
Flask-CORS==4.0.0
psycopg2-binary==2.9.9
redis==5.0.1
python-dotenv==1.0.0
EOF
```

**Explain each dependency:**

- `Flask`: Web framework
- `Flask-CORS`: Flask-CORS enables cross-origin requests between frontend and backend on different ports - browsers block these by default for security.
- `psycopg2-binary`: PostgreSQL database driver that allows Python code to connect to PostgreSQL, execute SQL queries, and retrieve results.
- `redis`: Redis client library for Python - enables connecting to Redis cache server, storing/retrieving data, and setting TTL (Time To Live) for cached values.
- `python-dotenv`: Environment variable management loads environment variables from .env file into Python - keeps sensitive data (passwords, API keys) out of code and enables easy configuration per
  environment.

### Step 2: Create Database Models

Create `backend/app/models.py`:

> **What this file does:** Defines the Product data model (class) with methods to convert between Python objects and JSON format for API responses.

```bash
cat > backend/app/models.py << 'EOF'
"""
Database models for the e-commerce application
"""

class Product:
    """Product model representing items in the catalog"""

    def __init__(self, id=None, name=None, description=None, price=None, stock=None):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.stock = stock

    def to_dict(self):
        """Convert product to dictionary format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else None,
            'stock': self.stock
        }

    @staticmethod
    def from_dict(data):
        """Create product from dictionary"""
        return Product(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            price=data.get('price'),
            stock=data.get('stock')
        )
EOF
```

### Step 3: Create Cache Utilities

Create `backend/app/cache.py`:

> **What this file does:** Contains helper functions to store, retrieve, and delete product data in Redis cache with automatic expiration (TTL).

```bash
cat > backend/app/cache.py << 'EOF'
"""
Redis cache utilities
"""
import json
import redis
import os

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

def get_cached_products():
    """Get products from cache"""
    try:
        cached = redis_client.get('products:all')
        if cached:
            return json.loads(cached)
        return None
    except Exception as e:
        print(f"Cache error: {e}")
        return None

def set_cached_products(products, ttl=300):
    """Cache products with TTL (default 5 minutes)"""
    try:
        redis_client.setex(
            'products:all',
            ttl,
            json.dumps(products)
        )
    except Exception as e:
        print(f"Cache error: {e}")

def invalidate_products_cache():
    """Invalidate products cache"""
    try:
        redis_client.delete('products:all')
    except Exception as e:
        print(f"Cache error: {e}")

def get_cached_product(product_id):
    """Get single product from cache"""
    try:
        cached = redis_client.get(f'product:{product_id}')
        if cached:
            return json.loads(cached)
        return None
    except Exception as e:
        print(f"Cache error: {e}")
        return None

def set_cached_product(product_id, product, ttl=300):
    """Cache single product"""
    try:
        redis_client.setex(
            f'product:{product_id}',
            ttl,
            json.dumps(product)
        )
    except Exception as e:
        print(f"Cache error: {e}")
EOF
```

**Explain caching strategy:**

Redis caching improves performance by storing frequently accessed data in memory:

1. **TTL (Time To Live): 5 minutes**

   - Cached data automatically expires after 5 minutes (300 seconds)
   - First request fetches from PostgreSQL and stores in Redis
   - Subsequent requests within 5 minutes are served from Redis (much faster!)
   - After 5 minutes, cache expires and next request fetches fresh data from database
   - Example: If you fetch products at 2:00 PM, Redis serves it instantly until 2:05 PM
2. **Cache Invalidation on Write Operations**

   - When you CREATE, UPDATE, or DELETE a product, the cache is immediately cleared
   - This ensures users always see the most up-to-date data after changes
   - Without invalidation, users might see old data for up to 5 minutes
   - Example: Add new product → cache cleared → next GET request fetches fresh data from database
3. **Separate Cache Keys**

   - `products:all` - stores the complete list of all products
   - `product:1`, `product:2`, etc. - stores individual product details
   - Separate keys allow independent caching and invalidation
   - Example: If product #5 is updated, only `product:5` needs to be invalidated, not the entire list

**Test cache behavior:**

```bash
# First request - from database (slower)
curl http://localhost:5000/api/products
# Response includes: "source": "database"

# Second request - from cache (faster!)
curl http://localhost:5000/api/products
# Response includes: "source": "cache"

# Create a new product - invalidates cache
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name":"New Item","description":"Test","price":25.00,"stock":5}'

# Next request - from database again (cache was cleared)
curl http://localhost:5000/api/products
# Response includes: "source": "database"
```

### Step 4: Create API Routes

Create `backend/app/routes.py`:

> **What this file does:** Implements all REST API endpoints (GET, POST, PUT, DELETE) for product management with PostgreSQL database operations and Redis caching logic.

```bash
cat > backend/app/routes.py << 'EOF'
"""
API routes for product management
"""
from flask import Blueprint, request, jsonify
import psycopg2
import os
from .models import Product
from . import cache

api = Blueprint('api', __name__)

def get_db_connection():
    """Create database connection"""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres'),
        database=os.getenv('DB_NAME', 'ecommerce'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )
    return conn

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'backend'}), 200

@api.route('/products', methods=['GET'])
def get_products():
    """Get all products with caching"""
    # Check cache first
    cached_products = cache.get_cached_products()
    if cached_products:
        return jsonify({
            'products': cached_products,
            'source': 'cache'
        }), 200

    # If not in cache, get from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, price, stock FROM products ORDER BY id')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    products = []
    for row in rows:
        product = Product(
            id=row[0],
            name=row[1],
            description=row[2],
            price=row[3],
            stock=row[4]
        )
        products.append(product.to_dict())

    # Cache the results
    cache.set_cached_products(products)

    return jsonify({
        'products': products,
        'source': 'database'
    }), 200

@api.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product by ID"""
    # Check cache
    cached_product = cache.get_cached_product(product_id)
    if cached_product:
        return jsonify({
            'product': cached_product,
            'source': 'cache'
        }), 200

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, name, description, price, stock FROM products WHERE id = %s',
        (product_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row is None:
        return jsonify({'error': 'Product not found'}), 404

    product = Product(
        id=row[0],
        name=row[1],
        description=row[2],
        price=row[3],
        stock=row[4]
    )

    product_dict = product.to_dict()
    cache.set_cached_product(product_id, product_dict)

    return jsonify({
        'product': product_dict,
        'source': 'database'
    }), 200

@api.route('/products', methods=['POST'])
def create_product():
    """Create new product"""
    data = request.get_json()

    # Validation
    required_fields = ['name', 'description', 'price', 'stock']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s) RETURNING id',
        (data['name'], data['description'], data['price'], data['stock'])
    )
    product_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    # Invalidate cache
    cache.invalidate_products_cache()

    return jsonify({
        'message': 'Product created successfully',
        'product_id': product_id
    }), 201

@api.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update existing product"""
    data = request.get_json()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if product exists
    cursor.execute('SELECT id FROM products WHERE id = %s', (product_id,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Product not found'}), 404

    # Update product
    cursor.execute(
        'UPDATE products SET name = %s, description = %s, price = %s, stock = %s WHERE id = %s',
        (data['name'], data['description'], data['price'], data['stock'], product_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    # Invalidate cache
    cache.invalidate_products_cache()

    return jsonify({'message': 'Product updated successfully'}), 200

@api.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete product"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM products WHERE id = %s', (product_id,))
    rows_deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if rows_deleted == 0:
        return jsonify({'error': 'Product not found'}), 404

    # Invalidate cache
    cache.invalidate_products_cache()

    return jsonify({'message': 'Product deleted successfully'}), 200
EOF
```

**Explain each endpoint:**

- GET /products: List with cache
- GET /products/🆔 Single item with cache
- POST /products: Create and invalidate cache
- PUT /products/🆔 Update and invalidate cache
- DELETE /products/🆔 Delete and invalidate cache

### Step 5: Create Flask Application

Create `backend/app/__init__.py`:

> **What this file does:** Initializes the Flask application with CORS enabled and registers the API routes blueprint.

```bash
cat > backend/app/__init__.py << 'EOF'
"""
Flask application factory
"""
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for frontend communication

    # Register blueprints
    from .routes import api
    app.register_blueprint(api, url_prefix='/api')

    return app
EOF
```

Create `backend/app/main.py`:

> **What this file does:** The entry point that creates and runs the Flask application on port 5000 for all network interfaces.

```bash
cat > backend/app/main.py << 'EOF'
"""
Application entry point
"""
from . import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF
```

### Step 6: Create Backend Dockerfile

Create `backend/Dockerfile`:

> **What this file does:** Defines how to build the backend Docker image - installs Python dependencies, copies application code, and sets up the container to run Flask on port 5000.

```bash
cat > backend/Dockerfile << 'EOF'
# Use Python 3.11 slim image for smaller size (50MB)
FROM python:3.11-slim

# Set working directory (/app folder will be created automatically and changed to /app folder)
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching and fast build.
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "-m", "app.main"]
EOF
```

---

## Part 5 - Database Setup (15 minutes)

### Step 1: Create Database Initialization Script

Create `database/init.sql`:

> **What this file does:** SQL script that runs automatically when PostgreSQL container starts - creates products table, adds indexes for performance, inserts sample data, and sets up auto-update triggers.

```bash
cat > database/init.sql << 'EOF'
-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on name for faster searches
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

-- Insert sample data
INSERT INTO products (name, description, price, stock) VALUES
    ('Laptop', 'High-performance laptop with 16GB RAM', 1299.99, 15),
    ('Wireless Mouse', 'Ergonomic wireless mouse with USB receiver', 29.99, 50),
    ('USB-C Hub', '7-in-1 USB-C hub with HDMI and card reader', 49.99, 30),
    ('Mechanical Keyboard', 'RGB mechanical keyboard with blue switches', 89.99, 20),
    ('Monitor 27"', '4K UHD monitor with HDR support', 399.99, 10),
    ('Webcam HD', '1080p webcam with built-in microphone', 79.99, 25),
    ('Laptop Stand', 'Adjustable aluminum laptop stand', 39.99, 40),
    ('Headphones', 'Noise-cancelling wireless headphones', 199.99, 18),
    ('External SSD', '1TB portable external SSD', 129.99, 35),
    ('Phone Stand', 'Adjustable phone stand for desk', 19.99, 60);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_products_updated_at BEFORE UPDATE
    ON products FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
EOF
```

**Explain database setup:**

- Table schema with proper data types
- Indexes for performance
- Sample data for testing
- Timestamps for audit trail
- Triggers for automatic updates

### Step 2: Understand Database Service Configuration

**Discussion points:**

- PostgreSQL official image
- Volume for data persistence
- Environment variables for configuration
- Internal networking (not exposed to host)
- Health checks

---

## Part 6 - Redis Cache Implementation (15 minutes)

### Understanding Redis Configuration

**Discuss:**

- Redis official image
- Why we use Alpine (smaller size)
- No persistent storage needed (cache is temporary)
- Internal networking
- Connection from backend only

### Testing Cache Strategy

**Explain the caching flow:**

1. **First Request (Cache Miss):**

   ```
   Browser → Backend → Check Redis → Not found → Query PostgreSQL → Save to Redis → Return data
   ```
2. **Subsequent Requests (Cache Hit):**

   ```
   Browser → Backend → Check Redis → Found → Return cached data (faster!)
   ```
3. **Write Operations (Cache Invalidation):**

   ```
   Browser → Backend → Create/Update/Delete in PostgreSQL → Clear Redis cache → Return success
   ```

**Benefits:**

- Reduced database load
- Faster response times
- Scalability improvement

---

## Part 7 - Frontend Development (20 minutes)

### Step 1: Create Package.json

Create `frontend/package.json`:

> **What this file does:** Defines the React frontend project metadata, lists required npm packages (React, ReactDOM, build scripts), and configures browser compatibility settings.

```bash
cat > frontend/package.json << 'EOF'
{
  "name": "ecommerce-frontend",
  "version": "1.0.0",
  "description": "E-commerce product catalog frontend",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOF
```

### Step 2: Create HTML Template

Create `frontend/public/index.html`:

> **What this file does:** The main HTML template that serves as the container for the React application - includes basic styling and a root div where React components will be rendered.

```bash
cat > frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="E-commerce Product Catalog" />
    <title>Product Catalog</title>
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
          'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
          sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        background-color: #f5f5f5;
      }
    </style>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF
```

### Step 3: Create React Components

Create `frontend/src/index.js`:

> **What this file does:** React entry point that initializes the app and renders the main App component into the HTML root element.

```bash
cat > frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF
```

## Docker Compose

Copy `.env.example` to `.env`, set a strong `DB_PASSWORD`, and set `HOST_IP` to `localhost` for local use or your EC2 public IP/DNS for remote use.

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f
```

Open `http://localhost:3000` locally or `http://<HOST_IP>:3000` remotely. API health: `http://<HOST_IP>:5000/api/health`. Stop with `docker compose down`; `docker compose down -v` also deletes persistent PostgreSQL data.

Security: never commit `.env`; restrict SSH (22) to your own IP. PostgreSQL and Redis are internal-only. The Flask sample uses direct psycopg2 connections (no connection pool). Cache invalidation clears both list and per-product keys.
