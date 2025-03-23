import pandas as pd
import os

# File path for persistent storage
FEEDBACK_FILE = "user_feedback.csv"

def load_feedback():
    """Loads feedback data from the CSV file into a DataFrame."""
    if os.path.exists(FEEDBACK_FILE):
        return pd.read_csv(FEEDBACK_FILE)
    else:
        return pd.DataFrame(columns=["user_id", "article_id", "feedback"])

# Load existing feedback data when the module is imported
user_feedback = load_feedback()

def store_feedback(user_id, article_id, feedback):
    """Stores user feedback (Like/Dislike) in a CSV file."""
    global user_feedback
    
    # Append new feedback
    new_entry = pd.DataFrame({"user_id": [user_id], "article_id": [article_id], "feedback": [feedback]})
    user_feedback = pd.concat([user_feedback, new_entry], ignore_index=True)

    # Save feedback persistently
    user_feedback.to_csv(FEEDBACK_FILE, index=False)

def get_feedback_data():
    """Returns user feedback history."""
    return user_feedback
