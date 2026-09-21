# AetherFlow Architecture Documentation

This document provides a comprehensive technical overview of the **AetherFlow** system architecture, component layout, backend layers, deployment model, and execution flows. 

---

## 1. High-Level System Architecture

AetherFlow uses a modular, decoupled architecture connecting a premium, state-of-the-art React frontend with an asynchronous Python FastAPI backend. The backend operates on a 3-layer pattern (API Router -> Service -> Repository/ORM) backed by a PostgreSQL database. Real-time updates are driven by persistent WebSocket connections.

```mermaid
graph TD
    subgraph Presentation Layer
        UI[React Frontend]
    end

    subgraph Communication Gateways
        WS[WebSocket Manager]
        HTTP[REST API Gateway]
    end

    subgraph FastAPI Backend Core
        Router[API Route Controllers]
        Service[Service Business Logic]
        Repo[Repository / ORM Mapping]
    end

    subgraph Job Execution Pool
        Worker[Autonomous Workers]
        Scheduler[APScheduler / Schedules]
    end

    subgraph Data Layer
        DB[(Supabase PostgreSQL)]
    end

    UI <-->|HTTP REST / JWT| HTTP
    UI <-->|WebSockets| WS
    WS <-->|Broadcasting Loop| Service
    HTTP --> Router
    Router --> Service
    Service --> Repo
    Repo <-->|SQLAlchemy AsyncPG| DB
    Worker <-->|FOR UPDATE SKIP LOCKED| DB
    Scheduler -->|Cron/Interval triggers| Service
```

### Component Descriptions:
- **React Frontend**: A single-page application built on Vite, React 18, Zustand, and TanStack React Query. It displays real-time job and worker telemetry via WebSockets and REST.
- **FastAPI Backend**: Asynchronous gateway utilizing Python 3.11. Exposes REST endpoints, validates auth headers, manages connections, and runs background broadcasts.
- **Service Layer**: Houses the business logic for state transitions, AI failure evaluations, DAG graph traversal, and queue state changes.
- **Repository / ORM Layer**: Leverages SQLAlchemy 2.0 async session pools to interface with the database.
- **Autonomous Workers**: Node processes running concurrently to fetch, lock, execute, and record jobs.
- **Scheduler**: Evaluation engine that tracks interval and cron schedules, dispatching jobs automatically.
- **WebSockets**: Bi-directional communication channel used to push alert toasts and metrics to clients.

---

## 2. Component Diagram

The component diagram details the interaction between the React frontend modules and the FastAPI backend services.

```mermaid
graph LR
    subgraph Frontend Components
        DashboardUI[Overview Panel]
        ObsUI[Observability Matrix]
        WorkflowUI[DAG Visualizer]
        AuthUI[JWT Auth Module]
    end

    subgraph API Gateway
        AuthRouter[Auth Controller]
        QueueRouter[Queue Controller]
        JobRouter[Job Controller]
        ObsRouter[Observability Controller]
        WSRouter[WebSocket Router]
    end

    subgraph Core Services
        AuthSvc[Auth Service]
        QueueSvc[Queue Service]
        JobSvc[Job Service]
        AISvc[AI Failure Analyzer]
        WorkflowSvc[Workflow Service]
        MetricSvc[Metrics Service]
    end

    DashboardUI --> JobRouter
    ObsUI --> ObsRouter
    WorkflowUI --> QueueRouter
    AuthUI --> AuthRouter
    ObsUI & DashboardUI <--> WSRouter

    AuthRouter --> AuthSvc
    QueueRouter --> QueueSvc
    JobRouter --> JobSvc
    ObsRouter --> MetricSvc
    WSRouter <--> MetricSvc

    JobSvc --> AISvc
    JobSvc --> WorkflowSvc
```

---

## 3. Backend Layer Diagram

The backend utilizes strict layering to isolate HTTP logic from database transactions.

