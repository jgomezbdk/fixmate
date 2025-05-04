import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os # To construct absolute path

# --- Configuration ---
# Assumes fixmate.db is in the same directory as this script
DATABASE_FILENAME = 'fixmate.db'
st.set_page_config(page_title="My FixMate Analytics", layout="wide")
st.title("📊 FixMate - My Task Analytics")

# --- Get User ID from URL Query Parameter ---
query_params = st.query_params
try:
    # Attempt to get user_id and convert to integer
    # .get returns a list, take the first element [0] if it exists
    user_id_str = query_params.get("user_id", [None])[0]
    user_id = int(user_id_str) if user_id_str is not None else None
except (TypeError, ValueError):
    user_id = None # Handle cases where conversion fails

if user_id is None:
    st.error("🚫 Error: User ID not provided or invalid in the URL.")
    st.info("Please access this dashboard via the link in the main FixMate application.")
    st.stop() # Halt execution if no valid user_id

# --- Database Connection Function (Cached) ---
@st.cache_resource # Cache the connection for efficiency
def get_connection(db_file):
    db_path = os.path.abspath(db_file)
    print(f"Connecting to Streamlit DB at: {db_path}") # For debugging path
    return sqlite3.connect(db_path, check_same_thread=False) # check_same_thread=False needed for Streamlit

# --- Data Loading Function (Filtered by user_id, Cached) ---
@st.cache_data # Cache the data based on user_id (reruns if user_id changes)
def load_user_data(user_id_param):
    """Loads tasks specifically for the given user ID."""
    conn = get_connection(DATABASE_FILENAME)
    try:
        # Select only tasks for the specific user
        query = "SELECT * FROM tasks WHERE user_id = ?"
        # Use params argument for safe query parameterization
        df = pd.read_sql_query(query, conn, params=(user_id_param,))

        # --- Data Type Conversions & Cleaning ---
        # Convert due_date, coercing errors to NaT (Not a Time)
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
        # Convert cost, coercing errors to NaN (Not a Number)
        df['cost'] = pd.to_numeric(df['cost'], errors='coerce')
        # Convert completed, filling missing values with 0, ensuring integer type
        df['completed'] = pd.to_numeric(df['completed'], errors='coerce').fillna(0).astype(int)
        # Ensure category is string, fill missing with 'Uncategorized'
        df['category'] = df['category'].fillna('Uncategorized').astype(str)

        print(f"Loaded {len(df)} tasks for user_id {user_id_param}") # Debug output
        return df
    except Exception as e:
        st.error(f"🚨 Error loading data from database: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

# --- Load Data for the specific user ---
df_user = load_user_data(user_id)

# --- Display Username (Optional but nice) ---
try:
    conn = get_connection(DATABASE_FILENAME)
    user_info = pd.read_sql_query("SELECT username FROM users WHERE id = ?", conn, params=(user_id,))
    if not user_info.empty:
        st.subheader(f"Analytics for User: {user_info['username'].iloc[0]}")
    else:
        st.warning("Could not retrieve username for this ID.")
except Exception as e:
     st.warning(f"Could not retrieve username: {e}")


# --- Handle No Tasks ---
if df_user.empty:
    st.warning(f"🤷 No tasks found for you (User ID {user_id}). Add some tasks in the main FixMate application!")
    st.stop() # Stop execution if there's no data to analyze

# --- Display Metrics ---
st.markdown("---")
st.subheader("📊 Overall Summary")
total_tasks = len(df_user)
completed_tasks = df_user['completed'].sum() # Summing 0s and 1s gives count of 1s
pending_tasks = total_tasks - completed_tasks

col1, col2, col3 = st.columns(3)
col1.metric("Total Tasks", total_tasks)
col2.metric("Completed Tasks", completed_tasks)
col3.metric("Pending Tasks", pending_tasks)

# --- Visualization Columns ---
st.markdown("---")
col_viz1, col_viz2 = st.columns(2)

with col_viz1:
    # --- Completion Status Chart ---
    st.subheader("📈 Completion Status")
    completion_status = df_user['completed'].map({0: 'Pending', 1: 'Complete'}).value_counts()
    # Ensure both categories exist for consistent charting
    if 'Pending' not in completion_status: completion_status['Pending'] = 0
    if 'Complete' not in completion_status: completion_status['Complete'] = 0
    st.bar_chart(completion_status)

    # --- Cost Analysis ---
    st.subheader("💰 Cost Overview")
    valid_costs = df_user['cost'].dropna() # Ignore tasks without cost
    if not valid_costs.empty:
        total_cost = valid_costs.sum()
        avg_cost = valid_costs.mean()
        cost_m1, cost_m2 = st.columns(2)
        cost_m1.metric("Total Estimated Cost", f"${total_cost:,.2f}")
        cost_m2.metric("Avg Cost per Task", f"${avg_cost:,.2f}")
    else:
        st.info("No cost data entered for your tasks.")

with col_viz2:
    # --- Tasks per Category ---
    st.subheader("📁 Tasks by Category")
    category_counts = df_user['category'].value_counts()
    if not category_counts.empty:
        st.bar_chart(category_counts)
        # Expander for table view
        with st.expander("View Category Counts Table"):
            st.dataframe(category_counts)
    else:
        st.info("No categories assigned to your tasks.")

# --- Upcoming & Overdue Tasks ---
st.markdown("---")
st.subheader("⏰ Due Dates Analysis")
today = pd.Timestamp(datetime.now().date()) # Get today's date without time
upcoming_cutoff = today + timedelta(days=7) # Example: tasks due within next 7 days

# Filter tasks that have a valid due date AND are not completed
df_dated_pending = df_user.dropna(subset=['due_date'])
df_dated_pending = df_dated_pending[df_dated_pending['completed'] == 0]

upcoming_tasks = df_dated_pending[
    (df_dated_pending['due_date'] >= today) &
    (df_dated_pending['due_date'] <= upcoming_cutoff)
]
overdue_tasks = df_dated_pending[df_dated_pending['due_date'] < today]

due_col1, due_col2 = st.columns(2)
with due_col1:
    st.markdown("**🚨 Overdue Tasks**")
    if not overdue_tasks.empty:
        st.dataframe(overdue_tasks[['title', 'due_date', 'category']].sort_values(by='due_date'))
    else:
        st.success("✅ No overdue tasks!")

with due_col2:
    st.markdown(f"**📅 Upcoming Tasks (Next 7 Days)**")
    if not upcoming_tasks.empty:
        st.dataframe(upcoming_tasks[['title', 'due_date', 'category']].sort_values(by='due_date'))
    else:
        st.info("📭 No tasks due soon.")

# --- Raw Data View (Filtered for the user) ---
st.markdown("---")
with st.expander("📋 View Your Raw Task Data"):
    st.dataframe(df_user)

st.caption("End of Report")
