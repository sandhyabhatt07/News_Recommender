import streamlit as st
from fetch_news import get_news_dataframe
from recommend import (
    build_recommendation_models,
    content_based_recommendations,
    collaborative_recommendations,
)
from user_feedback import store_feedback
from ui_components import display_article
import pandas as pd

# Set page config
st.set_page_config(page_title="Google News Recommender", layout="wide")

# Fetch news data
news_df = get_news_dataframe()

# Check if the news dataframe is empty
if news_df.empty:
    st.error("No news articles available. Please check the data source.")
    st.stop()

# Sidebar for user input
st.sidebar.title("🔍 News Filter")

# Category selection
categories = ["All"] + list(news_df["category"].unique())

if "selected_category" not in st.session_state:
    st.session_state.selected_category = "All"

# 🔹 Reset session state when category changes
selected_category = st.sidebar.selectbox("Select News Category", categories)

if selected_category != st.session_state.selected_category:
    st.session_state.selected_category = selected_category
    st.session_state.recommendations = {}  # Reset recommendations for all articles
    st.rerun()

# User ID input
user_id = st.sidebar.number_input("Enter User ID", min_value=1, max_value=100, value=1)

# Build recommendation models
cosine_sim, vectorizer, svd, user_article_ratings = build_recommendation_models(news_df)

st.title("📰 Google News Personalized Recommendations")

# Filter news based on selected category
filtered_news_df = (
    news_df if selected_category == "All" else news_df[news_df["category"] == selected_category]
)

# 🔹 Ensure session state variable for recommendations exists
if "recommendations" not in st.session_state:
    st.session_state.recommendations = {}

# 🔹 Store Collaborative Recommendations in Session State (so they persist)
if "collab_recs" not in st.session_state:
    st.session_state.collab_recs = collaborative_recommendations(news_df, user_id, svd, user_article_ratings)

# 🔥 Sidebar: Display Collaborative Filtering Recommendations
with st.sidebar:
    st.subheader("📌 Recommended For You")

    if st.session_state.collab_recs.empty:
        st.warning("No personalized recommendations available.")
    else:
        for _, row in st.session_state.collab_recs.head(5).iterrows():
            st.markdown(f"🔹 [{row['title']}]({row['link']})")

# Display articles from the selected category
for index, article in filtered_news_df.iterrows():
    with st.container():
        display_article(article)

        # Button for recommendations
        if st.button("Show Similar Articles", key=f"btn_{index}"):
            # 🔹 Generate recommendations only for this article
            st.session_state.recommendations = {article["title"]: content_based_recommendations(news_df, article["title"], cosine_sim)}
            st.rerun()  # Refresh UI to show recommendations under the article

        # 🔥 Show recommendations **under this specific article only**
        if article["title"] in st.session_state.recommendations:
            recommendations = st.session_state.recommendations[article["title"]]

            if recommendations.empty:
                st.warning(f"No content-based recommendations for {article['title']}.")
            else:
                with st.expander(f"🔍 Similar Articles to: {article['title']}", expanded=True):
                    for _, row in recommendations.iterrows():
                        st.markdown(f"🔹 [{row['title']}]({row['link']})")

                    # Collect feedback
                    feedback = st.radio(
                        "Do you like these recommendations?",
                        ["Liked", "Disliked", "Viewed"],
                        key=f"feedback_{index}",
                    )

                    if feedback:
                        article_id = article.name  # Use the index as the unique identifier
                        store_feedback(user_id, article_id, feedback)
