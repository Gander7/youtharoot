# Test Architecture

This project uses a proper separation between frontend and backend testing frameworks.

## Backend Tests (Python/pytest)

Located in: `backend/tests/`

**Framework:** pytest
**Purpose:** API logic, database operations, business logic, security

### Current Backend Tests:
- `test_backend_admin_security.py` - Admin user initialization security regression tests
- `api/test_*.py` - API endpoint tests  
- `models/test_*.py` - Model validation tests

### Running Backend Tests:
```bash
# From backend directory
cd backend/
python -m pytest tests/ -v

# Or with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

## Frontend Tests (JavaScript/Vitest)

Located in: `frontend/src/test/`

**Framework:** Vitest + React Testing Library
**Purpose:** Component behavior, user interactions, UI logic, frontend race conditions

### Current Frontend Tests:
- `components/ErrorBoundary.test.jsx` - Error boundary crash prevention
- `components/CheckIn.test.jsx` - Race condition fixes and checkout logic
- `integration/` - Integration tests (future)

### Testing (TDD Workflow)
```bash
# Run all tests
cd backend && python -m pytest tests/ -v && cd ../frontend && npm run test:run

# Watch mode for TDD
cd backend && python -m pytest tests/ --looponfail &  # Backend watch
cd frontend && npm test                                # Frontend watch
```

## Test Coverage Summary

### ✅ Completed Regression Tests

**Backend Security (Python):**
- [x] Admin user initialization security (12 tests)
- [x] Environment-based credential management
- [x] Bcrypt password hashing verification
- [x] PostgreSQL admin creation safety

**Frontend Stability (JavaScript):**
- [x] Error boundary crash prevention (19 tests)
- [x] Component error catching and recovery
- [x] Development vs production error display
- [x] Race condition elimination (12 tests)
- [x] Synchronous API response handling
- [x] Loading state management
- [x] setTimeout hack elimination

### 📋 Test Architecture Benefits

1. **Proper Tool Usage**: JavaScript tests for React components, Python tests for backend logic
2. **Fast Feedback**: Frontend tests run quickly with Vitest's hot reload
3. **Isolation**: Frontend and backend tests run independently
4. **Coverage**: Comprehensive regression protection for all critical fixes
5. **Maintainability**: Tests follow best practices for their respective ecosystems

### 🎯 Test Standards

**All tests follow:**
- AAA pattern (Arrange-Act-Assert)
- Descriptive naming: `MethodUnderTest_StateUnderTest_ExpectedBehaviour`
- Proper mocking and isolation
- Constants instead of magic strings
- Parallel execution capability

## Future Test Areas

### High Priority:
- API endpoint validation tests
- Database operation tests  
- Authentication middleware tests
- Input validation tests

### Medium Priority:
- Integration tests between frontend and backend
- Performance tests
- Accessibility tests
- E2E tests with Playwright

### Low Priority:
- Visual regression tests
- Load tests
- Security penetration tests