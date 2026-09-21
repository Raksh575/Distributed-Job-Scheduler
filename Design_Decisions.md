# AetherFlow Design Decisions & Architectural Trade-offs

This document outlines the core design decisions, technology choices, architectural patterns, and trade-offs made during the implementation of the AetherFlow platform.

---

## 1. Project Goals

AetherFlow was built to satisfy the following enterprise requirements:
- **Low Operational Overhead**: Leverage existing relational database engines for transactional queue management rather than introducing specialized in-memory message brokers.
- **Strict Data Consistency**: Ensure that business logic state updates and job scheduling events occur within a single database transaction, resolving the "dual-write" problem.
- **High Concurrency and Scalability**: Support lock-free concurrent worker threads that scale horizontally across separate execution environments.
- **Premium User Experience**: Render a sub-second, real-time dashboard UI displaying live metrics, worker health gauges, active notifications, and job execution logs.

---

## 2. Technology Stack & Architecture Choice

### Why FastAPI?
FastAPI was selected as the backend API framework because:
1. **Asynchronous by Default**: FastAPI is built directly on ASGI (Starlette), enabling concurrent network connections (REST and WebSockets) using minimal system resources.
2. **Speed**: Competes with Node.js and Go in throughput performance benchmarks.
3. **Type Safety & Auto-Documentation**: Leverages Python type hints and Pydantic to validate request parameters, generating interactive OpenAPI (Swagger) documentation automatically.

### Why React?
React was selected for the frontend application because:
1. **Declarative Component Model**: Enables composition of complex, reusable UI elements (e.g., dynamic area charts, glassmorphism telemetry cards, DAG nodes).
2. **Virtual DOM**: Optimized DOM manipulation, keeping the UI highly responsive when receiving high-frequency WebSocket updates.
3. **Ecosystem Maturity**: Provides robust libraries for interactive visualizations (Recharts) and transitions (Framer Motion).

### Why TypeScript?
TypeScript was adopted over vanilla JavaScript to:
1. **Enforce Interface Contracts**: Prevents runtime type mismatch bugs between backend DTO schemas and frontend component properties.
2. **Improve Developer Tooling**: Enables autocompletion and compile-time validation.
3. **Ease Maintenance**: Simplifies refactoring of large state handlers and visual components.

### Why PostgreSQL (Supabase)?
PostgreSQL is the core database of AetherFlow. Supabase was chosen as the hosting provider because:
1. **ACID Transaction Compliance**: Essential for tracking critical execution states (e.g., job claiming, state transitions, audit logging).
2. **Advanced Concurrency Controls**: Provides `SELECT ... FOR UPDATE SKIP LOCKED` syntax, enabling lock-free, multi-worker queues.
3. **Rich Data Types**: Inherent support for `JSONB` indexes, which is key for arbitrary job payloads, metadata results, and AI failure summaries.
4. **Managed Cloud Infrastructure**: High availability, built-in backups, connection pooling, and secure API keys.

### Why SQLAlchemy 2.0?
SQLAlchemy is Python's leading Object-Relational Mapper (ORM). Version 2.0 was selected to:
1. **Support Asynchronous SQL**: Integrates with `asyncpg` to run database sessions asynchronously, preventing blocker bottlenecks on database queries.
2. **Provide Strong Type Checking**: Employs Declarative Mapping (`Mapped[...]` and `mapped_column`) to align model schemas with IDE validation tools.
3. **Deliver Precise Query Control**: Allows developers to write complex SQL statements (such as concurrent locks) using clean Python classes.

### Why JWT Authentication?
JSON Web Tokens (JWT) are used for user verification to:
1. **Keep the Backend Stateless**: The API gateway decrypts and validates claims locally without executing database checks on every request, enabling horizontal scalability.
2. **Incorporate Tenant IDs**: Embeds the active user's roles and tenant identifier (`organization_id`) directly in the cryptographically signed payload for fast RBAC checks.
3. **Support Rotation Pattern**: Integrates with database-backed cryptographic refresh tokens to rotate expired access credentials and invalidate revoked sessions.

### Why the Repository Pattern?
The Repository Pattern wraps database query logic inside dedicated modules (e.g., `UserRepository`, `JobRepository`):
1. **Isolates Database Concerns**: Decouples the service business layer from ORM query structures.
2. **Simplifies Unit Testing**: Enables mocking of database accesses during service testing, bypassing database connections.
3. **Standardizes Common Queries**: Centralizes basic operations (create, update, retrieve, soft-delete).

### Why the Service Layer?
The Service Layer houses the core business logic of AetherFlow (e.g., `JobService`, `QueueService`):
1. **Encapsulates Operations**: Ensures API route controllers remain slim, focusing solely on handling HTTP requests/responses and request validation.
2. **Orchestrates Transactions**: Manages complex actions (e.g., updating a job, updating worker active counts, and broadcasting a WebSocket alert) in a single workflow.

### Why Clean Architecture?
Dividing the project into distinct layers (API Routers $\rightarrow$ Services $\rightarrow$ Repositories $\rightarrow$ DB Models) enforces the **Dependency Inversion Principle**:
1. High-level policies (business workflows) are decoupled from low-level details (HTTP parsers or SQL query logic).
2. Codebase components can be refactored independently, minimizing regression bugs.

