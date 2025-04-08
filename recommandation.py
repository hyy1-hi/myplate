import streamlit as st
from functions import get_session_key
import os
from dotenv import load_dotenv
import google.generativeai as genai
from prompts import prompt2, prompt3


def recommandation1():
    session_key_recommandation1 = get_session_key("recommandation1")
    session_key_profile = get_session_key("profile")

    if session_key_recommandation1 not in st.session_state:
        st.session_state[session_key_recommandation1] = ""
    
    if st.button('Analyze Nutrition Requirements', key=get_session_key("recomd1_button")):
        with st.spinner("Analyzing..."):
            if session_key_profile not in st.session_state:
                st.error("Please fill in your personal information first.")
                return
                
            # Check if nutrition data exists in profile
            if 'nutrition' not in st.session_state[session_key_profile]:
                st.error("Please generate or enter your nutrition requirements first.")
                return
                
            # Validate nutrition data has all required keys
            nutrition = st.session_state[session_key_profile]['nutrition']
            required_keys = ['calories', 'carbs', 'protein', 'fat']
            missing_keys = [key for key in required_keys if key not in nutrition]
                
            if missing_keys:
                st.error(f"Missing nutrition data: {', '.join(missing_keys)}. Please generate nutrition requirements.")
                return
                
            # Check if all nutrition values are zero
            if all(nutrition[key] == 0 for key in required_keys):
                st.error("All nutrition values are zero. Please generate valid nutrition requirements.")
                return
                
        
            load_dotenv()
            api_key = os.environ.get("GEMINI_API_KEY_3")
            if not api_key:
                st.error("API key not found. Please check your .env file.")
                return
                    
            genai.configure(api_key=api_key)

            generation_config = {
                            "temperature": 0.8,
                            "top_p": 0.95,
                            "top_k": 40,
                            "max_output_tokens": 1024,
                            "response_mime_type": "text/plain",
                        }

            model = genai.GenerativeModel(
                            model_name="gemini-2.0-flash-lite",
                            generation_config=generation_config,
                        )
                    
                    # Format nutrition data in a more readable way
            nutrition_str = str(st.session_state[session_key_profile]['nutrition'])
            profile_str = str(st.session_state[session_key_profile])
                    

            chat_session = model.start_chat(history=[
                            {"role": "user", "parts": [{"text": profile_str}]},
                            {"role": "user", "parts": [{"text": nutrition_str}]}
                        ])

                        
            message = str(prompt3)
            response = chat_session.send_message(message)
            st.session_state[session_key_recommandation1] = response.text
            st.markdown(st.session_state[session_key_recommandation1])       
                        
                        

