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
1. Clone the repository:
   ```sh
   git clone https://github.com/your-username/tiktok-scraper.git
   cd tiktok-scraper

2. install the required:
   ```sh
   pip install -r requirements.txt

3. Start the Flask server:
   ```sh
   python app.py

### Chrome Extension Setup

1. Open Chrome and navigate to chrome://extensions/
2. Enable "Developer mode" in the top right corner
3. Click "Load unpacked" and select the directory containing the extension files
4. The TikTok Scraper extension should now appear in your Chrome toolbar

## Usage

1. Navigate to a TikTok post in Chrome
2. Click the TikTok Scraper extension icon
3. Click "Scrape Comments" in the popup
4. Wait for the scraping and analysis process to complete
5. The results will open in a new tab, displaying sentiment analysis and comment data

## Important Notes

- As of now, it is not possible to extract comments without manual intervention
- This is not an official TikTok API and may be subject to changes in TikTok's website       structure

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is for educational purposes only. Be sure to comply with TikTok's terms of service and respect user privacy when using this scraper.
