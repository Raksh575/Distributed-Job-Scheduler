# AetherFlow API Documentation

This document describes all REST and WebSocket endpoints exposed by the AetherFlow backend application. All request and response bodies use JSON format, except where binary/streaming responses are explicitly indicated.

---

## Global API Configuration

- **Development Base URL**: `http://localhost:8000/api/v1`
- **WebSocket URL**: `ws://localhost:8000/ws`
- **Interactive OpenAPI (Swagger) Docs**: `http://localhost:8000/docs`
- **Rate Limit**: Max 120 requests/minute per client IP (sliding-window limit). Excess requests receive `429 Too Many Requests`.

---

## 1. System Health Checks

### Endpoint: General Health Check
- **URL**: `/health`
- **HTTP Method**: `GET`
- **Description**: Verifies if the service is running.
- **Authentication Required**: No
- **Roles Allowed**: None (Public)
- **Response Body**:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "environment": "development"
  }
  ```
- **Status Codes**: 
  - `200 OK`: System is healthy.

---

### Endpoint: Liveness Probe
- **URL**: `/health/liveness`
- **HTTP Method**: `GET`
- **Description**: Fast check used by container orchestrators to confirm process responsiveness.
- **Authentication Required**: No
- **Roles Allowed**: None (Public)
- **Response Body**:
  ```json
  {
    "status": "alive"
  }
  ```
- **Status Codes**: 
  - `200 OK`: Process is alive.

---

### Endpoint: Readiness Probe
- **URL**: `/health/readiness`
- **HTTP Method**: `GET`
- **Description**: Evaluates backend database connectivity.
- **Authentication Required**: No
- **Roles Allowed**: None (Public)
- **Response Body**:
  ```json
  {
    "status": "ready",
    "database": "connected"
  }
  ```
- **Status Codes**: 
  - `200 OK`: Database connected and ready.
  - `503 Service Unavailable`: Database ping fails.
- **Error Response Example**:
  ```json
  {
    "detail": "Database connectivity failed: Connection refused"
  }
  ```

---

## 2. Authentication

### Endpoint: Register Account
- **URL**: `/auth/register`
- **HTTP Method**: `POST`
- **Description**: Creates a new user profile.
- **Authentication Required**: No
- **Validation Rules**:
  - `email`: Must be a valid email string.
  - `password`: Minimum 8 characters, containing at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special character.
- **Request Body**:
  ```json
  {
    "email": "developer@catalyst.io",
    "password": "Password123!",
    "first_name": "Dev",
    "last_name": "User",
    "username": "devuser"
  }
  ```
- **Response Body**:
  ```json
  {
    "id": "c9a28b4d-ef01-4234-9abc-123456789abc",
    "email": "developer@catalyst.io",
    "first_name": "Dev",
    "last_name": "User",
    "username": "devuser",
    "phone": null,
    "country": null,
    "timezone": "UTC",
    "profile_picture": null,
    "is_verified": false,
    "is_active": true,
    "created_at": "2026-07-03T18:00:00Z"
  }
  ```
- **Status Codes**: 
  - `201 Created`: User successfully registered.
  - `400 Bad Request`: Email already exists, username exists, or password requirements are not met.

---

### Endpoint: User Login (Token Generation)
- **URL**: `/auth/token`
- **HTTP Method**: `POST`
- **Description**: Verifies credentials and generates access/refresh tokens.
- **Authentication Required**: No
- **Request Headers**: `Content-Type: application/x-www-form-urlencoded`
- **Request Body** (Form Data):
  - `username`: (string, email)
  - `password`: (string)
- **Response Body**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "a8f7c9e1-321a-4d2b-9c8f-287eac931234",
    "token_type": "bearer"
  }
  ```
- **Status Codes**: 
  - `200 OK`: Successful login.
  - `401 Unauthorized`: Invalid credentials.

---

### Endpoint: Refresh Session
- **URL**: `/auth/refresh`
- **HTTP Method**: `POST`
- **Description**: Rotates refresh tokens and returns a new access/refresh pair.
- **Authentication Required**: No
- **Request Body**:
  ```json
  {
    "refresh_token": "a8f7c9e1-321a-4d2b-9c8f-287eac931234"
  }
  ```
- **Response Body**: Same as `/auth/token` response.
- **Status Codes**: 
  - `200 OK`: Session rotated successfully.
  - `401 Unauthorized`: Expired or revoked refresh token.

---

