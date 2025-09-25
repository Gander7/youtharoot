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
- 🔮 **Authentication:** User login and permission system
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
3. **Install dependencies:**
	```bash
	pip install -r requirements.txt
	```
4. **Run the API server:**
	```bash
	source venv/bin/activate
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
	```

5. **Run the frontend (in another terminal):**
	```bash
	cd web
	npm run dev
	```

6. **Access the application:**
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

## 🧪 Testing

Run all tests with:
```bash
pytest
```

To check coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

To view a detailed coverage report:
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in your browser
```

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

## 🚧 TODO & Feature Requests

### **� EXTREMELY IMPORTANT**
- [ ] **SMS Messaging System**: Send text messages to youth and leaders
  - [ ] Integration with SMS service (Twilio, AWS SNS, or similar)
  - [ ] Bulk SMS capability for event notifications
  - [ ] Individual SMS messaging for urgent communications
  - [ ] SMS templates for common messages
  - [ ] Opt-in/opt-out SMS preferences management
  - [ ] SMS delivery status tracking
  - [ ] Emergency broadcast SMS functionality

### **�🔧 Improvements Needed**
- [ ] **Mobile UI Fixes**
  - [ ] Fix mobile view for check-in page (layout/responsiveness issues)
  - [ ] Audit all screens for mobile responsiveness
  - [ ] Test navigation on mobile devices
  - [ ] Optimize touch targets and spacing for mobile

### **🌟 Planned Features**
- [ ] **Emergency Contact Alerts**: Automated notifications for urgent situations
- [ ] **Birthday Notifications**: Automatic birthday reminders for youth and leaders
- [ ] **Contact Information Expansion**: Support for multiple phone numbers, email addresses, and social media handles
- [ ] **Attendance Analytics**: Charts and reports for attendance patterns
- [ ] **Event Templates**: Reusable event configurations
- [ ] **Group Management**: Organize youth into small groups or classes
- [ ] **Parent Portal**: Dedicated access for parents/guardians
- [ ] **Notification System**: SMS/Email alerts for events and updates

### **🛠️ Technical Enhancements**
- [ ] **Custom Domain Setup**: Configure custom domain for production deployment
  - [ ] Domain registration and DNS configuration
  - [ ] SSL certificate setup for HTTPS
  - [ ] Railway domain configuration
  - [ ] Update environment variables and CORS settings
- [ ] **Offline Support**: PWA capabilities for offline check-ins
- [ ] **Data Export**: Export attendance and contact data to CSV/Excel
- [ ] **API Rate Limiting**: Enhanced security for production use
- [ ] **Automated Backups**: Scheduled database backups with retention policies
- [ ] **Performance Optimization**: Database indexing and query optimization

---

## 💡 About

Created and maintained by passionate youth leaders and developers. Youtharoot is designed to make event management and attendance tracking simple, secure, and scalable.
