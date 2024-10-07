# TikTok Scraper & Downloader

This project provides a Chrome extension and backend server for scraping and analyzing TikTok comment data. It extracts comments from TikTok posts, performs sentiment analysis, and presents the results in a user-friendly format.

## Features

-  Scrape comments and metadata from TikTok posts
-  Perform sentiment analysis on the scraped comments
-  Categorize comments into positive, neutral, and negative sentiments
-  Display analysis results in an interactive web interface
-  Download post metadata and comment data
-  Chrome extension for easy access to scraping functionality

## Project Structure

1. Chrome Extension
   - manifest.json: Extension configuration
   - popup.html & popup.js: Extension popup interface
   - content.js: Content script for scraping TikTok pages
   - background.js: Background script for communication with the backend

2. Backend Server:
   - app.py: Flask server for handling requests and serving results
   - sentiment_analysis.py: Sentiment analysis functionality

3. Frontend:
   - results.html: Template for displaying analysis results
     
## Installation

### Prerequisites
- Python 3.7+
- Chrome Browser

### Backend Setup
1. Clone the repository
   git clone https://github.com/your-username/tiktok-scraper.git
   cd tiktok-scraper

2. install the required



