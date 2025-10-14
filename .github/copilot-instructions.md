# Youth Attendance Platform - Copilot Instructions

## Project Overview
This is a production youth group attendance management platform built with FastAPI (backend) and Astro/React (frontend). The project follows enterprise-grade security practices and Test-Driven Development (TDD).

## Architecture & Stack
- **Backend**: FastAPI with Python 3.12+
- **Frontend**: Astro with React components and Material-UI
- **Database**: Configurable (in-memory for dev, PostgreSQL for production)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Testing**: Vitest (frontend) + pytest (backend)

## Development Methodology: Test-Driven Development (TDD)

### TDD Workflow (RED-GREEN-REFACTOR)
1. **RED**: Write a failing test first
2. **GREEN**: Write minimal code to make the test pass
3. **REFACTOR**: Improve code while keeping tests green

### Testing Standards
- **Frontend Tests**: Use Vitest + React Testing Library in `web/src/test/`
- **Backend Tests**: Use pytest in `tests/`
- **Naming**: `MethodUnderTest_StateUnderTest_ExpectedBehaviour`
- **Structure**: Follow AAA pattern (Arrange-Act-Assert)
- **Coverage**: All critical business logic must have tests
- **Isolation**: Tests must run independently with proper mocking

### Testing Commands
```bash
# Backend tests
python -m pytest tests/ -v
python -m pytest tests/ --cov=app --cov-report=html

# Frontend tests
cd web/
npm test              # Watch mode
npm run test:run      # Run once
npm run test:ui       # UI interface
npm run coverage      # With coverage
```

## Security & Quality Standards

### ✅ COMPLETED CRITICAL FIXES
- **Admin Security**: Environment-based credential management (no hardcoded passwords)
- **Error Boundaries**: Comprehensive crash prevention with graceful recovery
- **Race Conditions**: Eliminated setTimeout hacks with proper API synchronization
- **Test Architecture**: 41 comprehensive regression tests protecting all fixes

### Security Rules
- **NEVER** commit secrets, API keys, or passwords to version control
- **ALWAYS** use environment variables for sensitive configuration
- **REQUIRE** proper authentication for protected API endpoints
- **VALIDATE** all user inputs on both client and server sides
- **HASH** all passwords with bcrypt before storage

### Database Rules
- **BACKWARDS COMPATIBILITY**: All schema changes must be additive only
- **NO DESTRUCTIVE CHANGES**: Never drop columns/tables with existing data
- **MIGRATIONS**: Use proper migration scripts for schema changes
- **TESTING**: Test all database changes against existing data

## Code Quality Standards

### Frontend (React/TypeScript)
- Use React error boundaries for component crash protection
- Implement proper loading and error states
- Follow Material-UI design patterns and responsive design
- Use proper TypeScript types and interfaces
- Avoid `any` types - use proper type definitions

### Backend (FastAPI/Python)
- Use proper HTTP status codes and error responses
- Implement comprehensive try-catch blocks in API routes
- Use Pydantic models for request/response validation
- Follow REST API conventions
- Add proper logging for debugging and monitoring

### Code Organization
- **Separation of Concerns**: Keep business logic separate from UI components
- **DRY Principle**: Avoid code duplication through reusable components/functions
- **Clear Naming**: Use descriptive names for variables, functions, and classes
- **Documentation**: Add docstrings and comments for complex logic

## Development Workflow

### For New Features
1. **Write Tests First** (TDD Red phase)
   - Backend: Create pytest tests in appropriate `tests/` subdirectory
   - Frontend: Create Vitest tests in `web/src/test/components/`
2. **Implement Feature** (TDD Green phase)
   - Write minimal code to make tests pass
   - Follow existing patterns and architecture
3. **Refactor & Improve** (TDD Refactor phase)
   - Clean up code while keeping tests green
   - Add error handling and edge case coverage

### For Bug Fixes
1. **Write Regression Test** that reproduces the bug
2. **Fix the Bug** while making the test pass
3. **Verify** all existing tests still pass
4. **Document** the fix in commit messages and pull requests

## Current Priority Areas

### High Priority Security & Stability
- [ ] Input validation for person creation (client + server)
- [ ] Proper error handling in API routes with try-catch blocks
- [ ] JWT authentication middleware for protected endpoints
- [ ] Database query optimization with proper indexes

### Medium Priority Features
- [ ] Data export functionality (CSV/Excel)
- [ ] Bulk operations for person management
- [ ] User role-based permissions (admin vs regular users)
- [ ] Audit trail for data changes

### Performance & UX
- [ ] Mobile responsiveness improvements
- [ ] Bundle size optimization with code splitting
- [ ] Real-time notifications with WebSocket connections

## File Structure Understanding
```
app/                    # Backend FastAPI application
├── repositories/       # Data access layer (memory + PostgreSQL)
├── routers/           # API endpoints
├── models.py          # Pydantic models
└── main.py           # FastAPI app entry point

web/                   # Frontend Astro/React application
├── src/
│   ├── components/    # React components
│   ├── pages/        # Astro pages
│   ├── stores/       # State management
│   └── test/         # Frontend tests

tests/                 # Backend tests
├── api/              # API endpoint tests
├── models/           # Model tests
└── test_backend_admin_security.py  # Security regression tests
```

## Common Tasks & Commands

### Development
```bash
# Start backend (from root)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (from web/)
cd web && npm run dev

# Install dependencies
pip install -r requirements.txt
cd web && npm install
```

### Testing (TDD Workflow)
```bash
# Run all tests
python -m pytest tests/ -v && cd web && npm run test:run

# Watch mode for TDD
python -m pytest tests/ --looponfail &  # Backend watch
cd web && npm test                       # Frontend watch
```

## When Helping with Code

1. **Always consider TDD**: Suggest writing tests first for new features
2. **Security First**: Check for security implications in any code changes
3. **Test Coverage**: Ensure changes don't break existing functionality
4. **Follow Patterns**: Use existing code patterns and architectural decisions
5. **Documentation**: Update relevant documentation when making significant changes

Remember: This is a production system managing real user data. Prioritize security, reliability, and maintainability in all suggestions and code generation.
