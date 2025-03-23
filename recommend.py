import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
import nltk
from nltk.corpus import stopwords
from fuzzywuzzy import fuzz
from fetch_news import get_news_dataframe  # Import the fetch_news function

nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

# Function to clean text summaries
def clean_text(text):
    """Cleans text by removing stopwords while keeping at least 2 words."""
    if pd.isna(text) or text.strip() in ["", "full article unavailable."]:
        return "no_content"
    
    words = text.lower().split()
    words = [word for word in words if word not in stop_words]

    if len(words) < 2:
        words = text.lower().split()[:2]  

    return " ".join(words).strip()

# Function to build the recommendation models (content-based and collaborative)
def build_recommendation_models(news_df):
    """Builds and trains content-based and collaborative filtering models."""
    # Content-based filtering (TF-IDF)
    news_df['cleaned_summary'] = news_df['summary'].apply(clean_text)
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(news_df["cleaned_summary"])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # Collaborative filtering setup
    user_article_ratings = pd.DataFrame({
        "user_id": np.random.randint(1, 100, size=200),  # Ensure we have enough ratings
        "article_id": np.random.randint(0, len(news_df), size=200),
        "rating": np.random.randint(1, 6, size=200)
    })

    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(user_article_ratings[['user_id', 'article_id', 'rating']], reader)
    trainset, testset = train_test_split(data, test_size=0.2)
    svd = SVD()
    svd.fit(trainset)

    return cosine_sim, vectorizer, svd, user_article_ratings

# Function for content-based recommendations
def content_based_recommendations(news_df, title, cosine_sim):
    """Generates content-based recommendations using cosine similarity."""
    # Ensure titles are formatted correctly
    title = title.strip().lower()

    # Fuzzy matching: find the closest match for the title in the dataset
    best_match = None
    highest_ratio = 0
    for article_title in news_df["title"]:
        ratio = fuzz.ratio(title, article_title.strip().lower())
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = article_title
    
    if best_match is None or highest_ratio < 80:  # Adjust threshold as needed
        print(f"No recommendations: Title '{title}' not found in the dataset.")
        return pd.DataFrame()  # Return empty dataframe if no match is found

    print(f"Best match found: {best_match} (Similarity: {highest_ratio}%)")

    # Perform case-insensitive matching after fuzzy matching
    idx = news_df[news_df["title"].str.lower() == best_match.lower()].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:6]
    article_indices = [i[0] for i in sim_scores]
    
    # Check if there are valid articles to return
    if len(article_indices) == 0:
        print("No similar articles found.")
        return pd.DataFrame()

    related_articles = news_df.iloc[article_indices][["title", "link", "image", "category"]]
    return related_articles

# Function for collaborative filtering recommendations
def collaborative_recommendations(news_df, user_id, svd, user_article_ratings):
    """Generates collaborative filtering recommendations using Surprise SVD."""
    if user_id not in user_article_ratings["user_id"].values:
        print(f"No recommendations: User ID '{user_id}' not found.")
        return pd.DataFrame()

    user_rated = user_article_ratings[user_article_ratings["user_id"] == user_id]["article_id"].tolist()
    article_predictions = [(i, svd.predict(user_id, i).est) for i in range(len(news_df)) if i not in user_rated]
    
    # If no recommendations can be made (e.g., user has rated all articles), return empty
    if len(article_predictions) == 0:
        print(f"No new recommendations available for user ID '{user_id}'.")
        return pd.DataFrame()

    article_predictions = sorted(article_predictions, key=lambda x: x[1], reverse=True)[:5]
    article_indices = [i[0] for i in article_predictions]
    
    return news_df.iloc[article_indices][["title", "link", "image"]]

# For testing
if __name__ == "__main__":
    news_df = get_news_dataframe()  # Get the news DataFrame from fetch_news.py
    cosine_sim, vectorizer, svd, user_article_ratings = build_recommendation_models(news_df)
    
    # Example for content-based recommendations
    title_to_search = "Israeli air strike kills top Hamas official in Gaza"  # Use a valid title from the dataset
    print(content_based_recommendations(news_df, title_to_search, cosine_sim))
    
    # Example for collaborative filtering recommendations
    user_id_to_search = 1  # Make sure this user exists
    print(collaborative_recommendations(news_df, user_id_to_search, svd, user_article_ratings))

    # Debugging output
    #print(news_df.isnull().sum())  # Check for missing values
    #print(news_df.head())  # Preview data
