![Build Status](https://img.shields.io/github/a  - ✅ Support for both memory and PostgreSQL storage

### Important Enhancementsworkflow/status/Gander7/Youtharoot/ci.yml)
![Coverage](https://img.shields.io/codecov/c/github/Gander7/Youtharoot)
![License](https://img.shields.io/github/license/Gander7/Youtharoot)
![Python Version](https://img.shields.io/badge/python-3.12-blue)
![Issues](https://img.shields.io/github/issues/Gander7/Youtharoot)
![Contributors](https://img.shields.io/github/contributors/Gander7/Youtharoot)


# 🚀 Youtharoot

An API-first, mobile-friendly platform for managing youth group events, attendance, and permissions. Built with FastAPI and designed for extensibility, reliability, and ease of use.

---

## 🌟 Features & Roadmap

### Core Features (Essential for MVP)

**🔮 Still To Do:**
- 🔮 **Waiver/Form Tracking:** Store and track signed waivers for overnight events
- 🔮 **Permissions/Roles:** Differentiate access for leaders and admins
- 🔮 **Emergency Contact Validation:** Make emergency contact fields required again for youth profiles
- 🔮 **Schools Dropdown:** Replace freeform school text field with dropdown selection

### Important Enhancements
- 🔮 **Emergency Contact Alerts:** Visual warning (red background/danger styling) for youth missing emergency contact information
- 🔮 **Birthday Notifications:** Display birthday alerts/notifications when it's a youth's birthday
- 🔮 **Contact Information Expansion:**
  - 🔮 Add email address field for youth profiles
  - 🔮 Split emergency contact name into separate first name and last name fields
  - 🔮 Add email address field for emergency contacts
- 🔮 **Groups/Teams:** Organize youths and leaders into groups
- 🔮 **Reporting:** Generate attendance reports and statistics
- 🔮 **Notes/Incidents:** Allow leaders to record notes per youth/event
- 🔮 **Person Detail Pages:** Individual person profiles with history
- 🔮 **Bulk Import:** Import people from CSV/Excel files
- 🔮 **Advanced Filtering:** Filter by grade, school, attendance history
- 🔮 **School Management:** Admin interface to manage the predefined school list
- 🔮 **Data Validation Enhancements:** 
  - 🔮 Phone number formatting and validation
  - 🔮 Address validation
  - 🔮 Emergency contact relationship presets

### Optional/Advanced Features
- 🔮 **QR Code Check-in:** Digital check-in/out using QR codes
- 🔮 **Notifications:** Send reminders or updates to users
- 🔮 **Integration:** Sync events with external calendars
- 🔮 **Audit Trail:** Track changes to attendance and user data

### Completed
- ✅ **Person Management:** Create, update, and view Youth and Leader profiles
  - ✅ Modern PersonList component with search and filtering
  - ✅ Streamlined PersonForm with context-aware fields
  - ✅ Mobile-first design with floating action buttons
  - ✅ Smart search by name, school, or role
  - ✅ Birthday dates must be in ISO format (YYYY-MM-DD)
- ✅ **Event Management:** Create, update, and view events (basic and overnight)
  - ✅ EventList component with "Add Event" functionality
  - ✅ Mobile-optimized event display
  - ✅ Check-in button for today/tomorrow events
- ✅ **Navigation System:** Seamless navigation between pages
  - ✅ Desktop app bar navigation
  - ✅ Mobile bottom navigation bar
  - ✅ Responsive design patterns
- ✅ **Dark Mode UI:** Consistent dark theme across all pages
  - ✅ Material Design 3 color system
  - ✅ Mobile-first responsive layouts
- ✅ **Attendance Tracking:** Record attendance for each event
  - ✅ Check-in/Check-out functionality
  - ✅ Available/Checked In/Checked Out filters
  - ✅ Real-time attendance updates
  - ✅ Support for both memory and PostgreSQL storage
- ✅ **Authentication:** User login and permission system
  - ✅ JWT token-based authentication
  - ✅ User management with admin controls
  - ✅ Role-based access control (admin/user roles)
  - ✅ Secure password hashing with bcrypt
---

## ⚡ Installation

1. **Clone the repository:**
	```bash
	git clone https://github.com/yourusername/youth-attendance.git
	cd youth-attendance
	```
2. **Create a virtual environment (recommended):**
	```bash
	python -m venv venv
	source venv/bin/activate
	```
3. **Install backend dependencies:**
	```bash
	cd backend
	pip install -r requirements.txt
	```
4. **Install frontend dependencies:**
	```bash
	cd ../frontend
	npm install
	```
5. **Run the API server:**
	```bash
	cd ../backend
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
	```

6. **Run the frontend (in another terminal):**
	```bash
	cd frontend
	npm run dev
	```

7. **Access the application:**
	- Frontend: http://localhost:4321
	- API Documentation: http://localhost:8000/docs

---

## 🗄️ Database Configuration

The application supports **configurable storage** for development and production:

### **Development Mode (Default)**
- **In-Memory Storage**: Data stored in Python dictionaries
- **No setup required**: Just run the application
- **Data is temporary**: Lost on server restart
- **Perfect for**: Testing, UI development, experimentation

### **Production Mode**
- **PostgreSQL Database**: Persistent, scalable storage
- **Automatic setup**: Railway provides managed PostgreSQL
- **Data persistence**: Survives server restarts
- **Perfect for**: Live deployments, real user data

### **Environment Variables**
```bash
# Development (default)
DATABASE_TYPE=memory
DEBUG=true
SECRET_KEY=your-dev-secret-key-for-local-testing

# Production  
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@host:port/db
DEBUG=false
SECRET_KEY=your-secure-production-secret-key-make-it-very-long-and-random
```

**Note:** The SECRET_KEY is required for JWT token signing in the authentication system. Use different keys for development and production.

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

---

## 🔐 Demo Credentials

For development and testing, the application creates a default admin user with these credentials:

```
Username: admin
Password: admin123
```

**⚠️ Important Security Notes:**
- These credentials are set via the `ADMIN_PASSWORD` environment variable
- In production, **always** change the default password via environment variables
- The application uses bcrypt password hashing for security
- JWT tokens expire after 2 hours for security

---

## 🧪 Testing

This project uses a proper separation between frontend and backend testing frameworks for optimal development experience.

### **Backend Tests (Python/pytest)**

Tests API logic, database operations, business logic, and security.

```bash
# Navigate to backend directory
cd backend/

# Run all backend tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/test_backend_admin_security.py -v
```

### **Frontend Tests (JavaScript/Vitest)**

Tests React components, user interactions, UI logic, and frontend race conditions.

```bash
# Navigate to frontend directory
cd frontend/

# Run tests (watch mode)
npm test

# Run tests once
npm run test:run

# Run with UI interface
npm run test:ui

# Run with coverage
npm run coverage
```

### **Test Coverage Summary**

- ✅ **Backend Security Tests:** 10 tests protecting admin initialization and credential security
- ✅ **Frontend Error Boundary Tests:** 19 tests ensuring crash prevention and recovery
- ✅ **Frontend Race Condition Tests:** 12 tests eliminating timing dependencies and API synchronization issues
- **Total:** 41 comprehensive regression tests

### **Test Architecture**

```
📁 backend/
├── tests/                          # Backend (Python/pytest)
│   ├── test_backend_admin_security.py  # Admin initialization security
│   ├── api/test_*.py                   # API endpoint tests
│   └── models/test_*.py                # Model validation tests
├── app/                            # FastAPI application
└── requirements.txt                # Python dependencies

📁 frontend/
├── src/test/                       # Frontend (JavaScript/Vitest)
│   ├── components/
│   │   ├── ErrorBoundary.test.jsx     # Crash prevention tests
│   │   └── CheckIn.test.jsx           # Race condition tests  
│   ├── integration/                   # Future integration tests
│   └── setup.js                      # Test configuration
├── src/                            # React/Astro source code
└── package.json                    # Node.js dependencies
```

See [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md) for detailed testing documentation.

---

## 🤝 Contributing

We welcome contributions! Please:
- Fork the repo and create your branch from `main`
- Use conventional commit messages
- Write tests for new features and bug fixes
- Open a pull request with a clear description

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---


---

## 🛠️ Technical Debt & Code Quality TODOs

### Critical Issues 🚨
- [x] **Remove hardcoded credentials** - ✅ COMPLETED: Replaced hardcoded admin password hash with secure environment variable initialization for both memory and PostgreSQL repositories
- [x] **Implement error boundaries** - ✅ COMPLETED: Added comprehensive React error boundaries with crash prevention, graceful error handling, and retry mechanisms
- [x] **Fix race conditions** - ✅ COMPLETED: Eliminated setTimeout hack in CheckIn.jsx and implemented proper synchronous API response handling

### High Priority ⚠️
- [ ] **Add input validation** - Implement client-side and server-side validation for required fields, phone number format, email format
- [ ] **Implement proper error handling in API routes** - Add try-catch blocks and proper HTTP status codes in FastAPI routes
- [ ] **Add authentication middleware** - Implement JWT token validation middleware for protected API endpoints
- [ ] **Refactor repository initialization architecture** - Fix the repository singleton pattern to prevent re-initialization between API calls in test environments. Current quick fix uses test-specific repository overrides, but production architecture needs proper singleton enforcement
- [ ] **Add request cancellation** - Implement AbortController for API requests and cleanup in useEffect hooks
- [ ] **Replace localStorage communication** - Replace localStorage-based cross-component communication with proper state management
- [ ] **Implement proper routing** - Replace window.location.href direct manipulation with proper Astro/React routing
- [ ] **Centralize API error handling** - Create consistent error response format across all API endpoints

### Medium Priority 🔧
- [x] **Add comprehensive unit tests** - ✅ COMPLETED: Created comprehensive regression tests with proper frontend (Vitest) and backend (pytest) separation
- [ ] **Improve type safety** - Convert remaining JavaScript to TypeScript and add proper type definitions
- [ ] **Separate business logic from UI** - Extract business logic from CheckIn.jsx into custom hooks and service layers
- [ ] **Add debouncing to search inputs** - Implement debouncing to prevent excessive API calls
- [ ] **Centralize theme definitions** - Move all inline styles and scattered theme definitions to centralized configuration
- [ ] **Optimize database queries** - Add database indexes for frequently queried fields and implement query optimization
- [ ] **Add comprehensive logging system** - Implement structured logging for debugging and monitoring

### Low Priority 📱
- [ ] **Implement accessibility features** - Add ARIA labels, keyboard navigation support, and improve color contrast
- [ ] **Add performance optimizations** - Implement virtualization for large lists, prevent unnecessary re-renders
- [ ] **Remove debug console logs** - Clean up console.log statements and implement proper logging framework
- [ ] **Add rate limiting** - Implement API rate limiting and request throttling
- [ ] **Implement integration tests** - Create end-to-end tests for critical user flows
- [ ] **Improve mobile responsiveness** - Optimize UI components for mobile devices and touch interfaces
- [ ] **Add data export functionality** - Add CSV/Excel export for attendance records and person data
- [ ] **Add bulk operations** - Implement bulk import/export and bulk edit operations for person management

---

## 💡 About

Created and maintained by passionate youth leaders and developers. Youtharoot is designed to make event management and attendance tracking simple, secure, and scalable.
