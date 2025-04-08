import io
from PIL import Image
import random
import uuid
import streamlit as st


def resize_image(image_bytes, max_size=(300, 300)):
    image = Image.open(io.BytesIO(image_bytes))
    image.thumbnail(max_size)
    new_image_bytes = io.BytesIO()
    image.save(new_image_bytes, format=image.format or "PNG")
    return new_image_bytes.getvalue()

def pick_random_number(lower, upper):
    return random.uniform(lower, upper)

def get_user_id():
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id

def get_session_key(base_key):
    return f"{get_user_id()}_{base_key}"

def choose_meal():
    if "meal" not in st.session_state:
        st.session_state.meal = "Other"
    option = ["Breakfast", "Lunch", "Dinner", "Snack"]
    selection = st.pills("What do you want to make?", option, key=get_session_key("meal"), selection_mode="single")
    if selection:
        st.session_state.meal = selection
    return selection

def cook_style():
    if "cook_style" not in st.session_state:
        st.session_state.cook_style = ""
    option = ["Bake", "Fry", "Grill", "Boil", "Steam", "Microwave"]
    selection = st.pills("Cooking method", option, key=get_session_key("cook_style"), selection_mode="multi")
    if selection:
        st.session_state.cook_style = selection
    return selection

def cook_time():
    if "cook_time" not in st.session_state:
        st.session_state.cook_time = 5
    selection = st.slider(
        "Cooking time (minutes)", 
        1, 60,
        step=1,
        key=get_session_key("cook_time"))
    if selection:
        st.session_state.cook_time = selection
    return selection

def ingredients():
    if "ingredients" not in st.session_state:
        st.session_state.ingredients = ""
    selection = st.slider(
        "Ingredients (kinds)",
        1, 10,
        step=1,
        key=get_session_key("ingredients"))
    if selection:
        st.session_state.ingredients = selection
    return selection

def display_habit_collection():
    if "recipe_style" not in st.session_state:
        st.session_state.cook_time = 5
    """Display the user's habit collection (diet analysis results) from the database."""
    if ('user_id' in st.session_state and st.session_state.user_id and 
        'username' in st.session_state and st.session_state.username != "Demo User"):
        from history import get_db_connection
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                # Check if user_id is a UUID string or an integer
                user_id = st.session_state.user_id
                # Try to convert user_id to integer if it's not already an integer
                if not isinstance(user_id, int):
                    try:
                        user_id = int(user_id)
                    except ValueError:
                        # If user_id is a UUID string and can't be converted to int,
                        # we need to handle this case differently
                        return None
                
                cur.execute("""
                    SELECT analysis_text, created_at 
                    FROM analysis_results 
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                
                analysis_results = cur.fetchall()
                cur.close()
                conn.close()
                
                if analysis_results:
                    # Extract all analysis texts
                    analysis_texts = [analysis for analysis, _ in analysis_results if len(analysis) < 60] 
                    # Display all analyses as pills
                    selection = st.pills(label="Recipe style", options=analysis_texts, key="recipe_habits_pills", selection_mode="multi")
                    if selection:
                        st.session_state.recipe_style = selection
                    return selection
                else:
                    st.caption("No habits found. Upload food images in the Habit tab to analyze your diet preferences.")
            except Exception as e:
                st.error(f"Error retrieving habit collection: {e}")
    else:
        pass
