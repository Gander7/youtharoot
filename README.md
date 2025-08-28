![Build Status](https://img.shields.io/github/actions/workflow/status/Gander7/Youtharoot/ci.yml)
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
- **Person Management:** Create, update, and view Youth and Leader profiles
- **Event Management:** Create, update, and view events (basic and overnight)
- **Attendance Tracking:** Record attendance for each event, including overnight attributes (waivers, forms)
- **Waiver/Form Tracking:** Store and track signed waivers for overnight events
- **Permissions/Roles:** Differentiate access for leaders and admins

### Important Enhancements
- **Groups/Teams:** Organize youths and leaders into groups
- **Reporting:** Generate attendance reports and statistics
- **Notes/Incidents:** Allow leaders to record notes per youth/event

### Optional/Advanced Features
- **Check-in/Check-out:** Digital check-in/out (QR code/manual)
- **Notifications:** Send reminders or updates to users
- **Integration:** Sync events with external calendars
- **Audit Trail:** Track changes to attendance and user data

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
	uvicorn app.main:app --reload
	```

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


## 💡 About

Created and maintained by passionate youth leaders and developers. Youtharoot is designed to make event management and attendance tracking simple, secure, and scalable.
