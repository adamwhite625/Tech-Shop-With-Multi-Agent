# PinkCapy Tech Store — Multi-Agent E-commerce System

PinkCapy Tech Store is a full-stack tech e-commerce platform powered by a **Multi-Agent AI system**. The platform combines a traditional e-commerce backend (FastAPI + MySQL) with an intelligent AI layer consisting of 4 specialized agents that handle product search, purchase advising, and order management through natural language conversation.

---

## System Architecture

### Overall Architecture

```
                          +-------------------+
                          |    Next.js UI     |
                          |   (Port 3000)     |
                          +--------+----------+
                                   |
                    +--------------+--------------+
                    |                              |
           +-------v--------+           +---------v---------+
           | Website Backend |           |    Host Agent     |
           |  FastAPI :8081  |           | (Orchestrator)    |
           |  (E-commerce    |           |   FastAPI :8000   |
           |   Core API)     |           +--------+----------+
           +-------+--------+                    |
                   |                 +------------+-------------+
                   |                 |            |             |
            +------v------+   +-----v-----+ +---v------+ +----v------+
            |   MySQL DB  |   |  Search   | | Advisor  | |  Order    |
            | (Products,  |   |  Agent    | |  Agent   | |  Agent    |
            |  Orders,    |   | :8001     | | :8002    | | :8003     |
            |  Users)     |   +-----+-----+ +----+-----+ +----+------+
            +-------------+         |            |             |
                                +---v---+   +----v----+   +---v---+
                                | Qdrant|   |  Redis  |   | MySQL |
                                | Vector|   | (Chat   |   | (Order|
                                |  DB   |   | Memory) |   | Query)|
                                +-------+   +---------+   +-------+
```

### Multi-Agent Communication Flow

```
User Message
     |
     v
Host Agent (Intent Classification via GPT-4o-mini)
     |
     +---> intent: "search"  ---> Search Agent (Semantic Search via Qdrant)
     |
     +---> intent: "advisor" ---> Advisor Agent (RAG + Chat Memory)
     |                                   |
     |                                   +---> Search Agent (fetch product context)
     |
     +---> intent: "order"   ---> Order Agent (Tool Calling: check/cancel orders)
     |
     +---> intent: "default" ---> Advisor Agent (General conversation)
```

---

## Table of Contents

