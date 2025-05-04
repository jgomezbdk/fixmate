# --- Imports ---
from flask import (
    Flask, render_template, redirect, url_for,
    request, session, g, flash # Added request here
)
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone # Added timezone for utcnow fix

# --- App Initialization ---
app = Flask(__name__)
# IMPORTANT: Replace with your own secret key! Use a long, random string.
# You can generate one using: python -c 'import secrets; print(secrets.token_hex())'
app.secret_key = 'replace_this_with_your_own_secret_string_now!' # <-- CHANGE THIS!
DATABASE = 'fixmate.db'

# --- Database Helper Functions ---
def get_db():
    """Connects to the specific database."""
    if 'db' not in g:
        # Get absolute path to ensure correctness, especially for CLI commands
        import os
        db_path = os.path.abspath(DATABASE)
        # print(f"Connecting to DB at: {db_path}") # Optional: for debugging path issues
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row # Return rows that behave like dictionaries
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db:
        db.close()

# --- Template Context Processor ---
@app.context_processor
def inject_now():
    """Injects current UTC date/time into templates, e.g., for footer year."""
    # Use the recommended timezone-aware method
    return {'now': datetime.now(timezone.utc)}

# --- Login Decorator ---
def login_required(f):
    """Decorator to ensure user is logged in before accessing a route."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        # Store user info in g for easy access during request if needed
        # g.user = session.get('user') # Optional convenience
        return f(*args, **kwargs)
    return wrapped

# --- Basic Routes (Home, Login, Register, Logout) ---
@app.route('/')
def home():
    """Homepage redirects to dashboard if logged in, else login."""
    return redirect(url_for('dashboard') if 'user' in session else url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    db = get_db()
    if 'user' in session:
        return redirect(url_for('dashboard')) # Don't show register page if logged in

    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')

        # --- Input Validation ---
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('register.html')
        # Add more checks? e.g., password length

        # --- Hash Password ---
        hashed_password = generate_password_hash(password)

        # --- Insert into Database ---
        try:
            db.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, hashed_password)
            )
            db.commit()
        except sqlite3.IntegrityError: # Specific error for UNIQUE constraint
            flash('Username already taken. Please choose another.', 'danger')
            return render_template('register.html')
        except sqlite3.Error as e: # Catch other potential DB errors
            flash(f'An error occurred during registration: {e}', 'danger')
            app.logger.error(f"Registration DB Error: {e}") # Log the actual error
            return render_template('register.html')

        # --- Auto-login after successful registration ---
        # Fetch the newly created user to get their ID
        user = db.execute(
            'SELECT id, username FROM users WHERE username = ?',
            (username,)
        ).fetchone()

        if user:
            session.clear() # Clear any old session data
            session['user'] = {
                'id': user['id'],
                'username': user['username']
            }
            flash(f'Registration successful! Welcome, {username}.', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Should not happen if insert succeeded, but handle defensively
            flash('Registration succeeded but failed to log in automatically. Please log in manually.', 'warning')
            app.logger.error(f"Failed to fetch user '{username}' immediately after registration.")
            return redirect(url_for('login'))

    # --- Show Registration Form (GET request) ---
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    db = get_db()
    if 'user' in session:
        return redirect(url_for('dashboard')) # Don't show login page if logged in

    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        user = None

        # --- Input Validation ---
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')

        # --- Fetch User ---
        try:
            user = db.execute(
                'SELECT id, username, password_hash FROM users WHERE username = ?',
                (username,)
            ).fetchone()
        except sqlite3.Error as e:
            flash(f'An error occurred during login: {e}', 'danger')
            app.logger.error(f"Login DB Error (Fetch User): {e}")
            return render_template('login.html')

        # --- Verify Password and Create Session ---
        if user and check_password_hash(user['password_hash'], password):
            session.clear() # Ensure clean session
            session['user'] = {
                'id': user['id'],
                'username': user['username']
            }
            # Optional: Add a welcome back flash message
            # flash(f"Welcome back, {user['username']}!", "info")
            # Redirect to intended page or dashboard
            # next_page = request.args.get('next') # For redirecting after login if required by @login_required
            # if next_page: return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            # No return here, falls through to render_template below

    # --- Show Login Form (GET request or failed POST) ---
    return render_template('login.html')

@app.route('/logout')
@login_required # Ensure only logged-in users can logout
def logout():
    """Logs the user out by clearing the session."""
    username = session.get('user', {}).get('username', 'User') # Get username for message
    session.clear()
    flash(f"You have been logged out, {username}.", "info")
    return redirect(url_for('login'))

# --- Core Application Routes (Dashboard, Tasks) ---

# !!! THIS IS THE UPDATED DASHBOARD FUNCTION !!!
@app.route('/dashboard')
@login_required
def dashboard():
    """Displays the user's task dashboard, toggling between views."""
    # --- Determine which view to show based on query parameter ---
    requested_view = request.args.get('view', 'incomplete') # Default to 'incomplete'
    if requested_view not in ['incomplete', 'completed']:
        current_view = 'incomplete' # Fallback for invalid values
    else:
        current_view = requested_view
    # --- End view determination ---

    db = get_db()
    user_id = session['user']['id']
    incomplete = []
    completed = []
    try:
        # Fetch both lists regardless of view; template will handle display
        incomplete = db.execute(
            'SELECT * FROM tasks WHERE user_id = ? AND completed = 0 ORDER BY due_date ASC, title ASC',
            (user_id,)
        ).fetchall()
        completed = db.execute(
            'SELECT * FROM tasks WHERE user_id = ? AND completed = 1 ORDER BY title ASC',
            (user_id,)
        ).fetchall()
    except sqlite3.Error as e:
        flash(f"Error fetching tasks: {e}", "danger")
        app.logger.error(f"Dashboard DB Error: {e}")
        # Render dashboard even if tasks can't be fetched, but pass current_view
        return render_template(
            'dashboard.html',
            incomplete_tasks=[],
            completed_tasks=[],
            current_view=current_view # Pass current view even on error
        )

    # Pass the task lists and current view to the template
    return render_template(
        'dashboard.html',
        incomplete_tasks=incomplete,
        completed_tasks=completed,
        current_view=current_view # Pass the current view to the template
    )
