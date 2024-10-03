from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import pandas as pd
from flask_caching import Cache
import uuid

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'

# Configure Flask-Caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

def analyze_comments(comments):
    positive_comments = []
    purchase_interest = []

    for _, row in comments.iterrows():
        summary = {
            "Nickname": row.get('Nickname', ''),
            "User @": row.get('User @', ''),
            "Comment_Text": row.get('Comment_Text', ''),
            "Time": row.get('Time', ''),
            "Likes": row.get('Likes', '')
        }

        if pd.notna(row.get('Comment_Text')):
            comment_text = str(row.get('Comment_Text', '')).lower()
            if any(keyword in comment_text for keyword in ["love", "great", "cool", "nice", "reward", "interested", "store"]):
                positive_comments.append(summary)

            if any(keyword in comment_text for keyword in ["purchase", "buy", "store", "order"]):
                purchase_interest.append(summary)

    return positive_comments, purchase_interest

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    comments_data = data['comments']
    metadata = data['metadata']
    comments = pd.DataFrame(comments_data)
    
    positive_comments, purchase_interest = analyze_comments(comments)
    
    # Generate a unique ID for this analysis
    analysis_id = str(uuid.uuid4())
    
    # Store the results in the cache
    cache.set(analysis_id, {
        'positive_comments': positive_comments,
        'purchase_interest': purchase_interest,
        'positive_count': len(positive_comments),
        'purchase_count': len(purchase_interest),
        'post_metadata': metadata,
        'all_comments': comments_data
    })
    
    # Store only the analysis ID in the session
    session['analysis_id'] = analysis_id
    
    return jsonify({'status': 'success'})

@app.route('/results')
def results():
    analysis_id = session.get('analysis_id')
    if not analysis_id:
        return jsonify({'error': 'No analysis ID found'}), 404
    
    results = cache.get(analysis_id)
    if not results:
        return jsonify({'error': 'No results found for this analysis ID'}), 404
    
    return render_template('results.html', 
                           positive_comments=results.get('positive_comments', []),
                           purchase_interest=results.get('purchase_interest', []),
                           positive_count=results.get('positive_count', 0),
                           purchase_count=results.get('purchase_count', 0),
                           post_metadata=results.get('post_metadata', {}),
                           all_comments=results.get('all_comments', []))

if __name__ == '__main__':
    app.run(debug=True)
