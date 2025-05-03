# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'replace_with_a_random_secret'

DB = 'fixmate.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password_hash = generate_password_hash(request.form['password'])
        db = get_db()
        try:
            db.execute("INSERT INTO users (username,password) VALUES (?,?)",
                       (username, password_hash))
            db.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already taken.", "danger")
        finally:
            db.close()
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?",
                          (username,)).fetchone()
        db.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Logged in successfully!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    tasks = db.execute(
        "SELECT * FROM tasks WHERE user_id = ? AND is_completed = 0 ORDER BY due_date",
        (session['user_id'],)
    ).fetchall()
    db.close()
    return render_template('dashboard.html', tasks=tasks)

@app.route('/completed')
@login_required
def completed():
    db = get_db()
    tasks = db.execute(
        "SELECT * FROM tasks WHERE user_id = ? AND is_completed = 1 ORDER BY due_date DESC",
        (session['user_id'],)
    ).fetchall()
    db.close()
    return render_template('completed_tasks.html', tasks=tasks)

@app.route('/task/add', methods=['GET','POST'])
@login_required
def add_task():
    if request.method == 'POST':
        f = request.form
        data = (
            session['user_id'],
            f['title'], f['category'], f['due_date'],
            f['frequency'], f['cost'] or 0, f['guide']
        )
        db = get_db()
        db.execute(
            "INSERT INTO tasks (user_id,title,category,due_date,frequency,cost,guide) VALUES (?,?,?,?,?,?,?)",
            data
        )
        db.commit()
        db.close()
        flash("Task added successfully!", "success")
        return redirect(url_for('dashboard'))
    return render_template('task_form.html', task=None)

@app.route('/task/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_task(id):
    db = get_db()
    task = db.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (id, session['user_id'])
    ).fetchone()
    if not task:
        db.close()
        flash("Task not found.", "danger")
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        f = request.form
        db.execute(
            "UPDATE tasks SET title=?,category=?,due_date=?,frequency=?,cost=?,guide=? WHERE id=?",
            (f['title'], f['category'], f['due_date'],
             f['frequency'], f['cost'] or 0, f['guide'], id)
        )
        db.commit()
        db.close()
        flash("Task updated successfully!", "success")
        return redirect(url_for('dashboard'))
    db.close()
    return render_template('task_form.html', task=task)

@app.route('/task/delete/<int:id>', methods=['POST'])
@login_required
def delete_task(id):
    db = get_db()
    db.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (id, session['user_id'])
    )
    db.commit()
    db.close()
    flash("Task deleted.", "info")
    return redirect(url_for('dashboard'))

@app.route('/task/complete/<int:id>', methods=['POST'])
@login_required
def complete_task(id):
    db = get_db()
    db.execute(
        "UPDATE tasks SET is_completed = 1 WHERE id = ? AND user_id = ?",
        (id, session['user_id'])
    )
    db.commit()
    db.close()
    flash("Marked task as completed!", "success")
    return redirect(url_for('dashboard'))

@app.route('/task/<int:id>')
@login_required
def task_detail(id):
    db = get_db()
    task = db.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (id, session['user_id'])
    ).fetchone()
    db.close()
    if not task:
        flash("Task not found.", "danger")
        return redirect(url_for('dashboard'))
    return render_template('task_detail.html', task=task)

if __name__ == '__main__':
    app.run()
