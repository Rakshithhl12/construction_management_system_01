from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_cors import CORS
from functools import wraps
import sqlite3
import hashlib
import os
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cms_super_secret_key_2024_change_in_prod')
CORS(app)

logging.basicConfig(level=logging.INFO)
DB_PATH = os.path.join(os.path.dirname(__file__), 'cms.db')


# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            phone TEXT,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            task_type TEXT,
            priority TEXT,
            assigned_to TEXT,
            status TEXT,
            start_date TEXT,
            due_date TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL,
            date TEXT,
            category TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_title TEXT NOT NULL,
            document_type TEXT,
            document_date TEXT,
            document_description TEXT,
            uploaded_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            rating INTEGER,
            description TEXT,
            author TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT,
            location TEXT,
            type TEXT,
            description TEXT,
            affected_workers INTEGER,
            severity TEXT,
            reported_by TEXT,
            resolution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER,
            unit TEXT,
            supplier TEXT,
            purchase_date TEXT,
            expiry_date TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_name TEXT NOT NULL,
            worker_id TEXT,
            department TEXT,
            contact_number TEXT,
            date_of_joining TEXT,
            worker_status TEXT,
            salary REAL,
            performance_rating REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    logging.info("Database initialised at %s", DB_PATH)


# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route('/')
def root():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, hash_password(password))
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', '').strip()
        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (name, email, password, phone, role) VALUES (?, ?, ?, ?, ?)",
                (name, email, hash_password(password), phone, role)
            )
            conn.commit()
            conn.close()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('An account with this email already exists.', 'danger')
        except Exception as e:
            logging.error(e)
            flash('Registration failed. Please try again.', 'danger')
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ── Protected page routes ─────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    stats = {
        'tasks': conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
        'workers': conn.execute("SELECT COUNT(*) FROM workers").fetchone()[0],
        'budgets': conn.execute("SELECT COUNT(*) FROM budgets").fetchone()[0],
        'incidents': conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0],
        'inventory': conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0],
        'documents': conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
    }
    conn.close()
    return render_template('dashboard.html', stats=stats)


@app.route('/tasks')
@login_required
def tasks():
    conn = get_db()
    rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('tasks.html', tasks=rows)


@app.route('/inventory')
@login_required
def inventory():
    conn = get_db()
    rows = conn.execute("SELECT * FROM inventory ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('inventory.html', items=rows)


@app.route('/budget')
@login_required
def budget():
    conn = get_db()
    rows = conn.execute("SELECT * FROM budgets ORDER BY created_at DESC").fetchall()
    total = conn.execute("SELECT SUM(amount) FROM budgets").fetchone()[0] or 0
    conn.close()
    return render_template('budget.html', budgets=rows, total=total)


@app.route('/workers')
@login_required
def workers():
    conn = get_db()
    rows = conn.execute("SELECT * FROM workers ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('workers.html', workers=rows)


@app.route('/incident')
@login_required
def incident():
    conn = get_db()
    rows = conn.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('incident.html', incidents=rows)


@app.route('/documents')
@login_required
def documents():
    conn = get_db()
    rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('document.html', documents=rows)


@app.route('/feedback')
@login_required
def feedback():
    conn = get_db()
    rows = conn.execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('feedback.html', feedbacks=rows)


@app.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html')


@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/contact')
@login_required
def contact():
    return render_template('contact.html')


# ── Form POST routes ──────────────────────────────────────────────────────────

@app.route('/add_tasks', methods=['POST'])
@login_required
def add_tasks():
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO tasks (task_name, task_type, priority, assigned_to, status,
               start_date, due_date, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (request.form['taskName'], request.form['taskType'], request.form['taskPriority'],
             request.form['assignedTo'], request.form['taskStatus'], request.form['startDate'],
             request.form['dueDate'], request.form['taskDescription'])
        )
        conn.commit()
        conn.close()
        flash('Task added successfully!', 'success')
    except Exception as e:
        logging.error(e)
        flash('Failed to add task.', 'danger')
    return redirect(url_for('tasks'))


@app.route('/submit_budget', methods=['POST'])
@login_required
def submit_budget():
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO budgets (title, amount, date, category, description) VALUES (?, ?, ?, ?, ?)",
            (request.form['budgetTitle'], request.form['budgetAmount'], request.form['budgetDate'],
             request.form['budgetCategory'], request.form['budgetDescription'])
        )
        conn.commit()
        conn.close()
        flash('Budget entry saved!', 'success')
    except Exception as e:
        logging.error(e)
        flash('Failed to save budget.', 'danger')
    return redirect(url_for('budget'))


@app.route('/submit_document', methods=['POST'])
@login_required
def submit_document():
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO documents (document_title, document_type, document_date,
               document_description, uploaded_by) VALUES (?, ?, ?, ?, ?)""",
            (request.form['documentTitle'], request.form['documentType'], request.form['documentDate'],
             request.form['documentDescription'], session.get('user_name', ''))
        )
        conn.commit()
        conn.close()
        flash('Document submitted successfully!', 'success')
    except Exception as e:
        logging.error(e)
        flash('Failed to submit document.', 'danger')
    return redirect(url_for('documents'))


@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO feedback (title, rating, description, author, email) VALUES (?, ?, ?, ?, ?)",
            (request.form['feedbackTitle'], request.form['feedbackRating'],
             request.form['feedbackDescription'], request.form['feedbackAuthor'],
             request.form['feedbackEmail'])
        )
        conn.commit()
        conn.close()
        flash('Feedback submitted!', 'success')
    except Exception as e:
        logging.error(e)
        flash('Failed to submit feedback.', 'danger')
    return redirect(url_for('feedback'))


@app.route('/report_incident', methods=['POST'])
@login_required
def report_incident():
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO incidents (title, date, location, type, description,
               affected_workers, severity, reported_by, resolution) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (request.form['incidentTitle'], request.form['incidentDate'], request.form['location'],
             request.form['incidentType'], request.form['incidentDescription'],
             request.form.get('affectedWorkers', 0), request.form['severity'],
             session.get('user_name', ''), request.form.get('resolution', ''))
        )
        conn.commit()
        conn.close()
        flash('Incident reported!', 'success')
    except Exception as e:
        logging.error(e)
        flash('Failed to report incident.', 'danger')
    return redirect(url_for('incident'))


@app.route('/submit_inventory', methods=['POST'])
@login_required
def submit_inventory():
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO inventory (item_name, category, quantity, unit, supplier,
               purchase_date, expiry_date, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (request.form['itemName'], request.form['category'], request.form['quantity'],
             request.form['unit'], request.form['supplier'], request.form['purchaseDate'],
             request.form.get('expiryDate', ''), request.form.get('description', ''))
        )
        conn.commit()
        conn.close()
        flash('Inventory item added!', 'success')
    except Exception as e:
        logging.error(e)
        flash('Failed to add inventory item.', 'danger')
    return redirect(url_for('inventory'))


@app.route('/add_worker', methods=['POST'])
@login_required
def add_worker():
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO workers (worker_name, worker_id, department, contact_number,
               date_of_joining, worker_status, salary, performance_rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (request.form['workerName'], request.form['workerId'], request.form['department'],
             request.form['contactNumber'], request.form['dateOfJoining'], request.form['workerStatus'],
             request.form['salary'], request.form.get('performanceRating') or None)
        )
        conn.commit()
        conn.close()
        flash('Worker added successfully!', 'success')
    except Exception as e:
        logging.error(e)
        flash('Failed to add worker.', 'danger')
    return redirect(url_for('workers'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5444)
