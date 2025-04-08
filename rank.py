import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from history import get_db_connection


def popular_habits():
    st.markdown("""
    <br><br>
    <div style="text-align: center;">
        <h4>Top 5 Popular Habits</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Connect to the database
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Query to get the top 5 most popular habits
            cur.execute("""
                SELECT analysis_text, COUNT(*) as count
                FROM analysis_results
                GROUP BY analysis_text
                ORDER BY count DESC
                LIMIT 5
            """)
            
            results = cur.fetchall()
            cur.close()
            conn.close()
            
            if results:
                # Create a DataFrame for better display
                df = pd.DataFrame(results, columns=["Habit", "Count"])
                
                # Create a horizontal bar chart with custom styling
                fig, ax = plt.subplots(figsize=(10, 4))
                 
                # Use a color palette similar to the one in the image
                colors = ['#f9ddd1', '#f5e9db', '#f8faf3', '#d9ead3', '#cff0f3']
                
                # Create horizontal bars - reverse the order so most popular is at the top
                habits = df["Habit"].tolist()[::-1]
                values = df["Count"].tolist()[::-1]
                
                # Ensure we have enough colors (in case there are fewer than 5 habits)
                colors = colors[:len(habits)]
                
                # Create horizontal bars with a small offset for the y-position to ensure all bars are visible
                y_pos = np.arange(len(habits))
                bars = ax.barh(y_pos, values, color=colors, height=0.5)
                
                # Set the y-tick positions and labels
                ax.set_yticks(y_pos)
                ax.set_yticklabels(habits)
                
                # Add count values at the end of each bar
                for i, v in enumerate(values):
                    # Add the count value
                    ax.text(v + 0.1, i, str(v), va='center', fontsize=12)
                    
                    
                
                # Customize the chart
                ax.set_xlim(0, 2)  # Add some space for the value labels
        
                
                # Remove the top, right, and bottom spines
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_visible(False)
                

                # Hide x-axis ticks while keeping the grid
                ax.tick_params(axis='x', which='both', bottom=False)
                
                # Hide x-axis
                ax.get_xaxis().set_visible(False)

                # Increase y-axis label (Habit names) font size
                ax.tick_params(axis='y', labelsize=14)
                
                # Adjust layout
                plt.tight_layout()
                
                # Display the chart in Streamlit
                st.pyplot(fig)
                
                
            else:
                st.info("No habits found in the database yet. Users need to analyze their diet preferences first.")
                
        except Exception as e:
            st.error(f"Error retrieving popular habits: {e}")
    else:
        st.warning("Could not connect to the database. Please make sure the database is properly configured.")

def new_habits():
    st.markdown("""
    <br><br>
    <div style="text-align: center;">
        <h4>New Trends</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Connect to the database
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Query to get the 5 latest habits that did not show in database before
            cur.execute("""
                WITH first_appearances AS (
                    SELECT analysis_text, MIN(created_at) as first_appearance
                    FROM analysis_results
                    GROUP BY analysis_text
                )
                SELECT analysis_text, first_appearance
                FROM first_appearances
                ORDER BY first_appearance DESC
                LIMIT 5
            """)
            
            results = cur.fetchall()
            cur.close()
            conn.close()
            
            if results:
                # Create a DataFrame for better display
                df = pd.DataFrame(results, columns=["Habit", "Added On"])
                
                # Format the datetime for better readability
                df["Added On"] = pd.to_datetime(df["Added On"]).dt.strftime("%Y-%m-%d %H:%M")
                
                # Create a badge/shield visualization like in the image
                fig, ax = plt.subplots(figsize=(14, 8))  # Increased height for two rows
                
                # Use 5 different colors for the circle backgrounds with dark blue border
                bg_colors = ['#8ab5b0', '#e6b89c', '#ead6b9', '#9fd8cb', '#cbaacb']  # Teal, peach, beige, mint, lavender
                border_colors = ['#1e3a5c', '#1e3a5c', '#1e3a5c', '#1e3a5c', '#1e3a5c']  # Dark blue border
                
                # Ensure we have enough colors
                bg_colors = bg_colors[:len(df)]
                border_colors = border_colors[:len(df)]
                
                # Position circles in two rows: 3 in first row, 2 in second row
                circle_radius = 0.12
                
                # Calculate positions for two rows
                row1_x = np.linspace(0.2, 0.8, 3)  # 3 badges in first row
                row2_x = np.linspace(0.35, 0.65, 2)  # 2 badges in second row
                
                row1_y = 0.65  # First row y-position
                row2_y = 0.35  # Second row y-position
                
                # Create circles with habits
                for i, (habit, date, bg_color, border_color) in enumerate(zip(df["Habit"], df["Added On"], bg_colors, border_colors)):
                    # Determine position based on index
                    if i < 3:  # First row (first 3 badges)
                        x = row1_x[i]
                        y = row1_y
                    else:  # Second row (last 2 badges)
                        x = row2_x[i-3]
                        y = row2_y
                    
                    # Create a white background circle
                    white_circle = plt.Circle((x, y), circle_radius + 0.01, facecolor='white', 
                                             edgecolor=border_color, linewidth=2, zorder=1)
                    ax.add_patch(white_circle)
                    
                    # Create the main teal/green circle
                    main_circle = plt.Circle((x, y), circle_radius, facecolor=bg_color, 
                                            edgecolor='none', zorder=2)
                    ax.add_patch(main_circle)
                    
                    # Add habit name in white (handle long names by splitting into two rows)
                    if len(habit) < 20:
                        # Short habit name - display on a single line
                        ax.text(x, y + 0.03, habit, 
                               ha='center', va='center', color='#fffcfc', 
                               fontsize=16, fontweight='bold', zorder=3)
                        
                        # Add date in a lighter color below the habit name
                        date_short = date.split()[0]  # Just show the date part, not time
                        ax.text(x, y - 0.03, date_short, 
                               ha='center', va='center', color='#fffcfc', 
                               fontsize=14, zorder=3)
                    else:
                        # Long habit name - split into two rows
                        # Find a good split point (space) near the middle
                        mid_point = len(habit) // 2
                        split_point = habit.rfind(' ', 0, mid_point)
                        if split_point == -1:  # No space found in first half
                            split_point = habit.find(' ', mid_point)
                        
                        if split_point == -1:  # No spaces at all, force split
                            first_line = habit[:mid_point]
                            second_line = habit[mid_point:]
                        else:
                            first_line = habit[:split_point]
                            second_line = habit[split_point+1:]  # Skip the space
                        
                        # Display first line of habit name
                        ax.text(x, y + 0.05, first_line, 
                               ha='center', va='center', color='#fffcfc', 
                               fontsize=15, fontweight='bold', zorder=3)
                        
                        # Display second line of habit name
                        ax.text(x, y, second_line, 
                               ha='center', va='center', color='#fffcfc', 
                               fontsize=15, fontweight='bold', zorder=3)
                        
                        # Add date in a lighter color below the habit name (adjusted position)
                        date_short = date.split()[0]  # Just show the date part, not time
                        ax.text(x, y - 0.05, date_short, 
                               ha='center', va='center', color='#fffcfc', 
                               fontsize=14, zorder=3)
                
                # Set axis limits and remove spines and ticks
                ax.set_xlim(0, 1)
                ax.set_ylim(0.1, 0.9)
                
                # Remove all spines
                for spine in ax.spines.values():
                    spine.set_visible(False)
                
                # Hide both axes
                ax.get_xaxis().set_visible(False)
                ax.get_yaxis().set_visible(False)
                
                
                # Adjust layout
                plt.tight_layout()
                
                # Display the chart in Streamlit
                st.pyplot(fig)
                
            else:
                st.info("No habits found in the database yet. Users need to analyze their diet preferences first.")
                
        except Exception as e:
            st.error(f"Error retrieving recent habits: {e}")
    else:
        st.warning("Could not connect to the database. Please make sure the database is properly configured.")