### Endpoint: User Logout
- **URL**: `/auth/logout`
- **HTTP Method**: `POST`
- **Description**: Revokes the provided refresh token and terminates the active session.
- **Authentication Required**: No
- **Request Body**:
  ```json
  {
    "refresh_token": "a8f7c9e1-321a-4d2b-9c8f-287eac931234"
  }
  ```
- **Status Codes**: 
  - `204 No Content`: Logged out.

---

### Endpoint: Change Password
- **URL**: `/auth/change-password`
- **HTTP Method**: `POST`
- **Description**: Changes user password after validating current password.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body**:
  ```json
  {
    "old_password": "OldPassword1!",
    "new_password": "NewPassword2!"
  }
  ```
- **Status Codes**: 
  - `204 No Content`: Password changed.
  - `401 Unauthorized`: Invalid authorization or old password verification fails.

---

## 3. Users

### Endpoint: Fetch My Profile
- **URL**: `/users/me`
- **HTTP Method**: `GET`
- **Description**: Retrieves profile details of the active user.
- **Authentication Required**: Yes (Bearer Token)
- **Response Body**: Same as `/auth/register` response.

---

### Endpoint: Update Profile Parameters
- **URL**: `/users/me`
- **HTTP Method**: `PATCH`
- **Description**: Partially updates profile properties.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body**:
  ```json
  {
    "first_name": "DevEdited",
    "phone": "+15550199",
    "timezone": "America/New_York"
  }
  ```
- **Response Body**: Returns the updated UserResponse.

---

### Endpoint: Fetch My Organizations
- **URL**: `/users/me/organizations`
- **HTTP Method**: `GET`
- **Description**: Lists all organizations where the active user is a member.
- **Authentication Required**: Yes (Bearer Token)
- **Response Body**:
  ```json
  [
    {
      "id": "e4b11e1f-0c76-48ff-92d1-a7c6e8944d04",
      "name": "Catalyst",
      "slug": "catalyst",
      "description": "Enterprise Cloud Systems Workspace",
      "logo": null,
      "plan": "Enterprise",
      "status": "Active",
      "created_at": "2026-07-03T18:00:00Z",
      "version": 1
    }
  ]
  ```

---

## 4. Organizations & Projects

### Endpoint: Create Organization
- **URL**: `/organizations`
- **HTTP Method**: `POST`
- **Description**: Registers a new organization. Creator is set as Owner.
- **Authentication Required**: Yes (Bearer Token)
- **Request Body**:
  ```json
  {
    "name": "Catalyst",
    "slug": "catalyst",
    "description": "Enterprise Cloud Systems Workspace"
  }
  ```
- **Response Body**: Returns the newly created organization details (OrgResponse).

---

### Endpoint: Fetch Organization Details
- **URL**: `/organizations/{org_id}`
- **HTTP Method**: `GET`
- **Description**: Retrieves details for the specified organization.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer`, `Viewer` (requires `metrics_access`)
- **Status Codes**: 
  - `200 OK`: Returns OrgResponse.
  - `403 Forbidden`: User does not belong to the organization.

---

### Endpoint: Create Project
- **URL**: `/organizations/{org_id}/projects`
- **HTTP Method**: `POST`
- **Description**: Registers a new project workspace under an organization.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin` (requires `org_management`)
- **Request Body**:
  ```json
  {
    "name": "AI Document Processing Platform",
    "slug": "ai-doc-processing",
    "description": "Distributed document classification engines.",
    "environment": "production"
  }
  ```
- **Response Body**:
  ```json
  {
    "id": "b1812ce3-a302-42dd-9230-707fba2863df",
    "name": "AI Document Processing Platform",
    "slug": "ai-doc-processing",
    "description": "Distributed document classification engines.",
    "environment": "production",
    "status": "Active",
    "organization_id": "e4b11e1f-0c76-48ff-92d1-a7c6e8944d04",
    "created_at": "2026-07-03T18:05:00Z",
    "version": 1
  }
  ```

---

### Endpoint: List Projects
- **URL**: `/organizations/{org_id}/projects`
- **HTTP Method**: `GET`
- **Description**: Lists active projects in the organization. Auto-creates a default project if none exist.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer`, `Viewer` (requires `metrics_access`)

---

## 5. Memberships

### Endpoint: Add Organization Member
- **URL**: `/organizations/{org_id}/members`
- **HTTP Method**: `POST`
- **Description**: Invites and assigns a user to the organization.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin` (requires `user_management`)
- **Request Body**:
  ```json
  {
    "email": "invited_user@catalyst.io",
    "role": "Developer"
  }
  ```