### Why AsyncIO?
Python's `asyncio` loop drives the FastAPI server, WebSocket handlers, and worker claim loops:
1. **Maximizes Concurrency**: Allows a single thread to manage thousands of concurrent active connections.
2. **Prevents Thread Overhead**: Operates on a single event loop, avoiding the thread contexts, locks, and memory overhead of multi-threaded web servers.

### Why APScheduler?
APScheduler is integrated as AetherFlow's background scheduling engine:
1. **Supports Multi-trigger Scheduling**: Parses standard Unix cron expressions and interval calculations.
2. **Integrates with Backend Lifespan**: Starts and stops alongside the FastAPI application process, avoiding the need for dedicated cron containers.

### Why WebSockets?
WebSockets establish a persistent, full-duplex TCP connection between the client browser and the API gateway:
1. **Eliminates Polling Overhead**: Allows the backend to immediately push status alerts or metrics without waiting for client requests.
2. **Reduces Network Bandwidth**: Minimizes HTTP header overhead on periodic updates.

### Why TanStack React Query?
React Query is used for caching client-side server state:
1. **Automates Server Syncing**: Features automatic background refetching, query polling, and caching.
2. **Reduces State Boilerplate**: Handles API loading, success, error, and caching states without manually dispatching custom actions.

### Why Zustand?
Zustand acts as AetherFlow's client-side client state store (e.g., active user profile, selected organization):
1. **Minimalist API**: Simple hook-based system without Redux's action/reducer boilerplate.
2. **Performant Rendering**: Components only re-render when their subscribed state slices change.

### Why Tailwind CSS?
Tailwind CSS provides utility-first classes, which were used to:
1. **Implement Premium Glassmorphic Designs**: Enables backdrop filter, drop-shadow, and layout styles to construct a sleek UI.
2. **Minimize CSS Bundle Size**: Eliminates unused styles during compilation.

---

## 3. Major Architectural Trade-offs

| Alternative Evaluated | Selected Technology | Trade-offs & Decisions |
| :--- | :--- | :--- |
| **FastAPI vs. Django** | **FastAPI** | Django provides a built-in admin panel and ORM but is traditionally synchronous. FastAPI was chosen for its high-performance async execution and native WebSockets support. |
| **React vs. Angular** | **React** | Angular provides a complete framework, but React's lightweight virtual DOM and Zustand integration were preferred for building a custom, fast dashboard. |
| **PostgreSQL vs. MySQL** | **PostgreSQL** | PostgreSQL was chosen due to its advanced `SKIP LOCKED` concurrency locks, native `JSONB` support, and robust transactional consistency. |
| **Supabase vs. Self-hosted Postgres** | **Supabase** | Self-hosting offers complete control but incurs maintenance overhead. Supabase provides a managed, high-performance database cluster with simple scaling paths. |
| **WebSockets vs. HTTP Polling** | **WebSockets** | Periodic HTTP polling is simpler but creates significant database and network overhead. WebSockets allow immediate, event-driven server pushes for active dashboards. |
| **JWT vs. Session Cookies** | **JWT** | Session cookies are easier to revoke but require a central session store. JWTs enable a stateless API gateway that simplifies horizontal scaling. |
| **Repository Pattern vs. Direct ORM** | **Repository Pattern** | Calling the ORM directly inside endpoints is faster to build but couples business logic with query logic. The Repository pattern ensures clean separation of concerns. |

---

## 4. Key Architectural Considerations

### Performance & Concurrency
AetherFlow achieves high performance through:
- **Lock-Free Queue Claiming**: `SELECT ... FOR UPDATE SKIP LOCKED` allows workers to grab tasks concurrently without blocking database transactions or causing deadlocks.
- **Async DB Drivers**: Using `asyncpg` prevents thread blocking during database queries, allowing FastAPI to handle other incoming API requests.

### Scalability
- **Horizontal Gateway Scaling**: The stateless nature of the FastAPI endpoints allows them to run behind load balancers.
- **Stateless Worker Nodes**: Workers poll the database independently. You can scale worker capacity simply by launching more worker processes.

### Maintainability
- **Type Integration**: TypeScript on the frontend and Pydantic on the backend minimize data format errors.
- **Layer Isolation**: Isolating route handling, business services, and database queries simplifies changes to individual layers.

### Security
- **Role-Based Access Control (RBAC)**: Middleware validates user permissions before exposing API routes.
- **Tenant Separation**: Database queries append organization-specific filters to isolate tenant data.
- **Secure Password Hashing**: Passwords are saved as Argon2 hashes.

### Reliability
- **Retry Policies**: Failed tasks automatically retry using configurable delay strategies (fixed, linear, or exponential).
- **Dead-Letter Queue (DLQ)**: Jobs that fail after all retries are quarantined for operator inspection, preventing infinite failing loops.
- **Worker Recovery**: The system periodically checks heartbeats and marks inactive workers as offline.

---

## 5. Future System Improvements

1. **Distributed Rate Limiting via Redis**: Migrating the sliding-window rate limiter from in-memory dictionary storage to a distributed Redis cluster for multi-node deployments.
2. **Dynamic Worker Auto-scaling**: Building an orchestrator that scales worker containers up or down based on queue load.
3. **Advanced DAG Workflows**: Adding support for parallel execution paths and conditional branch evaluation within the DAG engine.
