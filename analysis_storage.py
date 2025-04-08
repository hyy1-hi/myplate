import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv
from functions import get_session_key

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Initialize database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

# Create analysis_results table if it doesn't exist
def create_analysis_table():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Create analysis_results table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    analysis_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error creating analysis_results table: {e}")
            conn.close()
            return False
    return False

# Extract first line from analysis result
def extract_first_line(text):
    if not text:
        return None
    
    # Split by newline and get the first non-empty line
    lines = text.strip().split('\n')
    for line in lines:
        if line.strip():
            return line.strip()
    
    return None

# Check if analysis text already exists in database for the user
def analysis_exists(user_id, analysis_text):
    if not user_id or not analysis_text:
        return False
    
    # Check if user_id is a UUID string or an integer
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            # If user_id is a UUID string and can't be converted to int,
            # we need to handle this case differently
            return False
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 1 FROM analysis_results 
                WHERE user_id = %s AND analysis_text = %s
                LIMIT 1
            """, (user_id, analysis_text))
            
            exists = cur.fetchone() is not None
            cur.close()
            conn.close()
            return exists
        except Exception as e:
            st.error(f"Error checking if analysis exists: {e}")
            conn.close()
    return False

# Save analysis result to database
def save_analysis_result(user_id, analysis_text):
    if not user_id or not analysis_text:
        return False, "Invalid user ID or analysis text"
    
    # Check if user_id is a UUID string or an integer
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            # If user_id is a UUID string and can't be converted to int,
            # we need to handle this case differently
            return False, "Please log in to save analysis results."
    
    # Check if analysis already exists
    if analysis_exists(user_id, analysis_text):
        return True, "Analysis already exists in database"
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO analysis_results 
                (user_id, analysis_text)
                VALUES (%s, %s)
            """, (user_id, analysis_text))
            
            conn.commit()
            cur.close()
            conn.close()
            return True, "Analysis saved successfully"
        except Exception as e:
            conn.close()
            return False, f"Error saving analysis: {e}"
    return False, "Database connection error"

# Delete analysis result from database
def delete_analysis_result(user_id, analysis_text):
    if not user_id or not analysis_text:
        return False, "Invalid user ID or analysis text"
    
    # Check if user_id is a UUID string or an integer
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            # If user_id is a UUID string and can't be converted to int,
            # we need to handle this case differently
            return False, "Please log in to delete analysis results."
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM analysis_results 
                WHERE user_id = %s AND analysis_text = %s
            """, (user_id, analysis_text))
            
            # Check if any rows were affected
            if cur.rowcount > 0:
                conn.commit()
                cur.close()
                conn.close()
                return True, "Analysis deleted successfully"
            else:
                conn.rollback()
                cur.close()
                conn.close()
                return False, "Analysis not found"
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Error deleting analysis: {e}"
    return False, "Database connection error"

# Process and save analysis result
def process_analysis_result():
    # Check if user is logged in
    if not ('logged_in' in st.session_state and st.session_state.logged_in and 
            'user_id' in st.session_state and st.session_state.user_id and
            'username' in st.session_state and st.session_state.username != "Demo User"):
        return False, "User not logged in or in demo mode"
    
    # Get analysis result from session state
    session_key_analysis_result = get_session_key("analysis_result")
    if session_key_analysis_result not in st.session_state:
        return False, "No analysis result found"
    
    # Extract first line from analysis result
    analysis_text = extract_first_line(st.session_state[session_key_analysis_result])
    if not analysis_text:
        return False, "Could not extract text from analysis result"
    
    # Ensure analysis_results table exists
    create_analysis_table()
    
    # Get user_id and convert to integer if needed
    user_id = st.session_state.user_id
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            return False, "Invalid user ID format. Please log in again."
    
    # Save analysis result to database
    return save_analysis_result(user_id, analysis_text)