- **Response Body**:
  ```json
  {
    "id": "d0411e1f-0c76-48ff-92d1-a7c6e8944d04",
    "user_id": "c9a28b4d-ef01-4234-9abc-123456789abc",
    "organization_id": "e4b11e1f-0c76-48ff-92d1-a7c6e8944d04",
    "role": "Developer",
    "user": {
      "id": "c9a28b4d-ef01-4234-9abc-123456789abc",
      "email": "invited_user@catalyst.io",
      "first_name": "Invited",
      "last_name": "User",
      "username": "inviteduser",
      "is_verified": true,
      "is_active": true,
      "created_at": "2026-07-03T18:00:00Z"
    },
    "created_at": "2026-07-03T18:10:00Z"
  }
  ```

---

## 6. Queues

### Endpoint: Create Processing Queue
- **URL**: `/organizations/{org_id}/projects/{project_id}/queues`
- **HTTP Method**: `POST`
- **Description**: Creates a new concurrency and rate-limited processing queue.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer` (requires `queue_management`)
- **Request Body**:
  ```json
  {
    "name": "OCR_Queue",
    "priority": 10,
    "concurrency_limit": 15,
    "rate_limit": 50
  }
  ```
- **Response Body**:
  ```json
  {
    "id": "e812ce3a-3a02-42dd-9230-707fba2863df",
    "project_id": "b1812ce3-a302-42dd-9230-707fba2863df",
    "name": "OCR_Queue",
    "is_active": true,
    "is_paused": false,
    "priority": 10,
    "concurrency_limit": 15,
    "rate_limit": 50,
    "created_at": "2026-07-03T18:12:00Z"
  }
  ```

---

### Endpoint: Pause Queue
- **URL**: `/organizations/{org_id}/queues/{queue_id}/pause`
- **HTTP Method**: `POST`
- **Description**: Pauses job processing on a queue. Workers will skip enqueued tasks on this queue.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer` (requires `queue_management`)

---

## 7. Jobs

### Endpoint: Submit Background Job
- **URL**: `/organizations/{org_id}/queues/{queue_id}/jobs`
- **HTTP Method**: `POST`
- **Description**: Enqueues a job payload for execution.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer` (requires `job_management`)
- **Request Body**:
  ```json
  {
    "name": "ExtractDocumentMetadata",
    "payload": {
      "doc_id": "doc-9921",
      "s3_path": "s3://catalyst-documents/invoices/9921.pdf"
    },
    "parent_id": null,
    "delay_seconds": 0,
    "priority": 5,
    "max_retries": 3,
    "timeout": 300
  }
  ```
- **Response Body**:
  ```json
  {
    "id": "f812ce3a-3a02-42dd-9230-707fba2863df",
    "queue_id": "e812ce3a-3a02-42dd-9230-707fba2863df",
    "name": "ExtractDocumentMetadata",
    "status": "queued",
    "payload": {
      "doc_id": "doc-9921",
      "s3_path": "s3://catalyst-documents/invoices/9921.pdf"
    },
    "result": null,
    "progress": 0,
    "error_message": null,
    "run_at": "2026-07-03T18:15:00Z",
    "priority": 5,
    "max_retries": 3,
    "retries_count": 0,
    "timeout": 300,
    "parent_id": null,
    "workflow_id": null,
    "created_at": "2026-07-03T18:15:00Z"
  }
  ```
- **Status Codes**: 
  - `202 Accepted`: Job was successfully queued.

---

### Endpoint: Fetch Job Logs & Executions
- **URL**: `/organizations/{org_id}/jobs/{job_id}/logs`
- **HTTP Method**: `GET`
- **Description**: Retrieves execution history, durations, node telemetry, stdout messages, and AI failure summaries for a job.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer`, `Viewer` (requires `metrics_access`)
- **Response Body**:
  ```json
  [
    {
      "execution_id": "3b12ce3a-3a02-42dd-9230-707fba2863df",
      "worker_id": "bcb57c96-8688-48da-bfc8-5628cdc1dfe9",
      "status": "failed",
      "started_at": "2026-07-03T18:15:02Z",
      "completed_at": "2026-07-03T18:15:03Z",
      "error_message": "HTTP Request Timeout Exception",
      "duration_ms": 1500,
      "ai_analysis": {
        "failure_summary": "Network / Outbound request failed due to connection timeout.",
        "root_cause": "The external service API endpoint took too long to respond.",
        "remedy_steps": [
          "Verify target API uptime.",
          "Increase request timeout variables."
        ],
        "retry_recommendation": true,
        "estimated_recovery": "5 minutes"
      },
      "logs": [
        {
          "level": "info",
          "message": "Task claimed by node worker-prod-01.",
          "timestamp": "2026-07-03T18:15:02Z"
        },
        {
          "level": "error",
          "message": "Execution halted: HTTP Request Timeout Exception",
          "timestamp": "2026-07-03T18:15:03Z"
        }
      ]
    }
  ]
  ```

