import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv
from passlib.hash import pbkdf2_sha256
import re

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
        # First try to connect to the default 'postgres' database to create our database if it doesn't exist
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database="postgres",  # Connect to default database first
                user=DB_USER,
                password=DB_PASSWORD
            )
            conn.autocommit = True  # Set autocommit to create database
            cur = conn.cursor()
            
            # Check if our database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
            if cur.fetchone() is None:
                # Create database if it doesn't exist
                cur.execute(f"CREATE DATABASE {DB_NAME}")
            
            cur.close()
            conn.close()
        except Exception as e:
            st.warning(f"Could not create database: {e}")
            # Continue anyway to try connecting to the database if it already exists
        
        # Now connect to our application database
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
        st.info("Please make sure PostgreSQL is installed and running with the credentials specified in the .env file.")
        return None

# Create database tables if they don't exist
def create_tables():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Create users table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create user_profiles table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(100),
                    age INTEGER,
                    gender VARCHAR(20),
                    weight FLOAT,
                    height FLOAT,
                    activity_level VARCHAR(50),
                    goal VARCHAR(50),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id)
                )
            ''')
            
            # Create user_nutrition table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS user_nutrition (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    carbs INTEGER,
                    protein INTEGER,
                    fat INTEGER,
                    calories INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id)
                )
            ''')
            
            # Create analysis_results table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    analysis_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create feedback table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    rating FLOAT NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error creating tables: {e}")
            conn.close()
            return False
    return False

# Initialize the database
def init_db():
    if create_tables():
        return True
    return False

# Save user profile to database
def save_user_profile(user_id, profile_data):
    if not user_id or not profile_data:
        return False, "Invalid user ID or profile data"
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Save basic profile information
            cur.execute("""
                INSERT INTO user_profiles 
                (user_id, name, age, gender, weight, height, activity_level, goal)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    age = EXCLUDED.age,
                    gender = EXCLUDED.gender,
                    weight = EXCLUDED.weight,
                    height = EXCLUDED.height,
                    activity_level = EXCLUDED.activity_level,
                    goal = EXCLUDED.goal,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                user_id, 
                profile_data.get('name', ''),
                profile_data.get('age', 0),
                profile_data.get('gender', 'Male'),
                profile_data.get('weight', 0.0),
                profile_data.get('height', 0.0),
                profile_data.get('activity_level', 'Moderately Active'),
                profile_data.get('goal', 'Stay Active')
            ))
            
            # Save nutrition information if available
            if 'nutrition' in profile_data:
                nutrition = profile_data['nutrition']
                cur.execute("""
                    INSERT INTO user_nutrition
                    (user_id, carbs, protein, fat, calories)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id)
                    DO UPDATE SET
                        carbs = EXCLUDED.carbs,
                        protein = EXCLUDED.protein,
                        fat = EXCLUDED.fat,
                        calories = EXCLUDED.calories,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    user_id,
                    nutrition.get('carbs', 0),
                    nutrition.get('protein', 0),
                    nutrition.get('fat', 0),
                    nutrition.get('calories', 0)
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            return True, "Profile saved successfully"
        except Exception as e:
            conn.close()
            return False, f"Error saving profile: {e}"
    return False, "Database connection error"

