# analytics_dashboard.py
import streamlit as st
import sqlite3
import pandas as pd

# Connect to the same SQLite database
conn = sqlite3.connect('fixmate.db')
df = pd.read_sql_query("SELECT * FROM tasks", conn)
conn.close()

st.title("FixMate Analytics Dashboard")

if df.empty:
    st.write("No tasks to display.")
else:
    st.subheader("Tasks by Category")
    st.bar_chart(df['category'].value_counts())

    st.subheader("Total Cost by Category")
    st.bar_chart(df.groupby('category')['cost'].sum())
