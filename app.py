from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import pandas as pd
from flask_caching import Cache
import uuid
from sentiment_analysis import analyze_comments  # Import the analyze_comments function

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'

# Configure Flask-Caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    comments_data = data['comments']
    metadata = data['metadata']
    
    positive_comments, negative_comments, neutral_comments, df = analyze_comments(comments_data)
    
    results = {
        'positive_comments': positive_comments,
        'negative_comments': negative_comments,
        'neutral_comments': neutral_comments,
        'positive_count': len(positive_comments),
        'negative_count': len(negative_comments),
        'neutral_count': len(neutral_comments),
        'sentiment_distribution': df['sentiment'].value_counts().to_dict(),
        'post_metadata': metadata,
        'all_comments': comments_data
    }
    
    # Generate a unique ID for this analysis
    analysis_id = str(uuid.uuid4())
    
    # Store the results in the cache
    cache.set(analysis_id, results)
    
    # Store only the analysis ID in the session
    session['analysis_id'] = analysis_id
    
    return jsonify({'status': 'success', 'analysis_id': analysis_id})

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
                           negative_comments=results.get('negative_comments', []),
                           neutral_comments=results.get('neutral_comments', []),
                           positive_count=results.get('positive_count', 0),
                           negative_count=results.get('negative_count', 0),
                           neutral_count=results.get('neutral_count', 0),
                           sentiment_distribution=results.get('sentiment_distribution', {}),
                           post_metadata=results.get('post_metadata', {}),
                           all_comments=results.get('all_comments', []))

if __name__ == '__main__':
    app.run(debug=True)