# Get user profile from database
def get_user_profile(user_id):
    if not user_id:
        return None
    
    conn = get_db_connection()
    if conn:
        try:
            profile = {
                'name': '',
                'age': 0,
                'gender': 'Male',
                'weight': 0.0,
                'height': 0.0,
                'activity_level': 'Moderately Active',
                'goal': 'Stay Active',
                'nutrition': {
                    'carbs': 0,
                    'protein': 0,
                    'fat': 0,
                    'calories': 0
                }
            }
            
            cur = conn.cursor()
            
            # Get basic profile information
            cur.execute("""
                SELECT name, age, gender, weight, height, activity_level, goal
                FROM user_profiles
                WHERE user_id = %s
            """, (user_id,))
            
            profile_data = cur.fetchone()
            if profile_data:
                profile['name'] = profile_data[0]
                profile['age'] = profile_data[1]
                profile['gender'] = profile_data[2]
                profile['weight'] = profile_data[3]
                profile['height'] = profile_data[4]
                profile['activity_level'] = profile_data[5]
                profile['goal'] = profile_data[6]
            
            # Get nutrition information
            cur.execute("""
                SELECT carbs, protein, fat, calories
                FROM user_nutrition
                WHERE user_id = %s
            """, (user_id,))
            
            nutrition_data = cur.fetchone()
            if nutrition_data:
                profile['nutrition']['carbs'] = nutrition_data[0]
                profile['nutrition']['protein'] = nutrition_data[1]
                profile['nutrition']['fat'] = nutrition_data[2]
                profile['nutrition']['calories'] = nutrition_data[3]
            
            cur.close()
            conn.close()
            return profile
        except Exception as e:
            st.error(f"Error retrieving profile: {e}")
            conn.close()
    return None

# User registration function
def register_user(username, email, password):
    # Validate inputs
    if not username or not email or not password:
        return False, "All fields are required", None
    
    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email format", None
    
    # Validate password strength
    if len(password) < 8:
        return False, "Password must be at least 8 characters long", None
    
    # Hash the password
    password_hash = pbkdf2_sha256.hash(password)
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Check if username or email already exists
            cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            if cur.fetchone():
                cur.close()
                conn.close()
                return False, "Username or email already exists", None
            
            # Insert new user
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (username, email, password_hash)
            )
            user_id = cur.fetchone()[0]  # Get the newly created user ID
            conn.commit()
            cur.close()
            conn.close()
            return True, "Registration successful", user_id
        except Exception as e:
            conn.close()
            return False, f"Registration error: {e}", None
    return False, "Database connection error", None

# User login function
def login_user(username, password):
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            if user and pbkdf2_sha256.verify(password, user[2]):
                return True, user[0], user[1]  # Success, user_id, username
            else:
                return False, None, None  # Failed login
        except Exception as e:
            conn.close()
            return False, None, f"Login error: {e}"
    return False, None, "Database connection error"

# Check if PostgreSQL is available
def is_postgres_available():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=3  # Short timeout to check availability
        )
        conn.close()
        return True
    except:
        return False

# Import profile data from session state to database
def import_profile_from_session(user_id):
    from functions import get_session_key
    
    session_key_profile = get_session_key("profile")
    if session_key_profile in st.session_state:
        profile_data = st.session_state[session_key_profile]
        success, message = save_user_profile(user_id, profile_data)
        if not success:
            st.warning(f"Could not save profile data: {message}")

# Sync profile data between database and session state
def sync_profile_with_session(user_id):
    from functions import get_session_key
    
    session_key_profile = get_session_key("profile")
    
    # Get profile from database
    db_profile = get_user_profile(user_id)
    
    if db_profile:
        # If profile exists in database, update session state
        if session_key_profile not in st.session_state:
            # No session profile, use database profile
            st.session_state[session_key_profile] = db_profile
        else:
            # Merge database and session profiles, prioritizing non-empty values
            session_profile = st.session_state[session_key_profile]
            merged_profile = {
                'name': session_profile.get('name') or db_profile.get('name', ''),
                'age': session_profile.get('age') or db_profile.get('age', 0),
                'gender': session_profile.get('gender') or db_profile.get('gender', 'Male'),
                'weight': session_profile.get('weight') or db_profile.get('weight', 0.0),
                'height': session_profile.get('height') or db_profile.get('height', 0.0),
                'activity_level': session_profile.get('activity_level') or db_profile.get('activity_level', 'Moderately Active'),
                'goal': session_profile.get('goal') or db_profile.get('goal', 'Stay Active'),
            }
            
            # Merge nutrition data
            session_nutrition = session_profile.get('nutrition', {})
            db_nutrition = db_profile.get('nutrition', {})
            
            # Always prioritize database nutrition data if it exists and has non-zero values
            if db_nutrition and any(db_nutrition.values()):
                merged_profile['nutrition'] = db_nutrition
            else:
                # Fall back to session nutrition if database nutrition is empty or all zeros
                merged_profile['nutrition'] = session_nutrition
            
            # Update session state with merged profile
            st.session_state[session_key_profile] = merged_profile
            
            # Save merged profile to database to ensure consistency
            save_user_profile(user_id, merged_profile)
    else:
        # If no profile in database but exists in session, save to database
        if session_key_profile in st.session_state:
            save_user_profile(user_id, st.session_state[session_key_profile])