def recommandation2():
    session_key_recommandation2 = get_session_key("recommandation2")
    session_key_notes = get_session_key("notes")
    session_key_analysis_result = get_session_key("analysis_result")
    session_key_profile = get_session_key("profile")
    session_key_recipe_generated = get_session_key("recipe_generated")

    if session_key_recommandation2 not in st.session_state:
        st.session_state[session_key_recommandation2] = ""
    
    if session_key_analysis_result not in st.session_state:
        st.session_state[session_key_analysis_result] = ""
    
    if session_key_recipe_generated not in st.session_state:
        st.session_state[session_key_recipe_generated] = False
    
    # Generate recipe when button is clicked
    if st.button('Get Recipe', key=get_session_key("recomd_button")):
        with st.spinner("Generating..."):
            try:
                # Check if profile exists in session state
                if session_key_profile not in st.session_state:
                    st.error("Please fill in your personal information first.")
                    return
                
                # Check if nutrition data exists in profile
                if 'nutrition' not in st.session_state[session_key_profile]:
                    st.error("Please generate or enter your nutrition requirements first.")
                    return
                
                # Validate nutrition data has all required keys
                nutrition = st.session_state[session_key_profile]['nutrition']
                required_keys = ['calories', 'carbs', 'protein', 'fat']
                missing_keys = [key for key in required_keys if key not in nutrition]
                
                if missing_keys:
                    st.error(f"Missing nutrition data: {', '.join(missing_keys)}. Please generate nutrition requirements.")
                    return
                
                # Check if all nutrition values are zero
                if all(nutrition[key] == 0 for key in required_keys):
                    st.error("All nutrition values are zero. Please generate valid nutrition requirements.")
                    return
                
                try:
                    load_dotenv()
                    api_key = os.environ.get("GEMINI_API_KEY_2")
                    if not api_key:
                        st.error("API key not found. Please check your .env file.")
                        return
                    
                    genai.configure(api_key=api_key)

                    generation_config = {
                            "temperature": 0.8,
                            "top_p": 0.95,
                            "top_k": 40,
                            "max_output_tokens": 8192,
                            "response_mime_type": "text/plain",
                        }

                    model = genai.GenerativeModel(
                            model_name="gemini-2.0-flash-lite",
                            generation_config=generation_config,
                        )
                    
                    # Format nutrition data in a more readable way
                    nutrition_str = f"Daily Nutrition Requirements:\nCalories: {nutrition['calories']}\nCarbs: {nutrition['carbs']}g\nProtein: {nutrition['protein']}g\nFat: {nutrition['fat']}g"
                    
                    # Convert other data to strings
                    profile_str = str(st.session_state[session_key_profile])
                    
                    # Check if these session state variables exist before accessing them
                    time_str = str(st.session_state.get('cook_time', 5))  # Default to 5 minutes
                    meal_str = str(st.session_state.get('meal', 'Other'))  # Default to 'Other'
                    cook_style_str = str(st.session_state.get('cook_style', ''))  # Default to empty string
                    ingredients_str = str(st.session_state.get('ingredients', 3))  # Default to 3 ingredients
                    habit_str = str(st.session_state.get("recipe_style", ""))  # Default to empty string
                    
                    # Get notes and analysis result, with empty string defaults if not found
                    notes_text = st.session_state.get(session_key_notes, "")
                    
                    try:
                        chat_session = model.start_chat(history=[
                            {"role": "user", "parts": [{"text": notes_text}]},
                            {"role": "user", "parts": [{"text": profile_str}]},
                            {"role": "user", "parts": [{"text": nutrition_str}]},
                            {"role": "user", "parts": [{"text": habit_str}]},
                            {"role": "user", "parts": [{"text": cook_style_str}]},
                            {"role": "user", "parts": [{"text": time_str}]},
                            {"role": "user", "parts": [{"text": meal_str}]},
                            {"role": "user", "parts": [{"text": ingredients_str}]}
                        ])

                        # Create a simplified message to avoid the list index out of range error
                        try:
                            # Create a simplified recipe request that doesn't rely on complex formatting
                            simplified_message = str(prompt2)
                            
                            # Send the simplified message instead of prompt2
                            response = chat_session.send_message(simplified_message)
                        except Exception as e:
                            # If there's still an error, try an even simpler approach
                            try:
                                basic_message = "Please create a recipe based on the nutrition data I provided earlier."
                                response = chat_session.send_message(basic_message)
                            except Exception as e2:
                                error_message = f"Error sending message to Gemini API: {str(e2)}"
                                st.error(error_message)
                                raise
                        
                        # Check if response has text before trying to access it
                        if hasattr(response, 'text'):
                            st.session_state[session_key_recommandation2] = response.text
                            st.session_state[session_key_recipe_generated] = True
                        else:
                            error_message = "No response text received from the model. Please try again later."
                            st.error(error_message)
                            st.session_state[session_key_recommandation2] = error_message
                            st.session_state[session_key_recipe_generated] = False
                    except Exception as e:
                        error_message = f"Error in API call: {str(e)}"
                        st.error(error_message)
                        st.session_state[session_key_recommandation2] = error_message
                        st.session_state[session_key_recipe_generated] = False
                except Exception as e:
                    error_message = f"Error in API setup: {str(e)}"
                    st.error(error_message)
                    st.session_state[session_key_recommandation2] = error_message
                    st.session_state[session_key_recipe_generated] = False
            except Exception as e:
                import traceback
                error_message = f"Error generating recipe: {str(e)}\n{traceback.format_exc()}"
                st.error(error_message)
                st.session_state[session_key_recommandation2] = error_message
                st.session_state[session_key_recipe_generated] = False
    
    # Always display the recipe if it exists in session state
    if st.session_state[session_key_recipe_generated] and st.session_state[session_key_recommandation2]:
        # Display the recipe
        st.markdown(st.session_state[session_key_recommandation2])
    
    # Display save button if recipe has been generated
    if st.session_state[session_key_recipe_generated] and st.session_state[session_key_recommandation2]:
        if 'logged_in' in st.session_state and st.session_state.logged_in and 'user_id' in st.session_state and st.session_state.user_id:
            if st.button("Save Recipe", key=get_session_key("save_recipe_button")):
                from saved_recipes import save_recipe
                success, message = save_recipe(st.session_state.user_id, st.session_state[session_key_recommandation2])
                if success:
                    st.success(message)
                else:
                    st.error(message)
        else:
            st.info("Login to save this recipe.")
