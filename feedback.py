import streamlit as st
from functions import get_session_key
from history import save_feedback, get_average_rating, get_recent_comments, init_db, get_db_connection


def feedback():
    # Initialize database tables if they don't exist
    init_db()
    
    session_key_q1 = get_session_key("q1")
    session_key_feedback_text = get_session_key("feedback_text")

    
    if session_key_q1 not in st.session_state:
        st.session_state[session_key_q1] = 5.0

    if session_key_feedback_text not in st.session_state:
        st.session_state[session_key_feedback_text] = ""


    feedback = st.container()
    q1 = feedback.slider(
        "How do you like the app?",
        0.0, 10.0,
        step=0.1,
        key=get_session_key("q1")
    )
    feedback_text = feedback.text_area(
        "Leave a comment:",
        height=100,
        key=get_session_key("feedback_text")
    )

    if feedback.button("Submit"):
        # Store rating and feedback separately
        st.session_state.q1 = q1  
        st.session_state.feedback_text = feedback_text
        
        # Save to database
        success, message = save_feedback(q1, feedback_text)
        if not success:
            feedback.warning(f"Could not save feedback to database: {message}")

        # Display confirmation
        feedback.success("Thank you for your feedback!")


def feedback_score():
    # Get average rating from database
    avg_rating = get_average_rating()
    
    # Get total number of ratings
    conn = get_db_connection()
    total_ratings = 0
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM feedback")
            total_ratings = cur.fetchone()[0]
            cur.close()
            conn.close()
        except Exception as e:
            st.error(f"Error retrieving rating count: {e}")
            if conn:
                conn.close()
    
    st.markdown("""
    <div style="text-align: center;">
        <h4>App score</h4>
    </div>
    """, unsafe_allow_html=True)
    
    if avg_rating is not None and total_ratings > 0:
        # Convert 0-10 scale to 0-5 scale for stars
        stars_rating = avg_rating / 2
        
        # Generate stars based on rating (filled and half-filled stars)
        full_stars = int(stars_rating)
        half_star = stars_rating - full_stars >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        
        # Create star display
        stars_html = full_stars * "★" + ("★" if half_star else "") + empty_stars * "☆"
        
        # Display rating with stars and total count
        st.markdown(
            f"""
            <h2 style='text-align: center;'>
                {avg_rating:.1f} <span style='color: gold; font-size: 1.2em;'>{stars_html}</span> ({total_ratings})
            </h2>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.info("No ratings yet. Be the first to rate the app!")


def recent_commend():
    # Get recent comments from database
    comments = get_recent_comments(limit=5)
    
    st.markdown("""
    <div style="text-align: center;">
        <h4>Recent comments</h4>
    </div>
    """, unsafe_allow_html=True)
    
    if comments:
        # Create a container for the comments
        comment_container = st.empty()
        
        # Convert comments to a format suitable for JavaScript
        js_comments = []
        for comment, rating, created_at in comments:
            js_comments.append({
                'comment': comment,
                'rating': f"{rating:.1f}",
                'created_at': created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        # Create JavaScript to cycle through comments
        js_code = f"""
        <script>
            // Comments data
            const comments = {js_comments};
            let currentIndex = 0;
            
            // Function to update the displayed comment
            function updateComment() {{
                const commentData = comments[currentIndex];
                const commentElement = document.getElementById('comment-container');
                
                if (commentElement) {{
                    commentElement.innerHTML = `
                        <div style="border: 1px solid #e6e6e6; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem;">
                            <p><strong>Rating: ${{commentData.rating}}/10</strong> - <em>${{commentData.created_at}}</em></p>
                            <p>${{commentData.comment}}</p>
                        </div>
                    `;
                    
                    // Move to the next comment
                    currentIndex = (currentIndex + 1) % comments.length;
                }}
            }}
            
            // Initial display
            document.addEventListener('DOMContentLoaded', function() {{
                // Create a div for the comment if it doesn't exist
                if (!document.getElementById('comment-container')) {{
                    const container = document.createElement('div');
                    container.id = 'comment-container';
                    document.querySelector('h4').parentNode.after(container);
                }}
                
                // Show the first comment
                updateComment();
                
                // Set interval to change comments every 4 seconds
                setInterval(updateComment, 4000);
            }});
        </script>
        <div id="comment-container"></div>
        """
        
        # Display the JavaScript
        st.components.v1.html(js_code, height=150)
    else:
        st.info("No comments yet. Be the first to leave a comment!")

