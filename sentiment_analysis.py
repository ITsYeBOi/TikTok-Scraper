import pandas as pd
import numpy as np
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Initialize VADER sentiment analyzer
vader = SentimentIntensityAnalyzer()

def preprocess_text(text):
    # Convert to string if not already a string
    text = str(text)
    
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Tokenize
    tokens = word_tokenize(text)
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    # Join tokens back into string
    return ' '.join(tokens)

def get_vader_sentiment(text):
    scores = vader.polarity_scores(text)
    if scores['compound'] > 0.05:
        return 'positive'
    elif scores['compound'] < -0.05:
        return 'negative'
    else:
        return 'neutral'

def get_textblob_sentiment(text):
    analysis = TextBlob(text)
    if analysis.sentiment.polarity > 0.05:
        return 'positive'
    elif analysis.sentiment.polarity < -0.05:
        return 'negative'
    else:
        return 'neutral'

def train_custom_classifier(comments, labels):
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(comments, labels, test_size=0.2, random_state=42)

    # Create a pipeline that combines TF-IDF vectorization with a Linear SVC classifier
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(preprocessor=preprocess_text)),
        ('clf', LinearSVC()),
    ])

    # Train the model
    pipeline.fit(X_train, y_train)

    # Evaluate the model
    y_pred = pipeline.predict(X_test)
    print(classification_report(y_test, y_pred))

    return pipeline

def get_ensemble_sentiment(text, custom_classifier):
    vader_sentiment = get_vader_sentiment(text)
    textblob_sentiment = get_textblob_sentiment(text)
    custom_sentiment = custom_classifier.predict([text])[0]

    # Simple voting mechanism
    sentiments = [vader_sentiment, textblob_sentiment, custom_sentiment]
    return max(set(sentiments), key=sentiments.count)

def analyze_comments(comments):
    df = pd.DataFrame(comments)

    # Preprocess comments
    df['processed_text'] = df['Comment_Text'].apply(preprocess_text)

    # Generate labels for training (you might want to manually label a subset for better accuracy)
    df['sentiment_label'] = df['processed_text'].apply(get_vader_sentiment)

    # Train custom classifier
    custom_classifier = train_custom_classifier(df['processed_text'], df['sentiment_label'])

    # Apply ensemble sentiment analysis
    df['sentiment'] = df['processed_text'].apply(lambda x: get_ensemble_sentiment(x, custom_classifier))

    # Categorize comments
    positive_comments = df[df['sentiment'] == 'positive'].to_dict('records')
    negative_comments = df[df['sentiment'] == 'negative'].to_dict('records')
    neutral_comments = df[df['sentiment'] == 'neutral'].to_dict('records')

    return positive_comments, negative_comments, neutral_comments, df