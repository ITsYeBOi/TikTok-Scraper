from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import pandas as pd
import os
from werkzeug.utils import secure_filename
import csv
import chardet
from flask import redirect, url_for

app = Flask(__name__)
CORS(app)
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

    comment_start_index = next((i for i, row in enumerate(rows) if row and row[0] == 'Comment Number (ID)'), None)

    if comment_start_index is None:
        raise ValueError("CSV format is incorrect. Unable to find comment data.")

    metadata = {row[0]: row[1] for row in rows[:comment_start_index] if len(row) >= 2}

    comment_headers = rows[comment_start_index]
    comments = pd.DataFrame(rows[comment_start_index+1:], columns=comment_headers)

    return metadata, comments

def analyze_comments(comments):
    positive_comments = []
    purchase_interest = []

    for _, row in comments.iterrows():
        summary = {
            "Nickname": row.get('Nickname', ''),
            "User @": row.get('User @', ''),
            "User URL": row.get('User URL', ''),
            "Comment_Text": row.get('Comment_Text', ''),  # Changed from 'Comment Text' to 'Comment_Text'
            "Time": row.get('Time', ''),
            "Likes": row.get('Likes', ''),
            "Profile Picture URL": row.get('Profile Picture URL', ''),
            "Is 2nd Level Comment": row.get('Is 2nd Level Comment', ''),
            "User Replied To": row.get('User Replied To', ''),
            "Number of Replies": row.get('Number of Replies', ''),
        }

        if pd.notna(row.get('Comment_Text')):  # Changed from 'Comment Text' to 'Comment_Text'
            comment_text = str(row.get('Comment_Text', '')).lower()  # Changed from 'Comment Text' to 'Comment_Text'
            if any(keyword in comment_text for keyword in ["love", "great", "cool", "nice", "reward", "interested", "store"]):
                positive_comments.append(summary)

            if any(keyword in comment_text for keyword in ["purchase", "buy", "store", "order"]):
                purchase_interest.append(summary)

    return positive_comments, purchase_interest

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

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    comments_data = data['comments']
    metadata = data['metadata']
    comments = pd.DataFrame(comments_data)
    
    positive_comments, purchase_interest = analyze_comments(comments)
    
    session['results'] = {
        'positive_comments': positive_comments,
        'purchase_interest': purchase_interest,
        'positive_count': len(positive_comments),
        'purchase_count': len(purchase_interest),
        'post_metadata': metadata
    }
    
    return jsonify({'status': 'success'})

# Add a new route to handle CORS preflight requests
@app.route('/analyze', methods=['OPTIONS'])
def handle_options_request():
    response = app.make_default_options_response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

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