```
+-------------------------------------------------------------+
|                         API LAYER                           |
|  - fastapi.APIRouter (auth.py, jobs.py, queues.py, etc.)   |
|  - Pydantic Validation Schemas (dto.py)                     |
|  - CORS and Rate Limiting Middlewares                       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                       SECURITY LAYER                        |
|  - JWT Bearer Header Verification                           |
|  - Tenancy Isolation Filter (checks organizational ID)      |
|  - RBAC Checks (RequirePermission Middleware)               |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                        SERVICE LAYER                        |
|  - Business Logic (job_service.py, queue_service.py, etc.)  |
|  - Failure Analysis parsing (failure_analyzer.py)          |
|  - WebSocket push message generation (notification_service) |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      ORM & REPO LAYER                       |
|  - SQLAlchemy 2.0 Declarative Models (core.py)              |
|  - AsyncSession context managers                           |
|  - Skip Locked transaction executions                       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                       DATABASE LAYER                        |
|  - Supabase PostgreSQL (schema, triggers, constraints)      |
+-------------------------------------------------------------+
```

---

## 4. Deployment Architecture

AetherFlow is optimized for Docker containerization and cloud-native services.

```mermaid
graph TD
    subgraph Client Browser
        Client[React Static Files]
    end

    subgraph Public Network
        Gateway[Cloud Gateway / Load Balancer]
    end

    subgraph Virtual Private Cloud
        API[FastAPI Container]
        Worker1[Worker Node 01 Container]
        Worker2[Worker Node 02 Container]
        Redis[(Redis Cache)]
    end

    subgraph Data Platform
        DB[(Supabase PostgreSQL Database)]
    end

    Client -->|HTTPS / WSS| Gateway
    Gateway -->|Forward Port 8000| API
    Gateway -->|Forward Port 5173| Client
    API <-->|State Queries| DB
    API <-->|WS Sessions| Redis
    Worker1 & Worker2 <-->|FOR UPDATE SKIP LOCKED| DB
    Worker1 & Worker2 <-->|Status Coordination| Redis
```

---

## 5. Authentication Flow

AetherFlow implements multi-tenant token-based authentication using JSON Web Tokens (JWT) with hierarchical role permissions.

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant API as Auth Endpoint
    participant DB as Postgres Database

    User->>API: POST /auth/token (username, password)
    API->>DB: Query User by email
    DB-->>API: User details and Hashed Password
    API->>API: Verify password using Argon2
    alt Invalid Password
        API-->>User: HTTP 401 (Unauthorized)
    else Valid Password
        API->>DB: Fetch Memberships & Tenant Roles
        DB-->>API: Org ID and Role mapping
        API->>API: Generate Access Token (JWT with claims)
        API->>API: Generate Cryptographic Refresh Token
        API->>DB: Insert Session Refresh Token
        API-->>User: Return Tokens (Access & Refresh)
    end
    
    Note over User, API: User requests Workspace Resource
    User->>API: GET /jobs (Headers: Authorization: Bearer <Access Token>)
    API->>API: Decrypt JWT claims & Validate signature
    API->>API: Check user tenant access & Role permissions
    alt Insufficient Permissions (RBAC Check)
        API-->>User: HTTP 403 (Forbidden)
    else Authorized Tenant Access
        API->>DB: Execute Query within Organization isolation
        DB-->>API: Organization records
        API-->>User: Return records (HTTP 200)
    end
```

---

## 6. Job Processing Flow

This diagram illustrates the lifecycle of a job, from creation to worker execution, retry handling, and dead-letter queue transition.

```mermaid
sequenceDiagram
    autonumber
    participant App as Application Client
    participant API as FastAPI Backend
    participant DB as Postgres Database
    participant Worker as Worker Runner
    participant AI as AI Failure Analyzer

    App->>API: POST /jobs (Queue ID, Payload, Retries)
    API->>DB: INSERT INTO jobs (status='queued', payload, max_retries)
    DB-->>API: Job ID
    API-->>App: Job enqueued successfully (HTTP 201)

    Note over Worker, DB: Worker Poll Cycle (Lock-Free Claiming)
    Worker->>DB: BEGIN TRANSACTION
    Worker->>DB: SELECT * FROM jobs WHERE status='queued' FOR UPDATE SKIP LOCKED LIMIT 1
    alt No Jobs Available
        DB-->>Worker: Empty ResultSet
        Worker->>DB: ROLLBACK
    else Job Claimed
        DB-->>Worker: Return Job Record
        Worker->>DB: UPDATE jobs SET status='running', started_at=now WHERE id=Job_ID
        Worker->>DB: COMMIT TRANSACTION
        
        Note over Worker: Execute Asynchronous Function
        Worker->>Worker: Run Task Logic

        alt Execution Successful
            Worker->>DB: UPDATE jobs SET status='success', progress=100, completed_at=now
            Worker->>DB: INSERT INTO job_executions (job_id, status='success', duration_ms)
        else Execution Failed (Error Raised)
            Worker->>Worker: Capture Stack Trace
            alt Retries Available (retries_count < max_retries)
                Worker->>DB: UPDATE jobs SET status='queued', retries_count=retries_count+1, run_at=now+backoff
                Worker->>DB: INSERT INTO job_executions (job_id, status='failed', error_message)
            else Retries Exhausted
                Worker->>DB: UPDATE jobs SET status='failed', completed_at=now
                Worker->>AI: Analyze traceback with failure details
                AI-->>Worker: Return Category, Cause, and Remedy DTO
                Worker->>DB: INSERT INTO job_executions (job_id, status='failed', error_message, ai_analysis)
                Worker->>DB: INSERT INTO dead_letter_queues (job_id, reason, payload)
            end
        end
    end
