import streamlit as st
from fetch_news import get_news_dataframe
from recommend import build_recommendation_models, content_based_recommendations, collaborative_recommendations
from user_feedback import store_feedback
from ui_components import display_article, display_recommendations
import pandas as pd

# Set page config
st.set_page_config(page_title="Google News Recommender", layout="wide")

# Fetch news data
news_df = get_news_dataframe()

all_recommendations = []

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

selected_category = st.sidebar.selectbox("Select News Category", categories, 
                                         index=categories.index(st.session_state.selected_category))

# Update selected category and refresh UI if category changes
if selected_category != st.session_state.selected_category:
    st.session_state.selected_category = selected_category
    st.rerun()  # Refresh UI when category changes

# User ID input (make sure user_id is within the range of valid user IDs in your dataset)
user_id = st.sidebar.number_input("Enter User ID", min_value=1, max_value=100, value=1)

# Build recommendation models
cosine_sim, vectorizer, svd, user_article_ratings = build_recommendation_models(news_df)

st.title("📰 Google News Personalized Recommendations")

# Filter news based on selected category
filtered_news_df = news_df if selected_category == "All" else news_df[news_df["category"] == selected_category]

# Initialize session state for clicked article and feedback collection
if "clicked_articles" not in st.session_state:
    st.session_state.clicked_articles = []

if "feedback_collected" not in st.session_state:
    st.session_state.feedback_collected = False

# Display articles from the selected category
for index, article in filtered_news_df.iterrows():
    with st.container():
        display_article(article)

        # Button for recommendations
        if st.button("Show Similar Articles", key=f"btn_{index}"):

            # Add article to clicked list if not already clicked
            if article["title"] not in st.session_state.clicked_articles:
                st.session_state.clicked_articles.append(article["title"])

# Fallback: Display content-based recommendations if no articles are clicked
if not st.session_state.clicked_articles:
    st.subheader("📌 Suggested Articles for You (Content-Based)")

    # Fetch content-based recommendations
    fallback_recs = content_based_recommendations(news_df, "Top Stories", cosine_sim)

    # Debugging: Check if recommendations are empty or non-relevant
    if fallback_recs.empty:
        st.info("No content-based recommendations available.")
    else:
        # Display recommendations if available
        for _, row in fallback_recs.head(5).iterrows():
            st.markdown(f"🔹 [{row['title']}]({row['link']})")

# Check if any article was clicked and recommendations are available
if st.session_state.clicked_articles:
    st.subheader(f"🔍 Similar Articles to: {', '.join(st.session_state.clicked_articles)}")

    all_recommendations = []  # Initialize all_recommendations to avoid NameError

    for clicked_article in st.session_state.clicked_articles:
        recommendations = content_based_recommendations(news_df, clicked_article, cosine_sim)

        # Check if recommendations are empty
        if recommendations.empty:
            st.warning(f"No content-based recommendations for {clicked_article}.")
        else:
            all_recommendations.append(recommendations)

    # Display recommendations if available
    if all_recommendations:
        combined_recommendations = pd.concat(all_recommendations).drop_duplicates()
        display_recommendations(combined_recommendations)

        # Collect feedback once recommendations are shown
        if not st.session_state.feedback_collected:
            feedback = st.radio("Do you like these recommendations?", ["Liked", "Disliked", "Viewed"], key="feedback_radio")
            
            if feedback:
                # Store feedback
                for clicked_article in st.session_state.clicked_articles:
                    article = news_df[news_df['title'] == clicked_article].iloc[0]
                    article_id = article.name  # Use the index as the unique identifier
                    store_feedback(user_id, article_id, feedback)

                st.session_state.feedback_collected = True

else:
    st.warning("Please click on an article to see recommendations.")

# Collaborative filtering recommendations (for personalized recommendations)
collab_recs = collaborative_recommendations(news_df, user_id, svd, user_article_ratings)

# Debugging: Check if collaborative recommendations are empty
if collab_recs.empty:
    st.warning("No collaborative recommendations available.")
else:
    # Move Personalized Recommendations to Sidebar
    with st.sidebar:
        st.subheader("📌 Recommended For You")
        
        # Display personalized recommendations in the sidebar
        for _, row in collab_recs.head(5).iterrows():
            st.markdown(f"🔹 [{row['title']}]({row['link']})")

# Fallback: Display content-based recommendations if neither content-based nor collaborative recommendations are available
if not all_recommendations and collab_recs.empty:
    st.subheader("📌 Suggested Articles for You (Fallback)")
    fallback_recs = content_based_recommendations(news_df, "Top Stories", cosine_sim).head(5)

    if not fallback_recs.empty:
        for _, row in fallback_recs.iterrows():
            st.markdown(f"🔹 [{row['title']}]({row['link']})")
    else:
        st.info("No alternative recommendations available.")

# Feed entries for selected category (Displaying news articles from selected category)
st.subheader("📰 Latest News from Selected Category")

for _, article in filtered_news_df.iterrows():
    st.write(f"### [{article['title']}]({article['link']})")
    st.write(f"🕒 {article['published']}")
    st.write("---")