---

## 8. Workflows (DAGs)

### Endpoint: Submit DAG Workflow
- **URL**: `/organizations/{org_id}/projects/{project_id}/workflows`
- **HTTP Method**: `POST`
- **Description**: Enqueues multiple dependent jobs represented as a Directed Acyclic Graph (DAG).
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer` (requires `job_management`)
- **Request Body**:
  ```json
  {
    "name": "Invoicing Pipeline",
    "nodes": [
      {
        "temp_id": "fetch-data",
        "name": "FetchBillingData",
        "queue_id": "e812ce3a-3a02-42dd-9230-707fba2863df",
        "payload": { "billing_month": "July" },
        "dependencies": [],
        "priority": 1,
        "max_retries": 2
      },
      {
        "temp_id": "generate-invoice",
        "name": "GeneratePDFInvoice",
        "queue_id": "e812ce3a-3a02-42dd-9230-707fba2863df",
        "payload": {},
        "dependencies": ["fetch-data"],
        "priority": 1,
        "max_retries": 3
      }
    ]
  }
  ```
- **Response Body**:
  ```json
  {
    "id": "a9a28b4d-ef01-4234-9abc-123456789abc",
    "project_id": "b1812ce3-a302-42dd-9230-707fba2863df",
    "name": "Invoicing Pipeline",
    "status": "running",
    "created_at": "2026-07-03T18:20:00Z",
    "jobs": []
  }
  ```

---

## 9. Dead-Letter Queue (DLQ)

### Endpoint: Fetch DLQ Records
- **URL**: `/organizations/{org_id}/dlq`
- **HTTP Method**: `GET`
- **Description**: Lists jobs that failed and exhausted all configured retry attempts.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer`, `Viewer` (requires `metrics_access`)
- **Response Body**:
  ```json
  [
    {
      "job_id": "f812ce3a-3a02-42dd-9230-707fba2863df",
      "failed_at": "2026-07-03T18:15:03Z",
      "reason": "HTTP Request Timeout Exception: Connection lost to microservice node.",
      "job": {
        "id": "f812ce3a-3a02-42dd-9230-707fba2863df",
        "name": "ExtractDocumentMetadata",
        "status": "failed",
        "payload": {
          "doc_id": "doc-9921",
          "s3_path": "s3://catalyst-documents/invoices/9921.pdf"
        },
        "progress": 0,
        "error_message": "HTTP Request Timeout Exception: Connection lost to microservice node.",
        "run_at": "2026-07-03T18:15:00Z",
        "priority": 5,
        "max_retries": 3,
        "retries_count": 3,
        "created_at": "2026-07-03T18:15:00Z"
      }
    }
  ]
  ```

---

### Endpoint: Replay DLQ Job
- **URL**: `/organizations/{org_id}/dlq/{job_id}/replay`
- **HTTP Method**: `POST`
- **Description**: Re-enqueues a quarantined failed job, resetting retry counters and clearing error statuses.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer` (requires `job_management`)
- **Response Body**: Returns the updated active JobResponse with `status` reset to `queued`.

---

## 10. Scheduled Jobs

### Endpoint: Create Scheduled Trigger
- **URL**: `/organizations/{org_id}/projects/{project_id}/schedules`
- **HTTP Method**: `POST`
- **Description**: Registers a new recurring job trigger (cron-based or interval-based).
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer` (requires `queue_management`)
- **Request Body**:
  ```json
  {
    "name": "MidnightDatabaseCleanup",
    "trigger_type": "cron",
    "cron_expression": "0 0 * * *",
    "interval_seconds": null,
    "target_queue_id": "e812ce3a-3a02-42dd-9230-707fba2863df",
    "job_name": "DBCleanupTask",
    "job_payload": { "purge_retention_days": 30 }
  }
  ```
