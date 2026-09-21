# AetherFlow Automated Testing Documentation

This document describes AetherFlow's test architecture, tooling configurations, verification guides, mock systems, and execution procedures for both the backend (FastAPI) and frontend (React).

---

## 1. Test Architecture Overview

AetherFlow uses a dual-layered automated testing framework designed to validate business logic, transaction lifecycles, UI components, state management, and network communication layers:

```
                  +-----------------------------------+
                  |      AetherFlow Test Suite        |
                  +-----------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|  Backend (Pytest)     |                       |   Frontend (Vitest)   |
|  - Unit & Integration |                       |   - Component Tests   |
|  - Mock DB Sessions   |                       |   - Zustand Store Mock|
|  - Async IO Tests     |                       |   - React Test Lib    |
+-----------------------+                       +-----------------------+
```

### Coverage Goals:
- **Target**: Maintain $\ge 90\%$ test coverage on critical business modules, specifically within the service classes (`job_service.py`, `workflow_service.py`, `dlq_service.py`) and auth controllers.

---

## 2. Backend Testing Framework (Pytest)

The backend uses `pytest` alongside the asynchronous extension `pytest-asyncio` to execute concurrent tests without database connection blocks.

### Test Files Location:
All python test files reside inside the `backend/tests/` directory:
- `backend/tests/conftest.py`: Defines shared fixtures, factory helpers, and mock sessions.
- `backend/tests/test_auth.py`: Validates password policies and user registration checks.
- `backend/tests/test_failure_analyzer.py`: Asserts AI error categorizations and fixes.
- `backend/tests/test_job_service.py`: Asserts retry backoff calculations, re-enqueueing processes, and state changes.

### Key Fixtures & Mocks (conftest.py):
The backend isolates tests from Supabase by utilizing database session mocks:
- `mock_db_session`: An asynchronous SQLAlchemy session mock built using `unittest.mock.AsyncMock`. It intercepts commands like `.execute()`, `.add()`, and `.flush()`, returning dummy data or success logs.
- `mock_user`: Returns a verified user model to simulate logged-in request contexts.
- `mock_job`: Returns a sample job model with a JSON configuration payload.

### Backend Test Execution Guide:
1. Navigate to the `backend` directory and activate the virtual environment:
   ```bash
   cd backend
   # On Windows:
   .\venv\Scripts\activate
   ```
2. Execute the full test suite with verbose outputs:
   ```bash
   pytest -v
   ```
3. Generate a code coverage report:
   ```bash
   pytest --cov=app tests/ --cov-report=term-missing
   ```

---

## 3. Frontend Testing Framework (Vitest & RTL)

The frontend uses `Vitest` as the test runner and `React Testing Library (RTL)` to validate user actions, forms, routing, and UI rendering.

### Test Files Location:
All frontend tests are located inside the `frontend/src/tests/` directory:
- `frontend/src/tests/auth.test.ts`: Validates the global auth Zustand store (`useAuth`), checking token initialization, authentication states, and logout redirection logic.

### Globals & Storage Mocking:
Because Vitest executes within a Node.js context, browser APIs (such as `localStorage` and `window.location`) are mocked globally at the test runtime:
- `localStorage`: Implements a memory key-value store, allowing assertions on auth token retention (`djs_access_token`).
- `window.location`: Intercepts redirect actions (e.g. forwarding unauthenticated users to `/login`).
- `vi.mock`: Spies on REST services (such as `authService.logout`), returning mock promises.

### Frontend Test Execution Guide:
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Run the test suite:
   ```bash
   npm run test
   ```
3. Run tests in watch mode for development:
   ```bash
   npx vitest
   ```
4. Generate a coverage report:
   ```bash
   npx vitest run --coverage
   ```

---

## 4. Test Implementation Details

### Example 1: Asynchronous Service Test (Pytest)
This integration test validates that when a dead-letter job is replayed, the service correctly resets the retry counters and status values inside a database transaction:
```python
@pytest.mark.asyncio
async def test_job_replay(mock_db_session):
    job_id = uuid.uuid4()
    job = Job(
        id=job_id,
        status="failed",
        retries_count=3,
        payload={}
    )
    
    service = JobService(mock_db_session)
    service.get_job = AsyncMock(return_value=job)
    service.job_repo.update = AsyncMock(return_value=job)
    
    replayed = await service.replay_job(job_id)
    
    # Assertions
    assert service.job_repo.update.called
    update_data = service.job_repo.update.call_args[0][1]
    assert update_data["status"] == "queued"
    assert update_data["retries_count"] == 0
    assert update_data["error_message"] is None
```

### Example 2: Frontend State Management Test (Vitest)
This test validates that the Zustand store manages state variables and interacts with browser caches as expected:
```typescript
it("should store token and email on login", () => {
  useAuth.getState().login("mock-token-abc", "mock-refresh-token", "user@corp.com", "user-id-123", "User Name");
  
  const state = useAuth.getState();
  expect(state.isAuthenticated).toBe(true);
  expect(state.token).toBe("mock-token-abc");
  expect(state.userEmail).toBe("user@corp.com");
  expect(localStorage.getItem("djs_access_token")).toBe("mock-token-abc");
});
```

---

## 5. Mocking Strategy & Conventions

1. **Database Session Mocking**:
   Always mock session commits (`await db.commit()`) and transaction sessions (`async with session.begin()`) using `AsyncMock` to ensure no connection leakage occurs during tests.
2. **API Endpoint Security Mocking**:
   Mock `get_current_user` and `RequirePermission` dependencies inside `app.middleware.auth` using FastAPI dependency overrides:
   ```python
   app.dependency_overrides[get_current_user] = lambda: mock_user_instance
   ```
3. **UI Axios Client Mocking**:
   Use `vitest` mocks (`vi.mock`) to intercept global axios service instances (`services/api.ts`) to return dummy payload data rather than sending HTTP queries to the FastAPI port.
