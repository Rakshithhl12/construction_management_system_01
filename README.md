# Construction Management System (CMS) v2.0

A full-stack Flask web application for managing construction projects.

## Features
- **Authentication** — Register, login, logout with hashed passwords
- **Dashboard** — Live stats overview with quick-access module cards
- **Task Management** — Add and track tasks by type, priority and status
- **Worker Management** — Worker records, departments and salary info
- **Budget Tracking** — Log expenditures with category breakdown and totals
- **Inventory Management** — Track materials, quantities and suppliers
- **Incident Reporting** — Log safety incidents with severity levels
- **Document Management** — Submit and browse project documents
- **Feedback Collection** — Star-rated feedback from team / stakeholders
- **Attendance Tracker** — Client-side daily attendance marking

## Project Structure
```
cms/
├── app.py                  # Main Flask app (routes + auth + DB)
├── requirements.txt
├── run.sh                  # Quick-start script
├── cms.db                  # SQLite database (auto-created on first run)
├── static/
│   ├── css/main.css        # Single shared stylesheet
│   └── js/main.js          # Sidebar toggle + flash helpers
└── templates/
    ├── base.html           # Shared layout with sidebar
    ├── auth_base.html      # Auth layout (login / register)
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── tasks.html
    ├── workers.html
    ├── budget.html
    ├── inventory.html
    ├── incident.html
    ├── document.html
    ├── feedback.html
    ├── attendance.html
    ├── about.html
    └── contact.html
```

## Setup & Run

### Requirements
- Python 3.8+

### Steps
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# Or use the script:
bash run.sh
```

The app will be available at **http://localhost:5001**

First time? Register an account at `/register`, then log in at `/login`.

## Security Notes
- Passwords are hashed with SHA-256
- All module routes require login (`@login_required`)
- Set `SECRET_KEY` environment variable in production:
  ```bash
  export SECRET_KEY="your-long-random-secret-key"
  ```
- Use a production WSGI server (gunicorn) for deployment:
  ```bash
  pip install gunicorn
  gunicorn -w 4 app:app
  ```