- **Response Body**:
  ```json
  {
    "id": "c1812ce3-a302-42dd-9230-707fba2863df",
    "project_id": "b1812ce3-a302-42dd-9230-707fba2863df",
    "name": "MidnightDatabaseCleanup",
    "trigger_type": "cron",
    "cron_expression": "0 0 * * *",
    "interval_seconds": null,
    "target_queue_id": "e812ce3a-3a02-42dd-9230-707fba2863df",
    "job_name": "DBCleanupTask",
    "job_payload": { "purge_retention_days": 30 },
    "is_active": true,
    "next_run_time": "2026-07-04T00:00:00Z",
    "created_at": "2026-07-03T18:25:00Z"
  }
  ```

---

## 11. Observability, Logs & Telemetry

### Endpoint: Fetch Dashboard Metrics
- **URL**: `/organizations/{org_id}/dashboard-metrics`
- **HTTP Method**: `GET`
- **Description**: Retrieves aggregate performance metrics (system throughput, queue sizes, active workers).
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer`, `Viewer` (requires `metrics_access`)
- **Response Body**:
  ```json
  {
    "active_workers_count": 4,
    "queued_jobs_count": 3,
    "running_jobs_count": 2,
    "failed_jobs_count": 2,
    "completed_jobs_count": 50,
    "queue_throughput_per_min": 12.5,
    "worker_utilization_rate": 78.4
  }
  ```

---

### Endpoint: Fetch System Logs
- **URL**: `/organizations/{org_id}/observability/logs`
- **HTTP Method**: `GET`
- **Description**: Paginated logs search. Reads structured JSON app logs from files.
- **Authentication Required**: Yes (Bearer Token)
- **Query Parameters**:
  - `category`: Filter by log domain (e.g., `worker`, `api`, `scheduler`).
  - `level`: Filter by log severity (`INFO`, `WARN`, `ERROR`).
  - `search_query`: Text string search.
  - `skip`: (integer, default 0)
  - `limit`: (integer, default 50)
- **Response Body**:
  ```json
  {
    "logs": [
      {
        "timestamp": "2026-07-03T18:22:15Z",
        "level": "INFO",
        "category": "worker",
        "message": "Node worker-prod-02 polling for tasks."
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 50
  }
  ```

---

### Endpoint: Download System Logs
- **URL**: `/organizations/{org_id}/observability/logs/download`
- **HTTP Method**: `GET`
- **Description**: Returns structured system log history as a downloadable file attachment.
- **Authentication Required**: Yes (Bearer Token)
- **Response Type**: `text/plain` file stream attachment (`Content-Disposition: attachment; filename=djs_observability_logs_[TIMESTAMP].log`).

---

## 12. CSV Exports

### Endpoint: Export Executions Report
- **URL**: `/organizations/{org_id}/exports/executions`
- **HTTP Method**: `GET`
- **Description**: Streams history of the 1000 most recent execution runs as a CSV file.
- **Authentication Required**: Yes (Bearer Token)
- **Response Type**: `text/csv` stream attachment (`djs_executions_telemetry.csv`).

---

## 13. Simulator Controls

### Endpoint: Trigger Simulated Load
- **URL**: `/organizations/{org_id}/simulator/trigger`
- **HTTP Method**: `POST`
- **Description**: Starts a background daemon thread that generates simulated task traffic.
- **Authentication Required**: Yes (Bearer Token)
- **Roles Allowed**: `Owner`, `Admin`, `Developer` (requires `queue_management`)
- **Response Body**:
  ```json
  {
    "status": "started",
    "message": "Job ingestion simulator active."
  }
  ```

---

## 14. WebSocket Telemetry Interface

- **WebSocket Route URL**: `/ws`
- **Description**: Real-time event gateway for pushing real-time metrics updates and system alerts to active dashboards.

### Subscription Actions
Clients send JSON payloads to subscribe or unsubscribe from specific event topics.

#### 1. Subscribe to Global Metrics Broadcast
```json
{
  "action": "subscribe",
  "topic": "metrics"
}
```
- **Server Response**:
  ```json
  {
    "event": "subscribed",
    "topic": "metrics"
  }
  ```
- **Broadcast Events**: Pushes a stats payload every 2 seconds containing aggregate job execution counts.

#### 2. Subscribe to Organizational Observability Stream
```json
{
  "action": "subscribe",
  "topic": "observability:e4b11e1f-0c76-48ff-92d1-a7c6e8944d04"
}
```
- **Server Response**:
  ```json
  {
    "event": "subscribed",
    "topic": "observability:e4b11e1f-0c76-48ff-92d1-a7c6e8944d04"
  }
  ```
- **Broadcast Events**: Pushes granular CPU, memory, queue length data, and live alert toasts (e.g., node offline events).