1. [Features](#1-features)
2. [Architecture](#2-architecture)
3. [Project Structure](#3-project-structure)
4. [Prerequisites](#4-prerequisites)
5. [Installation and Setup](#5-installation-and-setup)
6. [API Overview](#6-api-overview)
7. [Environment Variables](#7-environment-variables)

---

## 1. Features

- **Multi-Agent AI Chatbot**: 4 specialized AI agents (Host, Search, Advisor, Order) collaborating through Agent-to-Agent (A2A) communication to handle user queries.
- **Semantic Product Search**: Multilingual text search using `paraphrase-multilingual-MiniLM-L12-v2` embeddings stored in Qdrant vector database.
- **Image-based Product Search**: Upload a product image and find visually similar items using CLIP (`clip-ViT-B-32`) embeddings.
- **RAG-based Tech Advisor**: Retrieval-Augmented Generation consultant that fetches real product data before generating personalized recommendations.
- **Order Management via Tool Calling**: LangChain Agent with tool-calling capabilities to check order status and cancel orders through natural conversation.
- **Multi-turn Chat Memory**: Persistent conversation history per session stored in Redis with configurable TTL.
- **Full E-commerce Flow**: Product browsing by category, shopping cart, checkout, order tracking, user authentication (JWT).
- **LLM-powered Intent Classification**: GPT-4o-mini with structured output (Pydantic) for accurate intent routing, with keyword-based fallback.
- **Production Resilience**: Rate limiting (SlowAPI), retry with exponential backoff (Tenacity), structured JSON logging, and Docker health checks.
- **Deployment Ready**: Fully containerized infrastructure with Docker Compose (7 services).

---

## 2. Architecture

### AI Agent Layer (Multi-Agent System)

The system implements a **Host-Delegate** pattern with 4 specialized agents:

| Agent                   | Port | Role                                                                                                     | Key Technology                                             |
| ----------------------- | ---- | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| **Host Agent**    | 8000 | Orchestrator / API Gateway. Classifies user intent and routes to the correct specialist agent.           | GPT-4o-mini (Structured Output), SlowAPI, Tenacity         |
| **Search Agent**  | 8001 | Handles semantic text search and image-based search against the product catalog.                         | SentenceTransformers, CLIP, Qdrant                         |
| **Advisor Agent** | 8002 | RAG-based tech consultant. Retrieves product context from Search Agent, then generates advice using LLM. | LangChain, GPT-4o-mini, Redis Memory                       |
| **Order Agent**   | 8003 | Manages order inquiries using LLM Tool Calling (check status, cancel orders).                            | LangChain AgentExecutor, Tool Calling, MySQL, Redis Memory |

### E-commerce Backend (Website Backend)

A standard FastAPI application providing RESTful APIs for the storefront:

- **Authentication**: JWT-based auth with bcrypt password hashing.
- **Product Catalog**: Categories, products, product metadata with pagination.
- **Shopping Cart**: Add/remove items, quantity management.
- **Checkout & Orders**: Cart-to-order conversion, order history, transaction tracking.

### Tech Stack

| Layer                    | Technologies                                                   |
| ------------------------ | -------------------------------------------------------------- |
| **AI / LLM**       | OpenAI GPT-4o-mini, LangChain, LangGraph, Pydantic v2          |
| **Search**         | SentenceTransformers (MiniLM, CLIP), Qdrant Vector DB          |
| **Backend**        | FastAPI, SQLAlchemy, PyJWT, Passlib                            |
| **Database**       | MySQL 8.0 (Relational), Qdrant (Vector), Redis 7 (Chat Memory) |
| **Frontend**       | Next.js 16, React 19, TypeScript, TailwindCSS v4, Zustand      |
| **Infrastructure** | Docker Compose, Uvicorn, Structured JSON Logging               |

---

## 3. Project Structure

```text
tech-ecommerce-system/
├── database/
│   └── init.sql                    # MySQL schema (users, products, orders, transactions...)
│
├── website_backend/                # E-commerce Core API (FastAPI)
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── database.py             # SQLAlchemy engine & session
│   │   ├── models.py               # ORM models (User, Product, Cart, Order...)
│   │   ├── core/
│   │   │   └── security.py         # JWT auth, password hashing
│   │   ├── routers/                # API endpoints
│   │   │   ├── auth.py             # Login, register, token
│   │   │   ├── product.py          # Product listing & detail
│   │   │   ├── category.py         # Category listing
│   │   │   ├── cart.py             # Cart operations
│   │   │   ├── checkout.py         # Checkout flow
│   │   │   └── orders.py           # Order history
│   │   └── schemas/                # Pydantic request/response models
│   ├── data/                       # CSV seed data (products, categories, metas)
│   ├── seed_db.py                  # Import CSV data into MySQL
│   ├── create_users.py             # Create admin & test user accounts
│   └── requirements.txt
│
├── tech_agent/                     # AI Multi-Agent System
│   ├── host_agent/                 # Orchestrator — Intent Router & API Gateway
│   │   ├── app/
│   │   │   ├── main.py             # Intent classification (LLM + keyword fallback)
│   │   │   ├── core/
│   │   │   │   ├── config.py       # Pydantic Settings (agent URLs, API keys)
│   │   │   │   └── logging_config.py  # Structured JSON logging
│   │   │   └── services/
│   │   │       └── a2a_client.py   # Agent-to-Agent HTTP client with retry logic
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── .env.example
│   │   └── requirements.txt
│   │
│   ├── search_agent/               # Semantic & Image Search (Qdrant + CLIP)
│   │   ├── app/
│   │   │   ├── main.py             # Text search & image search endpoints
│   │   │   ├── ingest_data.py      # Embed & upload product text to Qdrant
│   │   │   └── ingest_images.py    # Embed & upload product images to Qdrant
│   │   ├── data/                   # Product data for ingestion
│   │   ├── download_model.py       # Pre-download models during Docker build
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── .env.example
│   │   └── requirements.txt
│   │
│   ├── advisor_agent/              # RAG-based Tech Consultant
│   │   ├── app/
│   │   │   └── main.py             # RAG pipeline: Search Agent context + LLM + Redis memory
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── .env.example
│   │   └── requirements.txt
│   │
│   ├── order_agent/                # Order Management via Tool Calling
│   │   ├── app/
│   │   │   └── main.py             # LangChain Agent with check_order & cancel_order tools
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── .env.example
│   │   └── requirements.txt
│   │
│   └── shared/                     # Shared utilities (reserved)
│
├── tech_ui/                        # Next.js Frontend
│   ├── src/
│   │   ├── app/                    # App Router pages
│   │   │   ├── page.tsx            # Homepage (categories + product grid)
│   │   │   ├── layout.tsx          # Root layout (Header, Footer, Chatbot)
│   │   │   ├── login/              # Login page
│   │   │   ├── register/           # Registration page
│   │   │   ├── products/           # Product listing & detail ([slug])
│   │   │   ├── cart/               # Shopping cart page
│   │   │   ├── checkout/           # Checkout page
│   │   │   ├── orders/             # Order history page
│   │   │   └── profile/            # User profile page
│   │   ├── components/
│   │   │   ├── Header.tsx          # Navigation bar with search, cart, auth
│   │   │   ├── Footer.tsx          # Site footer
│   │   │   └── Chatbot.tsx         # Floating AI chatbot (text + image upload)
│   │   ├── store/
│   │   │   └── useStore.ts         # Zustand global state (user, cart, auth)
│   │   └── lib/
│   │       └── axios.ts            # Axios clients (webClient :8081, aiClient :8000)
│   ├── package.json
│   └── tailwind.config.ts
│
├── docker-compose.yml              # Full infrastructure orchestration (7 services)
└── .gitignore
```

---

## 4. Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for the Next.js frontend)
- **Docker Desktop** (for MySQL, Qdrant, Redis, and agent containers)
- **OpenAI API Key** (for GPT-4o-mini used by Host, Advisor, and Order agents)

---

## 5. Installation and Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/adamwhite625/Tech-Shop-With-Multi-Agent-System.git
cd Tech-Shop-With-Multi-Agent
```

### Step 2: Configure Environment Variables

Copy `.env.example` to `.env` for each agent and fill in your OpenAI API key:

```bash
# Host Agent
cp tech_agent/host_agent/.env.example tech_agent/host_agent/.env

# Search Agent
cp tech_agent/search_agent/.env.example tech_agent/search_agent/.env

# Advisor Agent
cp tech_agent/advisor_agent/.env.example tech_agent/advisor_agent/.env

# Order Agent
cp tech_agent/order_agent/.env.example tech_agent/order_agent/.env
```

Edit each `.env` file and set `OPENAI_API_KEY=your_actual_key_here`.

### Step 3: Start Infrastructure with Docker Compose

```bash
# Start all services (MySQL, Qdrant, Redis, and 4 AI Agents)
docker-compose up -d
```

This will build and start 7 containers:

| Container              | Service              | Port |
| ---------------------- | -------------------- | ---- |
| `tech_mysql`         | MySQL 8.0            | 3306 |
| `tech_qdrant`        | Qdrant Vector DB     | 6333 |
| `tech_redis`         | Redis 7              | 6379 |
| `tech_search_agent`  | Search Agent         | 8001 |
| `tech_advisor_agent` | Advisor Agent        | 8002 |
| `tech_order_agent`   | Order Agent          | 8003 |
| `tech_host_agent`    | Host Agent (Gateway) | 8000 |

### Step 4: Create and Activate Anaconda Environment (Python Backend)

We highly recommend using Anaconda to manage Python dependencies for the backend services and seed scripts to prevent conflicts.

```bash
# Create a new conda environment named 'tech_ecommerce' with Python 3.11
conda create -n tech_ecommerce python=3.12 -y

# Activate the environment
conda activate tech_ecommerce
```

### Step 5: Seed the Database

Ensure your `tech_ecommerce` conda environment is activated before proceeding.

```bash
cd website_backend

# Install Python dependencies
pip install -r requirements.txt

# Import product data from CSV into MySQL
python seed_db.py

# Create admin and test user accounts
python create_users.py
```

**Default credentials after seeding:**

| Role  | Email                  | Password      |
| ----- | ---------------------- | ------------- |
| Admin | `admin@techshop.com` | `Admin@123` |
| User  | `user@techshop.com`  | `User@123`  |

### Step 6: Ingest Product Data into Qdrant

```bash
cd tech_agent/search_agent/app

# Embed and upload product text data to Qdrant
python ingest_data.py

# (Optional) Embed and upload product images to Qdrant
python ingest_images.py
```

### Step 7: Run the Website Backend

```bash
cd website_backend
uvicorn app.main:app --reload --port 8081
```

### Step 8: Run the Frontend

```bash
cd tech_ui
npm install
npm run dev
```

### Step 9: Verify the Installation

| Service                  | URL                                 |
| ------------------------ | ----------------------------------- |
| Frontend                 | `http://localhost:3000`           |
| Website Backend API Docs | `http://localhost:8081/docs`      |
| Host Agent Health        | `http://localhost:8000/health`    |
| Search Agent Health      | `http://localhost:8001/health`    |
| Advisor Agent Health     | `http://localhost:8002/health`    |
| Order Agent Health       | `http://localhost:8003/health`    |
| Qdrant Dashboard         | `http://localhost:6333/dashboard` |

---

## 6. API Overview

### Website Backend (`localhost:8081`)

All requests are prefixed with `/api`.

| Category             | Endpoint               | Method | Description                                       |
| -------------------- | ---------------------- | ------ | ------------------------------------------------- |
| **Auth**       | `/api/auth/register` | POST   | Register a new user                               |
| **Auth**       | `/api/auth/token`    | POST   | Login and receive JWT                             |
| **Categories** | `/api/categories/`   | GET    | List all product categories                       |
| **Products**   | `/api/products/`     | GET    | List products (with pagination & category filter) |
| **Cart**       | `/api/cart/items`    | POST   | Add item to cart                                  |
| **Checkout**   | `/api/checkout/`     | POST   | Convert cart to order                             |
| **Orders**     | `/api/orders/`       | GET    | View order history                                |

### Host Agent — AI Gateway (`localhost:8000`)

| Endpoint                   | Method | Description                                                                                 |
| -------------------------- | ------ | ------------------------------------------------------------------------------------------- |
| `/api/orchestrate`       | POST   | Send a text message. Host Agent classifies intent and routes to Search/Advisor/Order agent. |
| `/api/orchestrate/image` | POST   | Upload an image for visual product search (routed to Search Agent CLIP).                    |
| `/health`                | GET    | Health check                                                                                |

### Specialist Agents (Internal)

| Agent         | Endpoint                   | Description                           |
| ------------- | -------------------------- | ------------------------------------- |
| Search Agent  | `POST /api/search`       | Semantic text search                  |
| Search Agent  | `POST /api/search/image` | CLIP image search                     |
| Advisor Agent | `POST /api/chat`         | RAG conversation with product context |
| Order Agent   | `POST /api/chat`         | Order inquiry with tool calling       |

---

## 7. Environment Variables

### Host Agent (`tech_agent/host_agent/.env`)

| Variable              | Description                              | Default                       |
| --------------------- | ---------------------------------------- | ----------------------------- |
| `OPENAI_API_KEY`    | OpenAI API key for intent classification | (required)                    |
| `SEARCH_AGENT_URL`  | Search Agent base URL                    | `http://search_agent:8001`  |
| `ADVISOR_AGENT_URL` | Advisor Agent base URL                   | `http://advisor_agent:8002` |
| `ORDER_AGENT_URL`   | Order Agent base URL                     | `http://order_agent:8003`   |

### Search Agent (`tech_agent/search_agent/.env`)

| Variable       | Description                | Default                |
| -------------- | -------------------------- | ---------------------- |
| `QDRANT_URL` | Qdrant vector database URL | `http://qdrant:6333` |

### Advisor Agent (`tech_agent/advisor_agent/.env`)

| Variable                | Description                                 | Default                                 |
| ----------------------- | ------------------------------------------- | --------------------------------------- |
| `OPENAI_API_KEY`      | OpenAI API key for RAG generation           | (required)                              |
| `SEARCH_AGENT_URL`    | Search Agent endpoint for context retrieval | `http://search_agent:8001/api/search` |
| `REDIS_URL`           | Redis URL for chat memory                   | `redis://redis:6379/0`                |
| `SESSION_TTL_SECONDS` | Chat session expiry time                    | `3600`                                |

### Order Agent (`tech_agent/order_agent/.env`)

| Variable                | Description                               | Default                                                   |
| ----------------------- | ----------------------------------------- | --------------------------------------------------------- |
| `OPENAI_API_KEY`      | OpenAI API key for tool calling agent     | (required)                                                |
| `DB_URL`              | MySQL connection string for order queries | `mysql+pymysql://root:root@mysql_db:3306/tech_store_db` |
| `REDIS_URL`           | Redis URL for chat memory                 | `redis://redis:6379/0`                                  |
| `SESSION_TTL_SECONDS` | Chat session expiry time                  | `3600`                                                  |