```

---

## 7. Worker Communication Flow

Workers act as decoupled, stateless runners. They register and report metrics independently.

```mermaid
sequenceDiagram
    autonumber
    participant Worker as Worker Runner
    participant DB as Postgres Database
    participant API as WebSocket Server
    participant UI as Observability Dashboard

    Worker->>DB: INSERT INTO workers (name, hostname, status='idle')
    DB-->>Worker: Worker registered successfully
    
    loop Heartbeat Loop (every 5 seconds)
        Worker->>Worker: Query OS Memory & CPU Load
        Worker->>DB: INSERT INTO worker_heartbeats (worker_id, status, cpu, memory, active_jobs_count)
        Worker->>DB: UPDATE workers SET last_heartbeat=now, status=current_status
    end

    loop WebSocket Broadcast (every 2 seconds)
        API->>DB: Fetch active worker statuses and metrics
        DB-->>API: Raw worker metrics data
        API->>UI: Broadcast payload to active subscribers ("observability:{org_id}")
    end
```

---

## 8. Scheduler Flow

AetherFlow manages interval and cron schedules inside the database. A background evaluator loop triggers the job creation on schedule intervals.

```mermaid
sequenceDiagram
    autonumber
    participant UI as Frontend Scheduler
    participant API as FastAPI Backend
    participant DB as Postgres Database
    participant Scheduler as Background Evaluator Loop

    UI->>API: POST /schedules (project_id, cron_expression, job_payload)
    API->>DB: INSERT INTO scheduled_jobs (trigger_type='cron', cron_expression, is_active=true)
    DB-->>API: Scheduled Job ID
    API-->>UI: Schedule registered successfully

    loop Schedule Poll Interval (every 10 seconds)
        Scheduler->>DB: SELECT * FROM scheduled_jobs WHERE is_active=true AND next_run_time <= now FOR UPDATE SKIP LOCKED
        DB-->>Scheduler: List of pending schedules
        loop For Each Pending Schedule
            Scheduler->>Scheduler: Evaluate next runtime using cron-parser
            Scheduler->>DB: INSERT INTO jobs (queue_id, name, status='queued', payload)
            Scheduler->>DB: UPDATE scheduled_jobs SET next_run_time=calculated_time, last_run_time=now
        end
    end
```

---

## 9. Key Database Architectural Patterns

### 1. Lock-Free Skipping (`SKIP LOCKED`)
AetherFlow uses the PostgreSQL concurrency feature `SELECT ... FOR UPDATE SKIP LOCKED`.
- **How it works**: When a worker attempts to claim a task, it issues a SELECT query that locks matching rows. If a row is already locked by another worker transaction, instead of waiting (which causes blocking and bottlenecks), the database engine skips the row and returns the next unlocked row.
- **Benefit**: Multi-core worker nodes scale horizontally without hitting thread contentions, deadlocks, or task double-claiming bugs.

### 2. Tenancy Partitioning
All primary models (`Project`, `Queue`, `Job`, `Workflow`, `ScheduledJob`, `Notification`, `AuditLog`) resolve back to an `Organization` relationship.
- Every API controller extracts the `organization_id` (either from the JWT token claims or a route parameter) and appends a `WHERE organization_id = [ID]` predicate to every query.
- This guarantees data isolation between organizations.
