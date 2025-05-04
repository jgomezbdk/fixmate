FixMate - Home Maintenance Task Manager
FixMate is a modern web application designed to help homeowners and renters organize, track, and maintain essential home upkeep tasks. From scheduling HVAC filter changes to power washing the exterior, FixMate centralizes task details—due dates, costs, repair guides—into a clean, intuitive interface, preventing tasks from falling through the cracks.

🚀 Key Features
User Authentication: Secure registration and login using hashed passwords (via Werkzeug).

Task Management: Create, read, update, and delete maintenance tasks with fields for title, category, due date, frequency, cost, estimated time, and repair guide text/URL.

Dashboard View Toggle: Easily switch between viewing pending ("Tasks") and completed tasks on the main dashboard.

Integrated Guide Search: A "🔍 Search YouTube" button appears when editing the repair guide field, providing quick access to relevant tutorial videos based on the guide content.

Basic Analytics: An integrated page showing counts of total, completed, and pending tasks for the logged-in user.

Optional Streamlit Analytics: A separate, optional interactive dashboard (run independently) showcasing more detailed task statistics and trends using Streamlit and Pandas.

Responsive Design: Built with Bootstrap 5.3 for a functional experience across different screen sizes.

🛠️ Prerequisites
Python 3.8+ installed and added to your system's PATH.

pip (Python package installer) available.

Git for cloning the repository.

⚡ Installation & Setup
Clone the Repository:

# Replace 'yourusername' with the actual GitHub username
git clone https://github.com/yourusername/fixmate.git
cd fixmate

Create and Activate Virtual Environment:
(Recommended to isolate project dependencies)

# Create environment (use python or python3 depending on your system)
python -m venv venv

# Activate environment
# Linux/macOS:
source venv/bin/activate
# Windows (Command Prompt/PowerShell):
venv\Scripts\activate

(You should see (venv) at the start of your terminal prompt)

Generate and Install Dependencies:

Generate requirements.txt (if not already present): If you cloned the repo and it doesn't have requirements.txt, you can create it based on the libraries we know are needed (or use pip freeze if you installed them manually):

# Create/overwrite requirements.txt with known dependencies
echo Flask > requirements.txt
echo Werkzeug >> requirements.txt
# Add pandas and streamlit ONLY if using the optional analytics dashboard
echo pandas >> requirements.txt
echo streamlit >> requirements.txt

(Alternatively, if you installed packages manually, run pip freeze > requirements.txt to capture everything in your venv)

Install:

pip install -r requirements.txt

Configure Environment Variables (Optional but Recommended):
These help Flask find your app and enable debugging features.

# Linux/macOS:
export FLASK_APP=app.py
export FLASK_DEBUG=1 # Use 1 for debug mode, 0 for production

# Windows (Command Prompt):
set FLASK_APP=app.py
set FLASK_DEBUG=1

# Windows (PowerShell):
$env:FLASK_APP = "app.py"
$env:FLASK_DEBUG = "1"

(Setting FLASK_DEBUG=1 enables the interactive debugger and auto-reloading)

Initialize the Database:
This command uses the schema defined in app.py to create the fixmate.db file and necessary tables (users, tasks).
Warning: If fixmate.db it already exists, this command (as written in app.py) won't overwrite it unless you manually delete the file first. Deleting the file removes all existing data.

flask init-db

▶️ Running the Application
Start the Flask Server:
(Make sure your virtual environment is activated and you are in the project directory)

flask run

(This is the preferred method. python app.py might also work, but flask run uses the CLI environment correctly.)

Access the Flask App:
Open your web browser and navigate to http://127.0.0.1:5000 (or the address shown in the terminal).

Launch the Streamlit Dashboard (Optional):

Open a separate, second terminal window.

Navigate to the project directory.

Activate the virtual environment (source venv/bin/activate or venv\Scripts\activate).

Run the Streamlit app:

streamlit run analytics_dashboard.py

Access the Streamlit dashboard in your browser, usually at http://localhost:8501. The link within the main Flask app will direct you here with the correct user ID parameter.

📁 Project Structure
fixmate/
├── app.py                  # Main Flask application logic, routes, DB setup
├── analytics_dashboard.py  # Optional: Streamlit analytics application
├── requirements.txt        # Python dependencies for pip
├── fixmate.db              # SQLite database file (created by init-db)
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base layout (navbar, footer, etc.)
│   ├── dashboard.html      # User's main task view
│   ├── login.html          # Login form
│   ├── register.html       # Registration form
│   ├── task_form.html      # Form for adding/editing tasks
│   ├── task_detail.html    # View details of a single task
│   └── analytics.html      # Simple task counts page (Flask)
└── static/                 # Static assets (CSS, JS, Images)
    └── custom.css          # Custom CSS rules

🤝 Contributing
Contributions are welcome! Please follow these steps:

Fork the repository on GitHub.

Create a new branch for your feature or bug fix: git checkout -b feature/YourFeatureName or bugfix/IssueDescription.

Make your changes and commit them with clear, descriptive messages: git commit -m "Add feature: Describe the feature".

Push your changes to your forked repository: git push origin feature/YourFeatureName.

Open a Pull Request back to the main repository.

Please ensure your code adheres to project standards and includes relevant updates if necessary.