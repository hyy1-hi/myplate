import streamlit as st
import base64
import time
import os
import re
import pandas as pd
from PIL import Image
from dotenv import load_dotenv
from prompts import prompt1
import google.generativeai as genai
from passlib.hash import pbkdf2_sha256
from functions import resize_image, pick_random_number, get_session_key, choose_meal, cook_style, cook_time, ingredients
from feedback import feedback, recent_commend, feedback_score
from history import hello, save_profile_data, save_user_profile, get_db_connection
from recommandation import recommandation2
from analysis_storage import process_analysis_result
from rank import popular_habits, new_habits
from nutrition_history import save_nutrition_history, display_nutrition_history_chart

img = Image.open("Logo.png")


st.set_page_config(
    page_title="My Plate",
    page_icon=img,
    )

# Part 1: Image Upload and Gallery
def image_upload():
    session_key_uploaded_images = get_session_key("uploaded_images")


    if session_key_uploaded_images not in st.session_state:
        st.session_state[session_key_uploaded_images] = []

    uploaded_files = st.file_uploader(
        "Please upload 3 to 6 images", 
        type=['jpg', 'jpeg', 'png', 'webp'], 
        accept_multiple_files=True,
        key=get_session_key("file_uploader")
    )

    # Clear the session state if no files are uploaded
    if uploaded_files is None or len(uploaded_files) == 0:
        st.session_state[session_key_uploaded_images] = []
    elif uploaded_files:
        st.session_state[session_key_uploaded_images] = []
        for file in uploaded_files:
            image_bytes = file.read()
            resized_image_bytes = resize_image(image_bytes)  # Resize before storing
            st.session_state[session_key_uploaded_images].append(resized_image_bytes)
        uploaded_files = []
        
    return st.session_state[session_key_uploaded_images]
    # Return the resized images

@st.fragment
def images_displayed():
    session_key_uploaded_images = get_session_key("uploaded_images")

    if st.button("Show Images", key=get_session_key("show_button")):
        cols = st.columns(6)
        for i, image_bytes in enumerate(st.session_state[session_key_uploaded_images]):
            with cols[i % 6]:
                st.image(image_bytes) 

# Part 2: Gemini Analysis
@st.fragment
def images_analysis():
    session_key_uploaded_images = get_session_key("uploaded_images")
    session_key_analysis_result = get_session_key("analysis_result")
    
    num_images = len(st.session_state[session_key_uploaded_images])
    
    if st.button('Analyze', key=get_session_key("analyze_button")):
        if 3 <= num_images <= 6:
            with st.spinner("Analyzing your dietary preference..."):

                load_dotenv()
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])

                generation_config = {
                    "temperature": 1.0,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 300,
                    "response_mime_type": "text/plain",
                }

                model = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    generation_config=generation_config,
                )

                chat_session = model.start_chat(history=[])

                # Prepare the message content with text and images
                message_parts = [str(prompt1)]  # Start with the prompt text
                
                # Add each image as a separate part
                for image_bytes in st.session_state[session_key_uploaded_images]:
                    base64_encoded = base64.b64encode(image_bytes).decode()
                    message_parts.append({
                        "mime_type": "image/jpeg",
                        "data": base64_encoded
                    })
                
                # Send the multipart message to Gemini
                response = chat_session.send_message(message_parts)

                st.markdown(response.text)

                st.session_state[session_key_analysis_result] = response.text
                
                # Save analysis result to database if user is logged in
                success, message = process_analysis_result()
                if success and 'logged_in' in st.session_state and st.session_state.logged_in:
                    # Clear the analysis result from session state so it doesn't show again after rerun
                    if session_key_analysis_result in st.session_state:
                        del st.session_state[session_key_analysis_result]
            
        elif num_images < 3 and num_images > 0:
            st.warning(f"Please upload {3 - num_images} more images for analysis.")
        elif num_images == 0:
            st.info("Please upload images to begin analysis.")
        else:  #num_images > 6
            st.warning("You can upload a maximum of 6 images for analysis.")

