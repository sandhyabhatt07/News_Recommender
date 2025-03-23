import streamlit as st

def display_sidebar(news_df):
    """Displays the sidebar with category filters and user preferences."""
    st.sidebar.title("🔍 News Filter & Preferences")

    # Category selection
    categories = ["All"] + list(news_df["category"].unique())

    # Use session state to persist the selected category
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = "All"

    selected_category = st.sidebar.selectbox("Select News Category", categories, index=categories.index(st.session_state.selected_category))

    # Update selected category in session state
    st.session_state.selected_category = selected_category

    # User ID input with session state persistence
    if "user_id" not in st.session_state:
        st.session_state.user_id = 1  # Default to 1

    user_id = st.sidebar.number_input("Enter User ID", min_value=1, max_value=100, value=st.session_state.user_id)

    # Update user_id in session state
    st.session_state.user_id = user_id

    # Section for personalized recommendations
    st.sidebar.subheader("📌 Recommended for You")

    return selected_category, user_id

def display_article(article):
    """Displays a single news article in Streamlit."""
    col1, col2 = st.columns([1, 4])

    # Default image if missing
    image_url = article.get("image", "https://via.placeholder.com/150")

    with col1:
        st.image(image_url, width=150)
    with col2:
        title = article.get("title", "No Title")
        link = article.get("link", "#")  # Default to "#" if link is missing
        published_date = article.get("published", "Unknown Date")

        st.markdown(f"### [{title}]({link})")
        st.caption(f"📅 {published_date}")

def display_recommendations(recommendations):
    """Displays recommended articles in Streamlit."""
    if recommendations.empty:
        st.warning("No recommendations available.")
        return

    for _, rec in recommendations.iterrows():
        title = rec.get("title", "No Title")
        link = rec.get("link", "#")
        image_url = rec.get("image", "https://via.placeholder.com/100")  # Default image
        
        st.markdown(f"🔹 [{title}]({link})", unsafe_allow_html=True)
        st.image(image_url, width=100)