# User profile page
def user_profile():
    # Initialize session state variables if they don't exist
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "login"
    if 'profile_synced' not in st.session_state:
        st.session_state.profile_synced = False
    
    # Check if PostgreSQL is available
    postgres_available = is_postgres_available()
    
    if not postgres_available:
        st.error("PostgreSQL database is not available.")
        st.info("""
        To use the sign-in/sign-up functionality, please:
        1. Install PostgreSQL if not already installed
        2. Make sure PostgreSQL service is running
        3. Check the database connection details in the .env file
        """)
        
        # Provide a demo mode option
        if st.button("Continue in Demo Mode"):
            st.session_state.logged_in = True
            st.session_state.username = "Demo User"
            st.rerun()
        return
    
    # Initialize database
    init_db()
    
    # Create tabs for login and registration
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        # Login tab
        with tab1:
            st.subheader("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", key="login_button"):
                if username and password:
                    success, user_id, user = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.username = user
                        
                        # Check if there's profile data in session state that needs to be saved
                        from functions import get_session_key
                        session_key_profile = get_session_key("profile")
                        
                        if session_key_profile in st.session_state:
                            # Save current session profile data to database
                            profile_data = st.session_state[session_key_profile]
                            if profile_data.get('name') or ('nutrition' in profile_data and profile_data['nutrition'].get('calories', 0) > 0):
                                save_user_profile(user_id, profile_data)
                        
                        st.session_state.profile_synced = False  # Mark for sync on next render
                        st.success(f"Welcome back, {user}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
        
        # Registration tab
        with tab2:
            st.subheader("Create an Account")
            new_username = st.text_input("Username", key="reg_username")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            if st.button("Sign Up", key="signup_button"):
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message, user_id = register_user(new_username, new_email, new_password)
                    if success:
                        # Automatically log in the user
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.username = new_username
                        
                        # Check if there's profile data in session state that needs to be saved
                        from functions import get_session_key
                        session_key_profile = get_session_key("profile")
                        
                        if session_key_profile in st.session_state:
                            # Save current session profile data to database
                            profile_data = st.session_state[session_key_profile]
                            if profile_data.get('name') or ('nutrition' in profile_data and profile_data['nutrition'].get('calories', 0) > 0):
                                save_user_profile(user_id, profile_data)
                        
                        st.session_state.profile_synced = False  # Mark for sync on next render
                        st.success(f"Registration successful! Welcome, {new_username}!")
                        st.rerun()
                    else:
                        st.error(message)
    
    # User profile display when logged in
    else:
        # Sync profile data with database if not already synced
        if not st.session_state.profile_synced and st.session_state.user_id and st.session_state.username != "Demo User":
            sync_profile_with_session(st.session_state.user_id)
            st.session_state.profile_synced = True
        
        st.text("")

        st.subheader(f"Welcome {st.session_state.username}!")
        
        # Display user information
        if st.session_state.username == "Demo User":
            st.write("You are currently in demo mode. Database functionality is limited.")
        else:
            # Add user history sections
            st.text("")
            st.subheader("Habit Collection")
            # Display saved analysis results
            if st.session_state.user_id and st.session_state.username != "Demo User":
                conn = get_db_connection()
                if conn:
                    try:
                        cur = conn.cursor()
                        cur.execute("""
                            SELECT analysis_text, created_at 
                            FROM analysis_results 
                            WHERE user_id = %s
                            ORDER BY created_at DESC
                        """, (st.session_state.user_id,))
                        
                        analysis_results = cur.fetchall()
                        cur.close()
                        conn.close()
                        
                        if analysis_results:
                            # Create a container for the pills
                            # Extract all analysis texts
                            analysis_texts = [analysis for analysis, _ in analysis_results if len(analysis) < 20] 
                            # Display all analyses as pills
                            st.pills(label="", options=analysis_texts, key="analysis_pills")
                        else:
                            st.info("No Habit found. Upload food images in the Habit tab to analyze your diet preferences.")
                            
                    except Exception as e:
                        st.error(f"Error retrieving analysis history: {e}")
            else:
                st.info("Login to view your diet analysis history.")
            
            st.text("")
            st.subheader("Liked Recipes")
            
            # Display user profile information after Liked Recipes
            st.text("")
            st.subheader("Profile Information")
            a = st.container(border=True)
            
            # Get user information from database
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("SELECT username, password_hash, email, created_at FROM users WHERE id = %s", (st.session_state.user_id,))
                    user_info = cur.fetchone()
                    cur.close()
                    conn.close()
                    
                    if user_info:
                        username, password_hash, email, created_at = user_info
                        a.write(f"Username: {username}")
                        a.write(f"Password: {'*' * 8}")  # Don't display actual password for security
                        a.write(f"Email: {email}")
                        a.write(f"Account created: {created_at}")
 
                        if a.button("Update User Information"):
                            st.session_state.show_update_form = True
        
                        if st.button("Logout"):
                                # Save profile data before logging out
                                if st.session_state.user_id and st.session_state.username != "Demo User":
                                    from functions import get_session_key
                                    session_key_profile = get_session_key("profile")
                                    if session_key_profile in st.session_state:
                                        save_user_profile(st.session_state.user_id, st.session_state[session_key_profile])
                                
                                st.session_state.logged_in = False
                                st.session_state.user_id = None
                                st.session_state.username = None
                                st.session_state.profile_synced = False
                                st.rerun()
                        
                        # Show update form when button is clicked
                        if 'show_update_form' not in st.session_state:
                            st.session_state.show_update_form = False
                            
                        if st.session_state.show_update_form:
                            with st.form("update_user_info"):
                                st.subheader("Update User Information")
                                new_username = st.text_input("New Username", value=username)
                                new_email = st.text_input("New Email", value=email)
                                new_password = st.text_input("New Password", type="password", 
                                                           help="Leave blank to keep current password")
                                confirm_password = st.text_input("Confirm New Password", type="password")
                                
                                update_submitted = st.form_submit_button("Save Changes")
                                
                                if update_submitted:
                                    # Validate inputs
                                    if new_username and new_email:
                                        # Validate email format
                                        if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                                            st.error("Invalid email format")
                                        else:
                                            # Check if new password was provided
                                            update_password = False
                                            if new_password:
                                                if new_password != confirm_password:
                                                    st.error("Passwords do not match")
                                                elif len(new_password) < 8:
                                                    st.error("Password must be at least 8 characters long")
                                                else:
                                                    update_password = True
                                            
                                            # Update user information in database
                                            try:
                                                conn = get_db_connection()
                                                if conn:
                                                    cur = conn.cursor()
                                                    
                                                    # Check if username or email already exists (except for current user)
                                                    cur.execute(
                                                        "SELECT id FROM users WHERE (username = %s OR email = %s) AND id != %s", 
                                                        (new_username, new_email, st.session_state.user_id)
                                                    )
                                                    
                                                    if cur.fetchone():
                                                        st.error("Username or email already exists")
                                                    else:
                                                        # Update username and email
                                                        if update_password:
                                                            # Hash the new password
                                                            password_hash = pbkdf2_sha256.hash(new_password)
                                                            
                                                            # Update all fields including password
                                                            cur.execute(
                                                                "UPDATE users SET username = %s, email = %s, password_hash = %s WHERE id = %s",
                                                                (new_username, new_email, password_hash, st.session_state.user_id)
                                                            )
                                                        else:
                                                            # Update only username and email
                                                            cur.execute(
                                                                "UPDATE users SET username = %s, email = %s WHERE id = %s",
                                                                (new_username, new_email, st.session_state.user_id)
                                                            )
                                                        
                                                        conn.commit()
                                                        
                                                        # Update session state if username changed
                                                        if new_username != username:
                                                            st.session_state.username = new_username
                                                        
                                                        st.success("User information updated successfully!")
                                                        st.session_state.show_update_form = False
                                                        st.rerun()
                                                    
                                                    cur.close()
                                                    conn.close()
                                            except Exception as e:
                                                st.error(f"Error updating user information: {e}")
                                    else:
                                        st.warning("Username and email are required")
                except Exception as e:
                    st.error(f"Error retrieving user information: {e}")

# Legacy function for backward compatibility
def hello():
    user_profile()

# Function to save profile data when updated in the app
def save_profile_data():
    # Only save if user is logged in and not in demo mode
    if ('logged_in' in st.session_state and st.session_state.logged_in and 
        'user_id' in st.session_state and st.session_state.user_id and
        'username' in st.session_state and st.session_state.username != "Demo User"):
        
        from functions import get_session_key
        session_key_profile = get_session_key("profile")
        
        if session_key_profile in st.session_state:
            profile_data = st.session_state[session_key_profile]
            success, message = save_user_profile(st.session_state.user_id, profile_data)
            return success, message
    
    return False, "User not logged in or in demo mode"

# Function to save feedback to the database
def save_feedback(rating, comment):
    """
    Save user feedback to the database.
    
    Args:
        rating (float): User rating from 0 to 10
        comment (str): User comment text
        
    Returns:
        tuple: (success, message)
    """
    # Get user_id if logged in
    user_id = None
    if ('logged_in' in st.session_state and st.session_state.logged_in and 
        'user_id' in st.session_state and st.session_state.user_id and
        st.session_state.username != "Demo User"):
        user_id = st.session_state.user_id
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Insert feedback
            cur.execute("""
                INSERT INTO feedback (user_id, rating, comment)
                VALUES (%s, %s, %s)
            """, (user_id, rating, comment))
            
            conn.commit()
            cur.close()
            conn.close()
            return True, "Feedback saved successfully"
        except Exception as e:
            conn.close()
            return False, f"Error saving feedback: {e}"
    return False, "Database connection error"

# Function to get average rating
def get_average_rating():
    """
    Get the average rating from all feedback.
    
    Returns:
        float or None: Average rating or None if no ratings
    """
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Get average rating
            cur.execute("SELECT AVG(rating) FROM feedback")
            
            avg_rating = cur.fetchone()[0]
            cur.close()
            conn.close()
            
            return avg_rating
        except Exception as e:
            st.error(f"Error retrieving average rating: {e}")
            conn.close()
    return None

# Function to get recent comments
def get_recent_comments(limit=5):
    """
    Get recent comments from feedback.
    
    Args:
        limit (int): Maximum number of comments to retrieve
        
    Returns:
        list: List of tuples (comment, rating, created_at)
    """
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Get recent comments
            cur.execute("""
                SELECT comment, rating, created_at 
                FROM feedback 
                WHERE comment IS NOT NULL AND comment != ''
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            comments = cur.fetchall()
            cur.close()
            conn.close()
            
            return comments
        except Exception as e:
            st.error(f"Error retrieving recent comments: {e}")
            conn.close()
    return []
