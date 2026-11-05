# AI SQL Database Analyst
> **Agentic AI-Powered Natural Language Relational Database Analytics Platform**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20AI-orange.svg)](https://www.langchain.com/langgraph)
[![Google Gemini](https://img.shields.io/badge/Gemini-3.8%20Flash-4285F4.svg)](https://ai.google.dev/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)

---

## 📌 Project Overview
**AI SQL Database Analyst** is an enterprise-grade full-stack web application that allows users to interact with relational databases using natural language instead of manually writing complex SQL queries.

Unlike conventional Text-to-SQL wrappers, this application implements an **autonomous Agentic AI workflow powered by LangGraph and Google Gemini 3.8 Flash**. The agent dynamically inspects live database schemas, formulates multi-table queries, validates them through an AST security engine, executes only verified read-only SELECT statements, self-heals from runtime errors, computes business observations, and recommends interactive visualizations (Bar, Line, and Pie charts).

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([User Question in Plain English]) --> Q_Node[1. Question Understanding Node]
    Q_Node -->|Ambiguous?| Clarify[Clarification Response]
    Q_Node -->|Clear Intent| Schema_Node[2. Schema Inspection Node]
    
    Schema_Node --> SQL_Gen[3. SQL Generation Node - Gemini 3.8 Flash]
    SQL_Gen --> SQL_Val{4. SQL Validation Node - SQLGlot AST}
    
    SQL_Val -->|Valid Read-Only SELECT| DB_Exec[5. Database Execution Node - MySQL 8]
    SQL_Val -->|Dangerous DDL/DML| Error_Node[6. Error Analysis Node]
    
    DB_Exec -->|Execution Success| Result_Node[7. Result Analysis & Chart Recommendation]
    DB_Exec -->|MySQL Syntax/Schema Error| Error_Node
    
    Error_Node -->|Retry Count < 2| SQL_Gen
    Error_Node -->|Retries Exceeded| Final_Resp[8. Response Generation Node]
    
    Result_Node --> Final_Resp
    Final_Resp --> Dashboard([Interactive React Dashboard & Charts])
```

---

## 🛡️ Key Software Engineering & Security Highlights

1. **AST-Based SQL Gatekeeper (SQLGlot):**
   - Strictly validates queries before they touch the database.
   - Enforces single statement execution (mitigating stacked query SQL injection).
   - Guarantees the query is purely an `exp.Select` or `exp.Union`.
   - Rejects `DROP`, `ALTER`, `DELETE`, `UPDATE`, `INSERT`, `TRUNCATE`, `GRANT`, `REVOKE`, and dangerous functions (`SLEEP`, `LOAD_FILE`, etc.).
   - Dynamically injects and caps `LIMIT` bounds to prevent memory exhaustion.
2. **Dedicated Read-Only Account (`analyst_readonly`):**
   - User-supplied queries execute through a dedicated non-administrative MySQL account granted solely `SELECT` permissions.
3. **AES-128 Credential Encryption at Rest:**
   - Database passwords are encrypted with `cryptography.fernet.Fernet` derived from the app's `SECRET_KEY` and decrypted strictly in memory.
4. **Self-Healing Agent Loop:**
   - If MySQL returns a runtime error (e.g. unknown column or join failure), the error message is fed back into Gemini's prompt to automatically correct the query up to 2 times without human intervention.
5. **No Hardcoded Schemas:**
   - Dynamically introspects live schemas using SQLAlchemy, discovering tables, data types, primary keys, and foreign keys.

---

## 📊 Sample Database Schema (`ecommerce_db`)

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : "places"
    ORDERS ||--|{ ORDER_ITEMS : "contains"
    PRODUCTS ||--o{ ORDER_ITEMS : "ordered_in"
    ORDERS ||--o| PAYMENTS : "paid_by"

    CUSTOMERS {
        int id PK
        string name
        string email UK
        string city
        datetime created_at
    }
    PRODUCTS {
        int id PK
        string name
        string category
        decimal price
        int stock
    }
    ORDERS {
        int id PK
        int customer_id FK
        datetime order_date
        string status
    }
    ORDER_ITEMS {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal price
    }
    PAYMENTS {
        int id PK
        int order_id FK
        decimal amount
        string payment_status
        datetime payment_date
    }
```

---

## 🚀 Quick-Start Guide (Windows PowerShell)

### 1. Backend Setup

```powershell
# Navigate to project root
cd d:\AI_SQL_DATABASE

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Configure your environment in .env (Add your GEMINI_API_KEY and MySQL credentials)
# Start the FastAPI server
uvicorn backend.main:app --reload --port 8000
```
* Backend Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend Setup

Open a **second PowerShell window**:

```powershell
cd d:\AI_SQL_DATABASE\frontend

# Install frontend dependencies
npm install

# Start Vite React development server
npm run dev
```
* Web Dashboard: [http://localhost:5173/](http://localhost:5173/)

### 3. Run Automated Tests

```powershell
pytest -v
```

---

## 📋 Roadmap & Implementation Checklist

- [x] **Phase 1: Project Initialization & Environment Setup**
- [x] **Phase 2: MySQL Sample E-Commerce Database (`ecommerce_db`)**
- [x] **Phase 3: Python & MySQL Connection Layer via SQLAlchemy 2.0**
- [x] **Phase 4: Dynamic Database Schema Inspection Tool**
- [x] **Phase 5: Gemini 3.8 Flash Integration & Structured SQL Generation**
- [x] **Phase 6: AST-Based SQL Validation & Read-Only Execution Engine**
- [x] **Phase 7: LangGraph Agentic Workflow & Self-Healing Retry Loop**
- [x] **Phase 8: Business Result Analysis & Data Visualization Selection**
- [x] **Phase 9: FastAPI REST Endpoints & Authentication**
- [x] **Phase 10: SaaS-Style React + Tailwind CSS Dashboard**
- [x] **Phase 11: Recharts Interactive Visualizations & Query History UI**
- [x] **Phase 12: Automated Test Suite (43 Unit & Integration Tests)**
- [x] **Phase 13: Docker & Docker Compose Multi-Container Orchestration**
- [x] **Phase 14: Comprehensive Project Documentation & Architecture Guides**
