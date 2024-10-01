from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import pandas as pd
import os
from werkzeug.utils import secure_filename
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import tempfile
import traceback
import time
import chardet
from flask import jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']

def process_csv(csv_file):
    encoding = detect_encoding(csv_file)
    with open(csv_file, 'r', encoding=encoding) as file:
        csv_reader = csv.reader(file)
        rows = list(csv_reader)

    # Find the index where the comment data starts
    comment_start_index = next((i for i, row in enumerate(rows) if row and row[0] == 'Comment Number (ID)'), None)

    if comment_start_index is None:
        raise ValueError("CSV format is incorrect. Unable to find comment data.")

    # Extract metadata
    metadata = {row[0]: row[1] for row in rows[:comment_start_index] if len(row) >= 2}

    # Extract comments
    comment_headers = rows[comment_start_index]
    comments = pd.DataFrame(rows[comment_start_index+1:], columns=comment_headers)

    return metadata, comments

def analyze_comments(comments):
    positive_comments = []
    purchase_interest = []

    for _, row in comments.iterrows():
        summary = {
            "Nickname": row['Nickname'],
            "User @": row['User @'],
            "User URL": row['User URL'],
            "Comment_Text": row['Comment Text'],
            "Time": row['Time'],
            "Likes": row['Likes'],
            "Profile Picture URL": row['Profile Picture URL'],
            "Is 2nd Level Comment": row['Is 2nd Level Comment'],
            "User Replied To": row['User Replied To'],
            "Number of Replies": row['Number of Replies'],
        }

        if pd.notna(row['Comment Text']):
            comment_text = str(row['Comment Text']).lower()
            if any(keyword in comment_text for keyword in ["love", "great", "cool", "nice", "reward", "interested", "store"]):
                positive_comments.append(summary)

            if any(keyword in comment_text for keyword in ["purchase", "buy", "store", "order"]):
                purchase_interest.append(summary)

    return positive_comments, purchase_interest

def scrape_tiktok_comments(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options) as driver:
        try:
            print(f"Navigating to URL: {url}")
            driver.get(url)
            
            print("Waiting for page to load...")
            time.sleep(5)  # Add a 5-second delay
            
            print("Waiting for comment container to load...")
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "DivCommentListContainer")]'))
            )
            print("Comment container loaded.")
            
            print("Loading scraper script...")
            with open('tiktok_scraper.js', 'r') as file:
                js_code = file.read()
            
            print("Executing scraper script...")
            driver.execute_script(js_code)
            
            print("Waiting for scraping to complete...")
            WebDriverWait(driver, 300).until(lambda d: d.execute_script("return window.scrapedData !== undefined"))
            
            print("Retrieving scraped data...")
            result = driver.execute_script("return window.scrapedData;")
            
            if not result:
                raise ValueError("No data returned from the JavaScript execution")
            
            data = json.loads(result)
            csv_content = data.get('csv')
            if not csv_content:
                raise ValueError("CSV content is None or empty")
            
            print("Scraping completed successfully.")
            return csv_content
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            print(f"Current URL: {driver.current_url}")
            print(f"Page source: {driver.page_source[:1000]}...")  # Print first 1000 characters of page source
            traceback.print_exc()
            return None
        

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        try:
            post_metadata, comments = process_csv(filepath)
            positive_comments, purchase_interest = analyze_comments(comments)
            
            session['results'] = {
                'positive_comments': positive_comments,
                'purchase_interest': purchase_interest,
                'positive_count': len(positive_comments),
                'purchase_count': len(purchase_interest),
                'post_metadata': post_metadata
            }
            
            os.remove(filepath)  # Remove the file after processing
            return jsonify({'redirect': url_for('results')})
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type'}), 400

@app.route('/scrape', methods=['POST'])
def scrape_url():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        csv_content = scrape_tiktok_comments(url)
        if csv_content is None:
            return jsonify({'error': 'Failed to scrape TikTok URL'}), 500

        # Save CSV content to a temporary file
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False, suffix='.csv') as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name

        # Process CSV file
        post_metadata, comments = process_csv(temp_file_path)

        # Clean up
        os.remove(temp_file_path)

        # Analyze comments
        positive_comments, purchase_interest = analyze_comments(comments)

        # Store results in session
        session['results'] = {
            'positive_comments': positive_comments,
            'purchase_interest': purchase_interest,
            'positive_count': len(positive_comments),
            'purchase_count': len(purchase_interest),
            'post_metadata': post_metadata
        }

        return jsonify({'redirect': url_for('results')})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results')
def results():
    results = session.get('results')
    if not results:
        return redirect(url_for('index'))
    
    return render_template('results.html', 
                           positive_comments=results.get('positive_comments', []),
                           purchase_interest=results.get('purchase_interest', []),
                           positive_count=results.get('positive_count', 0),
                           purchase_count=results.get('purchase_count', 0),
                           post_metadata=results.get('post_metadata', {}))
if __name__ == '__main__':
    app.run(debug=True)