# !!! END OF UPDATED DASHBOARD FUNCTION !!!


@app.route('/task/add', methods=['GET','POST'])
@login_required
def add_task():
    """Handles adding a new task."""
    if request.method == 'POST':
        form = request.form
        db = get_db()
        # Basic validation - ensure title is present
        if not form.get('title','').strip():
            flash("Task title cannot be empty.", "danger")
            # Re-render form, potentially passing back other entered data if needed
            return render_template('task_form.html', task=form, form_action=url_for('add_task'))

        try:
            db.execute(
                '''INSERT INTO tasks
                   (user_id, title, category, due_date, frequency, cost,
                    estimated_time, guide, completed)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)''',
                (
                    session['user']['id'],
                    form['title'].strip(), # Ensure title is stripped
                    form.get('category'), form.get('due_date'), # Store dates as YYYY-MM-DD strings
                    form.get('frequency'), form.get('cost'), # Store cost as number (REAL)
                    form.get('estimated_time'), form.get('guide'),
                    # video_url - not currently in form, could be added
                )
            )
            db.commit()
            flash("Task added successfully!", "success")
        except sqlite3.Error as e:
            flash(f"Error adding task: {e}", "danger")
            app.logger.error(f"Add Task DB Error: {e}")
            # Return to form on error, possibly pre-filling with form data
            return render_template('task_form.html', task=form, form_action=url_for('add_task'))

        return redirect(url_for('dashboard')) # Redirect to dashboard on success

    # --- Show Add Task Form (GET request) ---
    # Pass action URL for clarity in template
    return render_template('task_form.html', task=None, form_action=url_for('add_task'))