# Part 3: personal information
def personal_data_form():
    session_key_profile = get_session_key("profile")

    # Check if user is logged in and profile needs to be synced
    if ('logged_in' in st.session_state and st.session_state.logged_in and 
        'user_id' in st.session_state and st.session_state.user_id and
        'username' in st.session_state and st.session_state.username != "Demo User" and
        not st.session_state.get('profile_synced', False)):
        from history import sync_profile_with_session
        sync_profile_with_session(st.session_state.user_id)
        st.session_state.profile_synced = True

    if session_key_profile not in st.session_state:
        st.session_state[session_key_profile] = {
            
            'age': 0,
            'gender': "Male",
            'weight': 0.0,
            'height': 0.0,
            'activity_level': "Moderately Active",
            'goal': "Stay Active",
        }

    with st.form("personal_data"):
        st.write('Enter Personal Information')

        profile = st.session_state[session_key_profile]

        

        age = st.number_input(
            "Age", min_value=0, max_value=120, step=1, value=profile["age"])
        
        weight = st.number_input('Weight (kg)', min_value=0.0, max_value=500.0, step=0.1, value=float(profile['weight']))
        
        height = st.number_input('Height (cm)', min_value=0.0, max_value=300.0, step=0.1, value=float(profile['height']))

        genders = ["Male","Female","Other"]
        if profile.get("gender") in genders:
            gender = st.radio('Gender',genders, genders.index(profile.get("gender")))
        else:
            gender = st.radio('Gender',genders)
        
        activities = ("Sedentary","Lightly Active","Moderately Active","Very Active","Extra Active")
        if profile.get("activity_level") in activities:
            activity_level = st.selectbox('Activity Level',activities, 
       help="""
Sedentary: Little to no exercise.\n 
Lightly active: Light exercise or sports 1-3 days per week.\n
Moderately active: Moderate exercise or sports 3-5 days per week.\n
Very active: Hard exercise or sports 6-7 days a week.\n 
Extra active: Very hard exercise or physical job or 2x training.
""",                                   index=activities.index(profile.get("activity_level")))
        else:
            activity_level = st.selectbox('Activity Level',activities)


        goals = ("Muscle Gain", "Fat Loss", "Stay Active")
        if profile.get("goal") in goals:
            goal = st.selectbox('Goal',goals, index=goals.index(profile.get("goal")))
        else:
            goal = st.selectbox('Goal', goals)
        
        personal_data_submit = st.form_submit_button("Save")
        
        if personal_data_submit:
            if all([age, weight, height, gender, activity_level, goal]):
                with st.spinner():
                    st.session_state[session_key_profile]['weight'] = weight
                    st.session_state[session_key_profile]['height'] = height
                    st.session_state[session_key_profile]['gender'] = gender
                    st.session_state[session_key_profile]['age'] = age
                    st.session_state[session_key_profile]['activity_level'] = activity_level
                    st.session_state[session_key_profile]['goal'] = goal
                    
                    # Save to database if user is logged in
                    success, message = save_profile_data()
                    if success:
                        st.success("Information saved.")
                    else:
                        st.success("Information saved.")
                        if message != "User not logged in or in demo mode":
                            st.warning(f"Could not save to database: {message}")
            else:
                st.warning("Please fill in all of the data fields.")

