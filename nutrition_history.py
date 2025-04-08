import streamlit as st
import psycopg2
import os
import pandas as pd
import altair as alt
from dotenv import load_dotenv
from functions import get_session_key
from datetime import datetime

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

# Create nutrition_history table if it doesn't exist
def create_nutrition_history_table():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Create nutrition_history table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS nutrition_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    carbs INTEGER,
                    protein INTEGER,
                    fat INTEGER,
                    calories INTEGER,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error creating nutrition_history table: {e}")
            conn.close()
            return False
    return False

# Save nutrition data to history
def save_nutrition_history(user_id, nutrition_data):
    if not user_id or not nutrition_data:
        return False, "Invalid user ID or nutrition data"
    
    # Check if user_id is a UUID string or an integer
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            # If user_id is a UUID string and can't be converted to int,
            # we need to handle this case differently
            return False, "Please log in to save nutrition history."
    
    # Ensure nutrition_history table exists
    create_nutrition_history_table()
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Insert new nutrition history record
            cur.execute("""
                INSERT INTO nutrition_history
                (user_id, carbs, protein, fat, calories)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                nutrition_data.get('carbs', 0),
                nutrition_data.get('protein', 0),
                nutrition_data.get('fat', 0),
                nutrition_data.get('calories', 0)
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            return True, "Nutrition history saved successfully"
        except Exception as e:
            conn.close()
            return False, f"Error saving nutrition history: {e}"
    return False, "Database connection error"

# Get nutrition history for a user
def get_nutrition_history(user_id, limit=30):
    if not user_id:
        return None
    
    # Check if user_id is a UUID string or an integer
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            # If user_id is a UUID string and can't be converted to int,
            # we need to handle this case differently
            return None
    
    conn = get_db_connection()
    if conn:
        try:
            # Create DataFrame to store results
            df = pd.DataFrame(columns=['date', 'carbs', 'protein', 'fat', 'calories'])
            
            cur = conn.cursor()
            # Get the latest entry for each day
            cur.execute("""
                WITH latest_entries AS (
                    SELECT 
                        carbs, protein, fat, calories, 
                        DATE(recorded_at) as entry_date,
                        ROW_NUMBER() OVER (PARTITION BY DATE(recorded_at) ORDER BY recorded_at DESC) as rn
                    FROM nutrition_history
                    WHERE user_id = %s
                )
                SELECT carbs, protein, fat, calories, entry_date
                FROM latest_entries
                WHERE rn = 1
                ORDER BY entry_date ASC
                LIMIT %s
            """, (user_id, limit))
            
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            if rows:
                # Convert to DataFrame
                df = pd.DataFrame(rows, columns=['carbs', 'protein', 'fat', 'calories', 'date'])
                # Store original date for sorting
                df['date_sort'] = pd.to_datetime(df['date'])
                # Convert date to string format for display
                df['date'] = df['date_sort'].dt.strftime('%a, %b %d')
                # Calculate percentages for each macronutrient
                total_macros = df['carbs'] + df['protein'] + df['fat']
                df['carbs_pct'] = (df['carbs'] / total_macros * 100).round().astype(int)
                df['protein_pct'] = (df['protein'] / total_macros * 100).round().astype(int)
                df['fat_pct'] = (df['fat'] / total_macros * 100).round().astype(int)
                # Keep the order with newest date last (will appear on the right in charts)
                # df = df.iloc[::-1].reset_index(drop=True)
            
            return df
        except Exception as e:
            st.error(f"Error retrieving nutrition history: {e}")
            if conn:
                conn.close()
    return None

# Display nutrition history chart
def display_nutrition_history_chart():
    # Check if user is logged in
    if not ('logged_in' in st.session_state and st.session_state.logged_in and 
            'user_id' in st.session_state and st.session_state.user_id):
        st.info("Please log in to view your nutrition history.")
        return
    
    # Get user_id and convert to integer if needed
    user_id = st.session_state.user_id
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            st.warning("Invalid user ID format. Please log in again to view your nutrition history.")
            return
    
    # Get nutrition history data
    df = get_nutrition_history(user_id)
    
    if df is not None and not df.empty:
        st.text("")
        st.subheader("Nutrients")
        
        # Add a time period selector
        time_periods = ["1W", "2W", "3W", "1M", "2M", "3M", "4M", "5M", "6M", "7M", "8M,", "9M", "10M", "11M", "1Y", "All"]
        selected_period = st.select_slider("Select Time Period", options=time_periods, value="1W")
        
        # Create a stacked bar chart for macronutrients
        # Prepare data for stacked bar chart
        df_stacked = pd.melt(
            df,
            id_vars=['date'],
            value_vars=['carbs', 'fat', 'protein'],
            var_name='nutrient',
            value_name='grams'
        )
        
        # Map nutrient names to colors matching the image
        color_scale = alt.Scale(
            domain=['carbs', 'fat', 'protein'],
            range=['#addcd6', '#f7bfac', '#f2e3d2']  # Green, Yellow, Orange
        )
        
        # Add date_sort to df_stacked for sorting
        df_stacked['date_sort'] = df_stacked.merge(df[['date', 'date_sort']], on='date')['date_sort']
        
        # Create stacked bar chart with thinner bars, sorted by date
        stacked_bar = alt.Chart(df_stacked).mark_bar(
            size=30  # Make bars thinner
        ).encode(
            x=alt.X('date:N', title=None, sort=None, axis=alt.Axis(labelAngle=0)),  # Horizontal labels
            y=alt.Y('grams:Q', title=''),
            color=alt.Color('nutrient:N', scale=color_scale, legend=None),
            tooltip=['date', 'nutrient', 'grams'],
            order=alt.Order('date_sort')  # Use date_sort for ordering
        ).properties(
            height=300
        )
        
        # Create a separate line chart for calories, sorted by date
        calories_chart = alt.Chart(df).mark_line(
            point=True,
            color='#7b8f99'
        ).encode(
            x=alt.X('date:N', title=None, sort=None, axis=alt.Axis(labelAngle=0)),  # Horizontal labels
            y=alt.Y('calories:Q', title=None),
            tooltip=['date', alt.Tooltip('calories:Q', title='Calories')],
            order=alt.Order('date_sort')  # Use date_sort for ordering
        ).properties(
            height=200
        )
        
        # Display the stacked bar chart
        st.altair_chart(stacked_bar, use_container_width=True)
        
        # Display the calories chart
        st.subheader("Calories")
        st.altair_chart(calories_chart, use_container_width=True)
    else:
        st.info("No nutrition data available. Save your nutrition requirements in **Goal** to start tracking.")