@app.route('/task/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit_task(id):
    """Handles editing an existing task."""
    db = get_db()
    user_id = session['user']['id']
    task = None # Initialize task

    # --- Fetch Task (used for both GET and initial POST validation) ---
    try:
        task = db.execute(
            'SELECT * FROM tasks WHERE id = ? AND user_id = ?',
            (id, user_id)
        ).fetchone()
    except sqlite3.Error as e:
        flash(f"Error fetching task for edit: {e}", "danger")
        app.logger.error(f"Edit Task Fetch DB Error: {e}")
        return redirect(url_for('dashboard'))

    # --- Handle Task Not Found or Access Denied ---
    if not task:
        flash("Task not found or access denied.", "warning")
        return redirect(url_for('dashboard'))

    # --- Handle Form Submission (POST request) ---
    if request.method == 'POST':
        form = request.form
        # Basic validation - ensure title is present
        if not form.get('title','').strip():
            flash("Task title cannot be empty.", "danger")
            # Re-render form with current task data and error
            return render_template('task_form.html', task=task, form_action=url_for('edit_task', id=id))

        try:
            db.execute(
                '''UPDATE tasks SET
                      title=?, category=?, due_date=?, frequency=?,
                      cost=?, estimated_time=?, guide=?
                   WHERE id=? AND user_id=?''',
                (
                    form['title'].strip(), form.get('category'), form.get('due_date'),
                    form.get('frequency'), form.get('cost'),
                    form.get('estimated_time'), form.get('guide'),
                    # video_url - not currently in form
                    id, user_id
                )
            )
            db.commit()
            flash("Task updated successfully!", "success")
        except sqlite3.Error as e:
            flash(f"Error updating task: {e}", "danger")
            app.logger.error(f"Edit Task Update DB Error: {e}")
            # Return to form on error, maintaining existing task data in form
            return render_template('task_form.html', task=task, form_action=url_for('edit_task', id=id))

        # Redirect to dashboard after successful POST
        return redirect(url_for('dashboard'))

    # --- Show Edit Task Form (GET request) ---
    # Render the form pre-filled with existing task data
    return render_template('task_form.html', task=task, form_action=url_for('edit_task', id=id))


@app.route('/task/<int:id>')
@login_required
def task_detail(id):
    """Displays the details of a single task."""
    db = get_db()
    task = None
    try:
        task = db.execute(
            'SELECT * FROM tasks WHERE id = ? AND user_id = ?',
            (id, session['user']['id'])
        ).fetchone()
    except sqlite3.Error as e:
        flash(f"Error fetching task details: {e}", "danger")
        app.logger.error(f"Task Detail DB Error: {e}")
        return redirect(url_for('dashboard'))

    if not task:
        flash("Task not found or access denied.", "warning")
        return redirect(url_for('dashboard'))

    return render_template('task_detail.html', task=task)

@app.route('/task/complete/<int:id>', methods=['POST'])
@login_required
def complete_task(id):
    """Marks a task as complete."""
    db = get_db()
    user_id = session['user']['id']
    try:
        # Ensure the task belongs to the user before updating
        result = db.execute(
            'UPDATE tasks SET completed = 1 WHERE id = ? AND user_id = ?',
            (id, user_id)
        )
        db.commit()
        if result.rowcount == 0: # Check if any row was actually updated
             flash("Task not found or access denied.", "warning")
        else:
             flash("Task marked as complete.", "success")
    except sqlite3.Error as e:
        flash(f"Error completing task: {e}", "danger")
        app.logger.error(f"Complete Task DB Error: {e}")

    # Redirect back to the default dashboard view (Tasks)
    return redirect(url_for('dashboard'))

@app.route('/task/uncomplete/<int:id>', methods=['POST'])
@login_required
def uncomplete_task(id):
    """Marks a task as incomplete."""
    db = get_db()
    user_id = session['user']['id']
    try:
         # Ensure the task belongs to the user before updating
        result = db.execute(
            'UPDATE tasks SET completed = 0 WHERE id = ? AND user_id = ?',
            (id, user_id)
        )
        db.commit()
        if result.rowcount == 0: # Check if any row was actually updated
             flash("Task not found or access denied.", "warning")
        else:
             flash("Task marked as incomplete.", "info")
    except sqlite3.Error as e:
        flash(f"Error marking task as incomplete: {e}", "danger")
        app.logger.error(f"Uncomplete Task DB Error: {e}")

    # Redirect back to the completed view after uncompleting
    return redirect(url_for('dashboard', view='completed'))

@app.route('/task/delete/<int:id>', methods=['POST'])
@login_required
def delete_task(id):
    """Deletes a task."""
    db = get_db()
    user_id = session['user']['id']
    try:
         # Ensure the task belongs to the user before deleting
        result = db.execute(
            'DELETE FROM tasks WHERE id = ? AND user_id = ?',
            (id, user_id)
        )
        db.commit()
        if result.rowcount == 0: # Check if any row was actually deleted
             flash("Task not found or access denied.", "warning")
        else:
             flash("Task deleted.", "info")
    except sqlite3.Error as e:
        flash(f"Error deleting task: {e}", "danger")
        app.logger.error(f"Delete Task DB Error: {e}")

    # Determine which view to redirect back to
    # A bit tricky - maybe check referrer? Simpler to just go to default dashboard.
    # Or maybe check if the task *was* completed before deleting? Requires fetching first.
    # For now, just redirect to default dashboard view.
    return redirect(url_for('dashboard'))


# --- Analytics Route ---
@app.route('/analytics')
@login_required
def analytics():
    """Displays simple task count analytics."""
    db = get_db()
    user_id = session['user']['id']
    total_tasks = 0
    completed_tasks = 0

    try:
        # Query to count total tasks for the user
        total_result = db.execute(
            'SELECT COUNT(id) FROM tasks WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        if total_result:
            total_tasks = total_result[0] # COUNT returns one row, first column is the count

        # Query to count completed tasks for the user
        completed_result = db.execute(
            'SELECT COUNT(id) FROM tasks WHERE user_id = ? AND completed = 1',
            (user_id,)
        ).fetchone()
        if completed_result:
            completed_tasks = completed_result[0]

    except sqlite3.Error as e:
        flash(f"Error fetching analytics data: {e}", "danger")
        app.logger.error(f"Analytics DB Error: {e}")
        # Render with default values on error
        return render_template('analytics.html', total=0, done=0)

    # Pass the counts to the template
    return render_template(
        'analytics.html',
        total=total_tasks,
        done=completed_tasks
    )


# --- Database Initialization Function and CLI command ---
def init_db():
    """Initializes the database schema."""
    # Use try-except blocks for robustness during table creation
    db = get_db()
    schema_version = 0 # Track schema version if needed later

    # Get absolute path for clarity
    import os
    db_path = os.path.abspath(DATABASE)
    print(f"Initializing database schema in: {db_path}")

    try:
        print("Checking/Creating 'users' table...")
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
        ''')
        print(" -> 'users' table checked/created.")
        schema_version = 1 # Or increment if tracking versions
    except sqlite3.Error as e:
        print(f" -> Error creating/checking 'users' table: {e}")
        app.logger.error(f"Init DB Users Error: {e}") # Log error

    try:
        print("Checking/Creating 'tasks' table...")
        db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT,
                due_date TEXT,    -- Store dates as ISO 8601 strings (YYYY-MM-DD)
                frequency TEXT,
                cost REAL,        -- Use REAL for currency/decimal values
                estimated_time TEXT, -- e.g., "30 minutes", "2 hours"
                guide TEXT,       -- Text instructions
                video_url TEXT,   -- Optional: URL to a video guide (set to NULL if not needed)
                completed INTEGER DEFAULT 0 CHECK(completed IN (0, 1)), -- 0=False, 1=True
                created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, -- Track creation time
                -- completed_timestamp DATETIME, -- Optional: track completion time
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        ''')
        print(" -> 'tasks' table checked/created.")
    except sqlite3.Error as e:
        print(f" -> Error creating/checking 'tasks' table: {e}")
        app.logger.error(f"Init DB Tasks Error: {e}") # Log error

    try:
        # Add indexes for performance if they don't exist
        print("Checking/Creating indexes...")
        db.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks (user_id);')
        db.execute('CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks (user_id, completed);')
        print(" -> Indexes checked/created.")
    except sqlite3.Error as e:
        print(f" -> Error creating/checking indexes: {e}")
        app.logger.error(f"Init DB Indexes Error: {e}") # Log error

    # Add schema version tracking or migration logic here if needed in the future
    # Example: db.execute('PRAGMA user_version = ?', (schema_version,))

    db.commit()
    print("Database initialization process completed.")


@app.cli.command('init-db')
def init_db_command():
    """
    CLI command to clear existing data and create new tables.
    Run using: flask init-db
    """
    import click # For CLI echo
    click.echo("WARNING: This will delete existing data if tables are recreated!")
    # Consider adding a --force option or prompt? For now, rely on manual deletion if needed.
    # It's safer to manually delete the .db file if a schema *change* requires it,
    # as 'CREATE TABLE IF NOT EXISTS' won't modify existing tables.

    with app.app_context():
        # Connect using get_db to ensure correct path and context handling
        # init_db() function already handles the connection via get_db()
        init_db()
    click.echo('Initialized the database based on current app.py schema.')


# --- Run the App ---
if __name__ == '__main__':
    # Basic logging configuration (useful for seeing startup messages and errors)
    import logging
    logging.basicConfig(level=logging.INFO) # Log INFO level and above

    # Set debug=True for development (auto-reload, interactive debugger)
    # Set debug=False for production deployment
    # Consider using environment variable: debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=True)