def nutrition():
    session_key_profile = get_session_key("profile")

    # Check if user is logged in and profile needs to be synced
    if ('logged_in' in st.session_state and st.session_state.logged_in and 
        'user_id' in st.session_state and st.session_state.user_id and
        'username' in st.session_state and st.session_state.username != "Demo User" and
        not st.session_state.get('profile_synced', False)):
        from history import sync_profile_with_session
        sync_profile_with_session(st.session_state.user_id)
        st.session_state.profile_synced = True

    if session_key_profile not in st.session_state:
        st.warning("Please fill in the personal information form first and save.")
        return None

    profile = st.session_state[session_key_profile]

    if 'nutrition' not in profile:
        profile['nutrition'] = {'carbs': 0, 'protein': 0, 'fat': 0, 'calories': 0}
        st.session_state[session_key_profile] = profile

    input_keys = ["carbs_input", "protein_input", "fat_input", "calories_input"]
    nutrition_keys = ["carbs", "protein", "fat", "calories"]

    for input_key, nutrition_key in zip(input_keys, nutrition_keys):
        session_key = get_session_key(input_key)
        if session_key not in st.session_state:
            st.session_state[session_key] = profile['nutrition'][nutrition_key]


    nutrition = st.container(border=True)
    nutrition.write("Nutrition Requirements")
    
    if nutrition.button("Generate", key=get_session_key("gen_nutrition")):
        with st.spinner():
            # calculate BMR
            if profile['gender'] == 'Male':
                bmr = (13.7 * profile['weight']) + (5 * profile['height']) + (6.8 * profile['age']) + 66
            else: 
                bmr = (9.6 * profile['weight']) + (1.8 * profile['height']) - (4.7 * profile['age']) + 655
            
            # calculate TDEE
            if profile['activity_level'] == 'Sedentary':
                tdee = bmr * 1.2
            elif profile['activity_level'] == 'Lightly Active':
                tdee = bmr * 1.375
            elif profile['activity_level'] == 'Moderately Active':              
                tdee = bmr * 1.55
            elif profile['activity_level'] == 'Very Active':
                tdee = bmr * 1.725
            else:
                tdee = bmr * 1.9
            
            # calculate macros
            if profile['goal'] == 'Fat Loss':
                carbs = round(pick_random_number(0.25, 0.35) * tdee / 4)
                protein = round(pick_random_number(0.4,0.5) * tdee / 4)
                fat = round(pick_random_number(0.2, 0.3) * tdee / 9)
            elif profile['goal'] == 'Muscle Gain':
                carbs = round(pick_random_number(0.35, 0.45) * tdee / 4)
                protein = round(pick_random_number(0.3, 0.4) * tdee / 4)
                fat = round(pick_random_number(0.2, 0.3) * tdee / 9)
            else:
                carbs = round(pick_random_number(0.4, 0.6) * tdee / 4)
                protein = round(pick_random_number(0.2, 0.3) * tdee / 4)
                fat = round(pick_random_number(0.2, 0.3) * tdee / 9)    

            result = {
                "carbs": carbs,
                "protein": protein,
                "fat": fat,
                "calories": carbs * 4 + protein * 4 + fat * 9,}
            
            if result:
                profile['nutrition'] = result.copy()
                st.session_state[session_key_profile] = profile

                for input_key, value in zip(input_keys, result.values()):
                    st.session_state[get_session_key(input_key)] = value
                
                # Save to database if user is logged in
                success, message = save_profile_data()
                
                # Save to nutrition history if user is logged in
                if 'logged_in' in st.session_state and st.session_state.logged_in and 'user_id' in st.session_state and st.session_state.user_id:
                    history_success, history_message = save_nutrition_history(
                        st.session_state.user_id, 
                        profile['nutrition']
                    )
                    if history_success:
                        pass
                    else:
                        st.success("Nutrition requirements generated.")
                        if history_message != "Database connection error":
                            st.warning(f"Could not save to history: {history_message}")
                else:
                    if message != "User not logged in or in demo mode":
                        st.warning(f"Could not save to database: {message}")
            else:
                st.error("Failed to generate nutrition requirements")
        
    with nutrition.form(get_session_key("nutrition_form"), border=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            carbs = st.number_input(
                "Carbs",
                min_value=0,
                step=1,
                key=get_session_key("carbs_input")
            )
        with col2:
            protein = st.number_input(
                "Protein",
                min_value=0,
                step=1,
                key=get_session_key("protein_input")
            )
        with col3:
            fat = st.number_input(
                "Fat",
                min_value=0,
                step=1,
                key=get_session_key("fat_input")
            )
        with col4:
            calories = st.number_input(
                "Calories",
                min_value=0,
                step=1,
                key=get_session_key("calories_input")
            )

        if st.form_submit_button("Save"):
            profile['nutrition'].update({
                'carbs': st.session_state[get_session_key("carbs_input")],
                'protein': st.session_state[get_session_key("protein_input")],
                'fat': st.session_state[get_session_key("fat_input")],
                'calories': st.session_state[get_session_key("calories_input")]
            })
            st.session_state[session_key_profile] = profile
            
            # Save to database if user is logged in
            success, message = save_profile_data()
            
            # Save to nutrition history if user is logged in
            if 'logged_in' in st.session_state and st.session_state.logged_in and 'user_id' in st.session_state and st.session_state.user_id:
                history_success, history_message = save_nutrition_history(
                    st.session_state.user_id, 
                    profile['nutrition']
                )
                if history_success:
                    st.success("Saved.")
                else:
                    if history_message != "Database connection error":
                        st.warning(f"Could not save to history: {history_message}")
            else:
                st.success("Infomation saved.")
                if message != "User not logged in or in demo mode":
                    st.warning(f"Could not save to database: {message}")
            

@st.fragment            
def note():
    session_key_notes = get_session_key("notes")
    
    if session_key_notes not in st.session_state:
        st.session_state[session_key_notes] = ""

    notes = st.container(border=True)
    st.session_state[session_key_notes] = notes.text_area(
        label="**Notes:**",
        height=120,
        value=st.session_state[session_key_notes],
        help="Add special requirements."
    )

    if notes.button("Update Notes", key=get_session_key("update_notes_button")):
        if st.session_state[session_key_notes]:
            notes.markdown(f"**Your notes:** {st.session_state[session_key_notes]}")
        
# Main Streamlit app
if __name__ == "__main__":

# -- introduction --
    hide_streamlit_style = """
    <style>
        div[data-testid="stDecoration"] {
            visibility: hidden;
        }
    </style>
    """
    
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    st.markdown(
    """
    <div style="text-align: center; display: flex; justify-content: center; align-items: center;">
        <img src="data:image/png;base64,""" + base64.b64encode(open("Logo.png", "rb").read()).decode() + """" style="height: 50px; margin-right: 10px;">
        <h1>My Plate</h1>
    </div>
    """,
    unsafe_allow_html=True,
    )


    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Habit", 
        "Goal",
        "Recipe", 
        "Profile",
        "Feedback",
        "Rank",
    ])
    
    # If we need to switch to the Profile tab, use JavaScript to click on it
    if 'active_tab' in st.session_state and st.session_state['active_tab'] == 3:
        # Reset the active tab after it's been used
        st.session_state['active_tab'] = 0
        
        # Use JavaScript to click on the Profile tab
        js = """
        <script>
            // Wait for the DOM to be fully loaded
            document.addEventListener('DOMContentLoaded', function() {
                // Find all tab buttons
                var tabs = document.querySelectorAll('[data-baseweb="tab"]');
                // Click on the Profile tab (index 3)
                if (tabs.length >= 4) {
                    tabs[3].click();
                }
            });
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)

# -- part 1 --
    with tab1:
        st.markdown("""
    <br><br>
    <div style="text-align: center;">
        <h4>Diet Preference</h4>
    <br><br>
    """, unsafe_allow_html=True)

        image_upload()
        images_displayed()
        images_analysis()

# -- part 2 --
    with tab2:
        st.markdown("""
    <br><br>
    <div style="text-align: center;">
        <h4>Personal Details and Diet Goal</h4>
    </div>
    """, unsafe_allow_html=True)

        personal_data_form()

        st.text("")

        nutrition()
        
# -- part 3 --
    with tab3:
        st.markdown("""
    <br><br>
    <div style="text-align: center;">
        <h4>Today's Recipe</h4>
    </div>   
    """, unsafe_allow_html=True)
        choose_meal()
        cook_style()
        from functions import display_habit_collection
        display_habit_collection()
        cook_time()
        ingredients()
        note()
        recommandation2()

# -- part 4 --
    with tab4:
        # First display the welcome message and login/signup functionality
        st.text("")
        if 'logged_in' in st.session_state and st.session_state.logged_in:
            st.subheader(f"Welcome {st.session_state.username}!")
            
            # Display user information
            if st.session_state.username == "Demo User":
                st.write("You are currently in demo mode. Database functionality is limited.")
            
            st.button("Refresh Profile")
            # Display Habit Collection
            st.text("")
            st.subheader("Habit Collection")
            # Display saved analysis results
            if 'user_id' in st.session_state and st.session_state.user_id and st.session_state.username != "Demo User":
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
                            analysis_texts = [analysis for analysis, _ in analysis_results if len(analysis) < 60] 
                            # Display all analyses as pills
                            st.pills(label="Diet Analysis History", options=analysis_texts, key="analysis_pills", label_visibility="collapsed")
                            
                            # Add option to delete analysis results
                            st.text("")
                            
                            # Initialize session state for showing delete UI
                            if 'show_delete_habit_ui' not in st.session_state:
                                st.session_state.show_delete_habit_ui = False
                                
                            # Button to show/hide delete UI
                            if st.button("Manage Habits", key="manage_habits_button"):
                                st.session_state.show_delete_habit_ui = not st.session_state.show_delete_habit_ui
                                st.rerun()
                                
                            # Only show delete UI when button is clicked
                            if st.session_state.show_delete_habit_ui:
                                delete_container = st.container(border=True)
                                with delete_container:
                                    
                                    selected_analysis = st.selectbox(
                                            "Select a habit to delete:",
                                            options=analysis_texts,
                                            key="delete_analysis_selectbox"
                                        )
                                
                                    if st.button("Delete", key="delete_analysis_button"):
                                            from analysis_storage import delete_analysis_result
                                            success, message = delete_analysis_result(st.session_state.user_id, selected_analysis)
                                            if success:
                                                st.success("Habit deleted successfully!")
                                                st.session_state.show_delete_habit_ui = False
                                                st.rerun()  # Refresh the page to update the list
                                            else:
                                                st.error(f"Error deleting habit: {message}")
                                    
                                    # Button to cancel/hide delete UI
                                    if st.button("Cancel", key="cancel_delete_button"):
                                        st.session_state.show_delete_habit_ui = False
                                        st.rerun()
                        else:
                            st.info("No Habit found. Upload food images in the Habit tab to analyze your diet preferences.")
                            
                    except Exception as e:
                        st.error(f"Error retrieving analysis history: {e}")
            else:
                st.info("Login to view your diet analysis history.")
            
            # Display Saved Recipes
            st.text("")
            st.subheader("Saved Recipes")
            from saved_recipes import display_saved_recipes
            display_saved_recipes()
            
            # Display Nutrition History
            display_nutrition_history_chart()
            
            # Display Profile Information after Nutrition History
            st.text("")
            st.subheader("Profile Information")
            a = st.container(border=True)
            
            # Get user information from database
            if 'user_id' in st.session_state and st.session_state.user_id and st.session_state.username != "Demo User":
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
        else:
            # If not logged in, show the login/signup functionality
            hello()



# -- part 5 --
    with tab5:
        st.markdown("""
    <br><br>
    <div style="text-align: center;">
        <h4>Rate the Experience</h4>
    </div>
    """, unsafe_allow_html=True)
        
        feedback()
        feedback_score()
        recent_commend()

# -- part 6 --
    with tab6:
        popular_habits()
        new_habits()


