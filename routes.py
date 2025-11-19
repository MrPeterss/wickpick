import json
import pandas as pd
from flask import render_template, request
from models import db, Candle, Review
from models.similarity import PandasSim

# Global similarity model - will be initialized in app.py
similarity = None
# Mapping from candle ID to DataFrame index
id_to_index_map = {}

def initialize_similarity():
    """Initialize similarity model with data from database"""
    global similarity, id_to_index_map
    
    # Load candles and reviews from database into DataFrames
    candles = Candle.query.all()
    reviews = Review.query.all()
    
    candles_data = []
    reviews_data = []
    
    # Create a mapping from candle ID to DataFrame index
    # Sort candles by ID to ensure consistent ordering
    sorted_candles = sorted(candles, key=lambda c: int(c.id) if c.id.isdigit() else 999999)
    
    for idx, candle in enumerate(sorted_candles):
        id_to_index_map[candle.id] = idx
        candle_info = {
            'id': candle.id,
            'name': candle.name,
            'category': candle.category,
            'description': candle.description,
            'overall_rating': candle.overall_rating,
            'overall_reviewcount': candle.overall_reviewcount,
            'link': candle.link,
            'img_url': candle.img_url,
            'liked': candle.liked if candle.liked else "0"
        }
        candles_data.append(candle_info)
    
    for review in reviews:
        review_info = {
            'candle_id': review.candle_id,
            'review_body': review.review_body,
            'rating_value': review.rating_value
        }
        reviews_data.append(review_info)
    
    candles_df = pd.DataFrame(candles_data)
    reviews_df = pd.DataFrame(reviews_data)
    
    # Initialize similarity model
    similarity = PandasSim(candles_df, reviews_df)

def register_routes(app):
    """Register all routes with the Flask app"""
    
    @app.route("/")
    def home():
        return render_template('base.html', title="Candle Search")

    @app.route("/candles")
    def candles_search():
        query = request.args.get("query", "")
        category = request.args.get("category", "").lower()

        if not similarity:
            return json.dumps({"error": "Similarity model not initialized"}), 500

        # Integrated Rocchio (only perform Rocchio if there is atleast some similarity)
        sim_df = similarity.retrieve_sorted_candles_svd(query)
        # max_sim_score = sim_df['sim_score'].max() if not sim_df.empty else 0
        # if (max_sim_score < 0.15 and max_sim_score > 0):
        # print("Rocchio running:")
        # query = similarity.get_query_suggestions(similarity.rocchio(query), num_terms=30)

        # sim_df = similarity.retrieve_sorted_candles_svd(query, use_rocchio=True)

        # Get reviews from database
        reviews = Review.query.all()
        reviews_data = []
        for review in reviews:
            review_info = {
                'candle_id': review.candle_id,
                'review_body': review.review_body,
                'rating_value': review.rating_value
            }
            reviews_data.append(review_info)
        reviews_df = pd.DataFrame(reviews_data)

        merged_df = pd.merge(sim_df, reviews_df, left_on='id', right_on='candle_id', how='inner')
        # Fix image URL path: replace 'images/' with 'candle-images/'
        merged_df['img_url'] = request.url_root + 'static/' + merged_df['img_url'].str.replace('images/', 'candle-images/', regex=False)

        if category:
            merged_df = merged_df[merged_df['category'].str.lower() == category]

        unique_candles = merged_df[['id', 'name', 'category', 'description', 'overall_rating',
                                    'overall_reviewcount', 'img_url', 'link', 'sim_score']].drop_duplicates()

        results = []
        for _, candle in unique_candles.iterrows():
            candle_reviews = merged_df[merged_df['id'] == candle['id']]
            
            # Convert candle ID to DataFrame index for similarity model
            # The similarity model uses 0-based indices corresponding to DataFrame index
            candle_id_str = candle['id']
            candle_index = id_to_index_map.get(candle_id_str, 0)
            
            candle_data = {
                'id': candle['id'],
                'name': candle['name'],
                'category': candle['category'],
                'description': candle['description'],
                'overall_rating': candle['overall_rating'],
                'overall_reviewcount': candle['overall_reviewcount'],
                'img_url': candle['img_url'],
                'link': candle['link'],
                'reviews': [],
                'sim_score': float(candle['sim_score']) if pd.notna(candle['sim_score']) else 0.0,
                'svd_labels_new': similarity.top_words_by_id.get(candle_index, []),
                'svd_dim_labels_values': similarity.svd_dim_labels_values(candle_index) if 0 <= candle_index < len(similarity.candles) else [],
                'similar_candles': similarity.similar_candles_by_id.get(candle_index, [])
            }

            for _, review in candle_reviews.iterrows():
                candle_data['reviews'].append({
                    'review_body': review['review_body'],
                    'rating_value': int(review['rating_value']) if pd.notna(review['rating_value']) else None
                })

            results.append(candle_data)
        # print(json.dumps(results[0], indent=2))
        return json.dumps(results)

