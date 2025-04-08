import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv
from functions import get_session_key
from history import get_db_connection
from datetime import datetime

# Create saved_recipes table if it doesn't exist
def create_saved_recipes_table():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Create saved_recipes table if it doesn't exist
            cur.execute('''
                CREATE TABLE IF NOT EXISTS saved_recipes (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    recipe_title TEXT,
                    recipe_content TEXT,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Check if meal_type column exists, add it if it doesn't
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'saved_recipes' AND column_name = 'meal_type'
            """)
            
            if not cur.fetchone():
                # Add meal_type column if it doesn't exist
                cur.execute("ALTER TABLE saved_recipes ADD COLUMN meal_type TEXT DEFAULT 'Other'")
                st.success("Added meal_type column to saved_recipes table")
                
                # Update existing recipes with meal types based on their titles
                update_existing_recipe_meal_types()
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error creating saved_recipes table: {e}")
            conn.close()
            return False
    return False

# Update existing recipes with meal types and better titles
def update_existing_recipe_meal_types():
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Get all recipes
            cur.execute("""
                SELECT id, recipe_title, recipe_content, meal_type
                FROM saved_recipes
            """)
            
            recipes = cur.fetchall()
            
            for recipe_id, recipe_title, recipe_content, current_meal_type in recipes:
                # Determine meal type from title or content if not already set
                meal_type = current_meal_type if current_meal_type else "Other"
                lower_title = recipe_title.lower()
                lower_content = recipe_content.lower()
                
                if meal_type == "Other":
                    if 'breakfast' in lower_title or 'breakfast' in lower_content:
                        meal_type = "Breakfast"
                    elif 'lunch' in lower_title or 'lunch' in lower_content:
                        meal_type = "Lunch"
                    elif 'dinner' in lower_title or 'dinner' in lower_content:
                        meal_type = "Dinner"
                    elif 'snack' in lower_title or 'snack' in lower_content:
                        meal_type = "Snack"
                    elif any(word in lower_title for word in ['morning', 'toast', 'cereal', 'oatmeal', 'pancake']):
                        meal_type = "Breakfast"
                    elif any(word in lower_title for word in ['sandwich', 'salad', 'soup']):
                        meal_type = "Lunch"
                    elif any(word in lower_title for word in ['roast', 'steak', 'chicken', 'fish', 'supper']):
                        meal_type = "Dinner"
                    elif any(word in lower_title for word in ['cookie', 'bar', 'nuts', 'fruit']):
                        meal_type = "Snack"
                
                # Extract a better title from the content
                new_title = recipe_title
                
                # Check if the current title is just a generic meal type with nutritional info
                if (lower_title.startswith(('breakfast', 'lunch', 'dinner', 'snack')) and 
                    '(' in lower_title and 'calories' in lower_title):
                    
                    # Get the second line of the recipe content as specified by the user
                    lines = recipe_content.strip().split('\n')
                    line_index = 0
                    actual_line_count = 0
                    
                    # Find the second non-empty line
                    while line_index < len(lines) and actual_line_count < 2:
                        if lines[line_index].strip():
                            actual_line_count += 1
                        line_index += 1
                    
                    # If we found the second line, use it as the title
                    if actual_line_count == 2 and line_index > 0 and line_index <= len(lines):
                        second_line = lines[line_index - 1].strip()
                        
                        # Skip if the second line is just a header like "Ingredients:" or "Instructions:"
                        if second_line.lower() not in ['ingredients:', 'instructions:', 'directions:', 'steps:', 'method:']:
                            # Extract timestamp from original title if present
                            timestamp = ""
                            if '(' in recipe_title and ')' in recipe_title:
                                timestamp_start = recipe_title.rfind('(')
                                timestamp_end = recipe_title.rfind(')')
                                if timestamp_start > 0 and timestamp_end > timestamp_start:
                                    timestamp = recipe_title[timestamp_start:timestamp_end+1]
                            
                            # Create new title with the dish name from the second line and timestamp
                            new_title = second_line
                            if timestamp:
                                new_title = f"{new_title} {timestamp}"
                
                # Update the recipe with the determined meal type and better title
                cur.execute("""
                    UPDATE saved_recipes
                    SET meal_type = %s, recipe_title = %s
                    WHERE id = %s
                """, (meal_type, new_title, recipe_id))
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error updating recipe meal types and titles: {e}")
            if conn:
                conn.close()
            return False
    return False

# Save recipe to database
def save_recipe(user_id, recipe_content):
    if not user_id or not recipe_content:
        return False, "Invalid user ID or recipe content"
    
    # Check if user_id is a UUID string or an integer
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            # If user_id is a UUID string and can't be converted to int,
            # we need to handle this case differently
            return False, "Please log in to save recipes."
    
    # Ensure saved_recipes table exists
    create_saved_recipes_table()
    
    # Extract recipe title from content - specifically the second non-empty line as requested
    lines = recipe_content.strip().split('\n')
    recipe_title = "Saved Recipe"
    
    # Find the second non-empty line
    line_index = 0
    actual_line_count = 0
    
    while line_index < len(lines) and actual_line_count < 2:
        if lines[line_index].strip():
            actual_line_count += 1
            if actual_line_count == 2:
                second_line = lines[line_index].strip()
                # Skip if the second line is just a header like "Ingredients:" or "Instructions:"
                if second_line.lower() not in ['ingredients:', 'instructions:', 'directions:', 'steps:', 'method:']:
                    recipe_title = second_line
        line_index += 1
    
    # If we couldn't find a second line or it was a header, fall back to the first line
    if recipe_title == "Saved Recipe" and lines:
        recipe_title = lines[0]
    
    # Remove markdown formatting if present
    recipe_title = recipe_title.replace('#', '').replace('*', '').strip()
    # Limit title length
    recipe_title = recipe_title[:100] if len(recipe_title) > 100 else recipe_title
    
    # Determine meal type from title or content
    meal_type = "Other"
    lower_title = recipe_title.lower()
    lower_content = recipe_content.lower()
    
    if 'breakfast' in lower_title or 'breakfast' in lower_content:
        meal_type = "Breakfast"
    elif 'lunch' in lower_title or 'lunch' in lower_content:
        meal_type = "Lunch"
    elif 'dinner' in lower_title or 'dinner' in lower_content:
        meal_type = "Dinner"
    elif 'snack' in lower_title or 'snack' in lower_content:
        meal_type = "Snack"
    elif any(word in lower_title for word in ['morning', 'toast', 'cereal', 'oatmeal', 'pancake']):
        meal_type = "Breakfast"
    elif any(word in lower_title for word in ['sandwich', 'salad', 'soup']):
        meal_type = "Lunch"
    elif any(word in lower_title for word in ['roast', 'steak', 'chicken', 'fish', 'supper']):
        meal_type = "Dinner"
    elif any(word in lower_title for word in ['cookie', 'bar', 'nuts', 'fruit']):
        meal_type = "Snack"
    
    # Check if meal type is in session state (from the meal selection in the Recipe tab)
    try:
        if hasattr(st.session_state, 'meal') and st.session_state.meal:
            session_meal = st.session_state.meal.lower()
            if 'breakfast' in session_meal:
                meal_type = "Breakfast"
            elif 'lunch' in session_meal:
                meal_type = "Lunch"
            elif 'dinner' in session_meal:
                meal_type = "Dinner"
            elif 'snack' in session_meal:
                meal_type = "Snack"
    except Exception as e:
        # If there's any error accessing the meal attribute, just use the meal type determined above
        pass
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Always insert a new recipe entry
            # Add timestamp to recipe title to ensure uniqueness
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            recipe_title_with_time = f"{recipe_title} ({timestamp})"
            
            # Insert new recipe with meal type
            cur.execute("""
                INSERT INTO saved_recipes
                (user_id, recipe_title, recipe_content, meal_type)
                VALUES (%s, %s, %s, %s)
            """, (user_id, recipe_title_with_time, recipe_content, meal_type))
            message = "Recipe saved successfully"
            
            conn.commit()
            cur.close()
            conn.close()
            return True, message
        except Exception as e:
            conn.close()
            return False, f"Error saving recipe: {e}"
    return False, "Database connection error"

# Get saved recipes for a user
def get_saved_recipes(user_id):
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
    
    # Ensure saved_recipes table exists
    create_saved_recipes_table()
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Get all saved recipes for the user
            cur.execute("""
                SELECT id, recipe_title, recipe_content, meal_type, saved_at
                FROM saved_recipes
                WHERE user_id = %s
                ORDER BY meal_type, saved_at DESC
            """, (user_id,))
            
            recipes = cur.fetchall()
            cur.close()
            conn.close()
            
            return recipes
        except Exception as e:
            st.error(f"Error retrieving saved recipes: {e}")
            if conn:
                conn.close()
    return None

# Delete a saved recipe
def delete_saved_recipe(recipe_id, user_id):
    if not recipe_id or not user_id:
        return False, "Invalid recipe ID or user ID"
    
    # Check if user_id is a UUID string or an integer
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except ValueError:
            # If user_id is a UUID string and can't be converted to int,
            # we need to handle this case differently
            return False, "Please log in to delete recipes."
    
    # Ensure saved_recipes table exists
    create_saved_recipes_table()
    
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Delete the recipe (ensuring it belongs to the user)
            cur.execute("""
                DELETE FROM saved_recipes
                WHERE id = %s AND user_id = %s
                RETURNING id
            """, (recipe_id, user_id))
            
            deleted = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            
            if deleted:
                return True, "Recipe deleted successfully"
            else:
                return False, "Recipe not found or not owned by user"
        except Exception as e:
            conn.close()
            return False, f"Error deleting recipe: {e}"
    return False, "Database connection error"

# Display saved recipes in the profile tab
def display_saved_recipes():
    # Check if user is logged in
    if not ('logged_in' in st.session_state and st.session_state.logged_in and 
            'user_id' in st.session_state and st.session_state.user_id):
        return
    
    try:
        # Ensure saved_recipes table exists
        create_saved_recipes_table()
        
        # Get user_id and convert to integer if needed
        user_id = st.session_state.user_id
        if not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except ValueError:
                st.warning("Invalid user ID format. Please log in again to view your saved recipes.")
                return
        
        # Get saved recipes
        recipes = get_saved_recipes(user_id)
        
        if recipes and len(recipes) > 0:
            # Group recipes by meal type
            breakfast_recipes = []
            lunch_recipes = []
            dinner_recipes = []
            snack_recipes = []
            other_recipes = []
            
            for recipe in recipes:
                recipe_id, recipe_title, recipe_content, meal_type, saved_at = recipe
                if meal_type == "Breakfast":
                    breakfast_recipes.append(recipe)
                elif meal_type == "Lunch":
                    lunch_recipes.append(recipe)
                elif meal_type == "Dinner":
                    dinner_recipes.append(recipe)
                elif meal_type == "Snack":
                    snack_recipes.append(recipe)
                else:
                    other_recipes.append(recipe)
            
            # Create tabs for each meal type
            breakfast_tab, lunch_tab, dinner_tab, snack_tab, other_tab = st.tabs([
                f"Breakfast ({len(breakfast_recipes)})", 
                f"Lunch ({len(lunch_recipes)})", 
                f"Dinner ({len(dinner_recipes)})", 
                f"Snack ({len(snack_recipes)})",
                f"Other ({len(other_recipes)})"
            ])
            
            # Display recipes in each tab
            with breakfast_tab:
                if breakfast_recipes:
                    for recipe_id, recipe_title, recipe_content, meal_type, saved_at in breakfast_recipes:
                        with st.expander(f"{recipe_title}"):
                            st.markdown(recipe_content)
                            if st.button(f"Delete", key=f"delete_breakfast_{recipe_id}"):
                                success, message = delete_saved_recipe(recipe_id, st.session_state.user_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.info("No breakfast recipes saved yet.")
            
            with lunch_tab:
                if lunch_recipes:
                    for recipe_id, recipe_title, recipe_content, meal_type, saved_at in lunch_recipes:
                        with st.expander(f"{recipe_title}"):
                            st.markdown(recipe_content)
                            if st.button(f"Delete", key=f"delete_lunch_{recipe_id}"):
                                success, message = delete_saved_recipe(recipe_id, st.session_state.user_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.info("No lunch recipes saved yet.")
            
            with dinner_tab:
                if dinner_recipes:
                    for recipe_id, recipe_title, recipe_content, meal_type, saved_at in dinner_recipes:
                        with st.expander(f"{recipe_title}"):
                            st.markdown(recipe_content)
                            if st.button(f"Delete", key=f"delete_dinner_{recipe_id}"):
                                success, message = delete_saved_recipe(recipe_id, st.session_state.user_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.info("No dinner recipes saved yet.")
            
            with snack_tab:
                if snack_recipes:
                    for recipe_id, recipe_title, recipe_content, meal_type, saved_at in snack_recipes:
                        with st.expander(f"{recipe_title}"):
                            st.markdown(recipe_content)
                            if st.button(f"Delete", key=f"delete_snack_{recipe_id}"):
                                success, message = delete_saved_recipe(recipe_id, st.session_state.user_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.info("No snack recipes saved yet.")
            
            with other_tab:
                if other_recipes:
                    for recipe_id, recipe_title, recipe_content, meal_type, saved_at in other_recipes:
                        with st.expander(f"{recipe_title}"):
                            st.markdown(recipe_content)
                            if st.button(f"Delete", key=f"delete_other_{recipe_id}"):
                                success, message = delete_saved_recipe(recipe_id, st.session_state.user_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.info("No other recipes saved yet.")
        else:
            st.info("No saved recipes found. Save recipes from the Recipe tab to see them here.")
    except Exception as e:
        st.error(f"Error displaying saved recipes: {e}")
