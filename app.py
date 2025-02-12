import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import math
from dataclasses import dataclass
import random
import hashlib
import sqlite3
from typing import List, Dict
import json

# Enhanced data structures
@dataclass
class Shape:
    name: str
    formula: str
    parameters: list
    points: int  # Points awarded for correct solution
    
    def calculate_area(self, params):
        if self.name == "Square":
            return params["side"] ** 2
        elif self.name == "Rectangle":
            return params["length"] * params["width"]
        elif self.name == "Circle":
            return math.pi * (params["radius"] ** 2)
        elif self.name == "Triangle":
            return 0.5 * params["base"] * params["height"]

@dataclass
class Achievement:
    name: str
    description: str
    condition: str
    points: int
    icon: str

# Database setup
def init_database():
    conn = sqlite3.connect('geometry_app.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, 
                  password_hash TEXT,
                  total_points INTEGER DEFAULT 0,
                  level INTEGER DEFAULT 1,
                  achievements TEXT DEFAULT '[]',
                  streak INTEGER DEFAULT 0,
                  last_login DATE)''')
    
    # Create progress table
    c.execute('''CREATE TABLE IF NOT EXISTS progress
                 (username TEXT,
                  timestamp DATETIME,
                  shape TEXT,
                  correct BOOLEAN,
                  points INTEGER,
                  FOREIGN KEY (username) REFERENCES users(username))''')
    
    conn.commit()
    conn.close()

# Authentication functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username: str, password: str) -> bool:
    conn = sqlite3.connect('geometry_app.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                 (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username: str, password: str) -> bool:
    conn = sqlite3.connect('geometry_app.db')
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == hash_password(password)

# Gamification elements
ACHIEVEMENTS = {
    "first_solve": Achievement(
        "First Steps", 
        "Solve your first geometry problem",
        "problems_solved >= 1",
        10,
        "🎯"
    ),
    "perfect_streak": Achievement(
        "Perfect Streak",
        "Solve 5 problems in a row correctly",
        "streak >= 5",
        50,
        "🔥"
    ),
    "shape_master": Achievement(
        "Shape Master",
        "Solve problems for all available shapes",
        "shapes_solved >= 4",
        100,
        "👑"
    ),
}

LEVELS = {
    1: {"name": "Novice Geometer", "points_needed": 0},
    2: {"name": "Shape Apprentice", "points_needed": 100},
    3: {"name": "Geometry Scholar", "points_needed": 250},
    4: {"name": "Master of Areas", "points_needed": 500},
    5: {"name": "Geometry Sage", "points_needed": 1000},
}

# Enhanced shape definitions with points
SHAPES = {
    "Square": Shape("Square", "A = side²", ["side"], 10),
    "Rectangle": Shape("Rectangle", "A = length × width", ["length", "width"], 15),
    "Circle": Shape("Circle", "A = πr²", ["radius"], 20),
    "Triangle": Shape("Triangle", "A = ½ × base × height", ["base", "height"], 25)
}

# Home page
def show_home():
    st.title(f"Welcome, {st.session_state.user}!")
    st.write("""
    Welcome to your interactive geometry learning journey! This platform will help you:
    - Learn about different geometric shapes
    - Practice area calculations
    - Track your progress
    - Challenge yourself with quizzes
    """)
    
    
    st.subheader("Getting Started")
    st.write("""
    1. Visit the Learn section to understand shape concepts
    2. Practice with interactive problems
    3. Track your progress in the Progress section
    """)
    
    # Quick access buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Learning"):
            st.session_state.page = "learn"
    with col2:
        if st.button("Practice Problems"):
            st.session_state.page = "practice"

# Learning module
def show_learn():
    st.title("Learn Geometry")
    
    selected_shape = st.selectbox("Select a shape to learn about:", list(SHAPES.keys()))
    shape = SHAPES[selected_shape]
    
    st.subheader(f"Understanding {selected_shape}")
    st.write(f"Area Formula: {shape.formula}")
    
    
    st.subheader("Key Components:")
    if selected_shape == "Square":
        st.write("- Side: The length of any side of the square")
    elif selected_shape == "Rectangle":
        st.write("- Length: The longer side of the rectangle")
        st.write("- Width: The shorter side of the rectangle")
    elif selected_shape == "Circle":
        st.write("- Radius: The distance from the center to any point on the circle")
        st.write("- π (pi): Approximately 3.14159")
    elif selected_shape == "Triangle":
        st.write("- Base: The length of the triangle's base")
        st.write("- Height: The perpendicular height from the base to the opposite vertex")

# Practice module
def show_practice():
    st.title("Practice Area Calculations")
    
    if "problem" not in st.session_state:
        generate_problem()
    
    shape = SHAPES[st.session_state.current_shape]
    st.subheader(f"Calculate the area of this {shape.name}")
    
    # Display shape parameters
    params = {}
    for param in shape.parameters:
        value = st.session_state.problem[param]
        st.write(f"{param.capitalize()}: {value} units")
        params[param] = value
    
    # User input
    user_answer = st.number_input("Enter your answer:", min_value=0.0, step=0.1)
    
    if st.button("Check Answer"):
        correct_answer = shape.calculate_area(params)
        if abs(user_answer - correct_answer) < 0.1:  # Allow for small rounding differences
            st.success("Correct! Well done!")
            
            # Update user progress with points
            update_user_progress(st.session_state.user, shape.name, True, shape.points)
            
            st.balloons()
        else:
            st.error(f"Not quite. The correct answer is {correct_answer:.2f}")
            
            # Update user progress without points
            update_user_progress(st.session_state.user, shape.name, False, 0)
            
            show_solution(shape, params, correct_answer)
    
    if st.button("New Problem"):
        generate_problem()

def generate_problem():
    shape_name = random.choice(list(SHAPES.keys()))
    st.session_state.current_shape = shape_name
    shape = SHAPES[shape_name]
    
    st.session_state.problem = {}
    for param in shape.parameters:
        st.session_state.problem[param] = random.randint(1, 10)

def show_solution(shape, params, correct_answer):
    st.subheader("Solution")
    if shape.name == "Square":
        st.write(f"Area = side² = {params['side']}² = {correct_answer:.2f}")
    elif shape.name == "Rectangle":
        st.write(f"Area = length × width = {params['length']} × {params['width']} = {correct_answer:.2f}")
    elif shape.name == "Circle":
        st.write(f"Area = πr² = π × {params['radius']}² = {correct_answer:.2f}")
    elif shape.name == "Triangle":
        st.write(f"Area = ½ × base × height = ½ × {params['base']} × {params['height']} = {correct_answer:.2f}")


# User progress and achievements
def update_user_progress(username: str, shape: str, correct: bool, points: int):
    conn = sqlite3.connect('geometry_app.db')
    c = conn.cursor()
    
    # Update progress
    c.execute("""INSERT INTO progress (username, timestamp, shape, correct, points)
                 VALUES (?, ?, ?, ?, ?)""",
              (username, datetime.now(), shape, correct, points))
    
    # Update user points and check achievements
    if correct:
        c.execute("UPDATE users SET total_points = total_points + ? WHERE username = ?",
                 (points, username))
        
        # Update streak
        c.execute("UPDATE users SET streak = streak + 1 WHERE username = ?", (username,))
    else:
        c.execute("UPDATE users SET streak = 0 WHERE username = ?", (username,))
    
    conn.commit()
    
    # Check for new achievements
    check_achievements(username)
    
    conn.close()

def check_achievements(username: str):
    conn = sqlite3.connect('geometry_app.db')
    c = conn.cursor()
    
    # Get user data
    c.execute("""SELECT total_points, streak, achievements FROM users 
                 WHERE username = ?""", (username,))
    total_points, streak, achievements_json = c.fetchone()
    current_achievements = set(json.loads(achievements_json))
    
    # Get solved shapes
    c.execute("""SELECT DISTINCT shape FROM progress 
                 WHERE username = ? AND correct = 1""", (username,))
    shapes_solved = len(c.fetchall())
    
    # Check each achievement
    for ach_id, achievement in ACHIEVEMENTS.items():
        if ach_id not in current_achievements:
            condition_met = eval(achievement.condition, {
                "problems_solved": get_problems_solved(username),
                "streak": streak,
                "shapes_solved": shapes_solved
            })
            
            if condition_met:
                current_achievements.add(ach_id)
                c.execute("""UPDATE users 
                           SET achievements = ?,
                               total_points = total_points + ?
                           WHERE username = ?""",
                         (json.dumps(list(current_achievements)),
                          achievement.points,
                          username))
                
                st.balloons()
                st.success(f"Achievement Unlocked: {achievement.name}! +{achievement.points} points")
    
    conn.commit()
    conn.close()

def get_problems_solved(username: str) -> int:
    conn = sqlite3.connect('geometry_app.db')
    c = conn.cursor()
    c.execute("""SELECT COUNT(*) FROM progress 
                 WHERE username = ? AND correct = 1""", (username,))
    result = c.fetchone()[0]
    conn.close()
    return result

# Authentication UI
def show_auth_page():
    st.title("Welcome to Geometry Learning")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if verify_user(username, password):
                    st.session_state.user = username
                    st.success("Login successful!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords don't match")
                elif register_user(new_username, new_password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Username already exists")

def show_progress():
    st.title("Your Learning Progress")
    
    conn = sqlite3.connect('geometry_app.db')
    
    # Modify the SQL query to explicitly cast correct to boolean
    progress_df = pd.read_sql_query(
        "SELECT *, CASE WHEN correct = 1 THEN 1 ELSE 0 END AS is_correct FROM progress WHERE username = ?",
        conn,
        params=(st.session_state.user,)
    )
    
    user_data = pd.read_sql_query(
        "SELECT * FROM users WHERE username = ?",
        conn,
        params=(st.session_state.user,)
    ).iloc[0]
    
    # Display level and points
    col1, col2, col3 = st.columns(3)
    current_level = max(level for level, info in LEVELS.items() 
                       if info["points_needed"] <= user_data["total_points"])
    
    col1.metric("Current Level", f"{current_level} - {LEVELS[current_level]['name']}")
    col2.metric("Total Points", user_data["total_points"])
    col3.metric("Current Streak", f"{user_data['streak']} 🔥")
    
    # Progress to next level
    if current_level < max(LEVELS.keys()):
        next_level = current_level + 1
        points_needed = LEVELS[next_level]["points_needed"] - user_data["total_points"]
        st.progress(user_data["total_points"] / LEVELS[next_level]["points_needed"])
        st.write(f"{points_needed} points needed for next level")
    
    # Achievements
    st.subheader("Your Achievements")
    achievements = json.loads(user_data["achievements"])
    cols = st.columns(3)
    for i, (ach_id, achievement) in enumerate(ACHIEVEMENTS.items()):
        with cols[i % 3]:
            if ach_id in achievements:
                st.success(f"{achievement.icon} {achievement.name}")
            else:
                st.info(f"🔒 {achievement.name}")
            st.caption(achievement.description)
    
    # Performance statistics
    if not progress_df.empty:
        st.subheader("Performance Statistics")
        
        # Overall statistics
        total_problems = len(progress_df)
        correct_problems = progress_df['is_correct'].sum()
        accuracy = (correct_problems / total_problems) * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Problems", total_problems)
        col2.metric("Correct Answers", correct_problems)
        col3.metric("Accuracy", f"{accuracy:.1f}%")
        
        # Performance by shape
        st.subheader("Performance by Shape")
        shape_stats = progress_df.groupby("shape")['is_correct'].agg(["count", "mean"])
        shape_stats["accuracy"] = shape_stats["mean"] * 100
        st.dataframe(shape_stats.rename(columns={"count": "Problems", "accuracy": "Accuracy %"}))
    
    conn.close()
# Leaderboard
def show_leaderboard():
    st.subheader("Leaderboard")
    
    conn = sqlite3.connect('geometry_app.db')
    leaders_df = pd.read_sql_query("""
        SELECT username, total_points, level, streak,
               (SELECT COUNT(*) FROM progress WHERE username = users.username AND correct = 1) as problems_solved
        FROM users
        ORDER BY total_points DESC
        LIMIT 10
    """, conn)
    
    for i, row in leaders_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            col1.write(f"#{i+1}")
            col2.write(row["username"])
            col3.write(f"{row['total_points']} pts")
    
    conn.close()




# Main app with authentication
def main():
    st.set_page_config(page_title="Geometry Learning", layout="wide")
    init_database()
    
    # Check authentication
    if "user" not in st.session_state:
        show_auth_page()
        return
    
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    # Navigation with user info
    st.sidebar.title(f"Welcome, {st.session_state.user}!")
    pages = {
        "Home": "home",
        "Learn": "learn",
        "Practice": "practice",
        "Progress": "progress",
        "Leaderboard": "leaderboard"
    }
    selection = st.sidebar.radio("Navigation", list(pages.keys()))
    st.session_state.page = pages[selection]
    
    # Logout button
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.experimental_rerun()
    
    # Show selected page
    if st.session_state.page == "home":
        show_home()
    elif st.session_state.page == "learn":
        show_learn()
    elif st.session_state.page == "practice":
        show_practice()
    elif st.session_state.page == "progress":
        show_progress()
    elif st.session_state.page == "leaderboard":
        show_leaderboard()

if __name__ == "__main__":
    main()