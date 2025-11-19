import json
import os
from flask import Flask
from flask_cors import CORS
from models import db, Candle, Review
from routes import register_routes, initialize_similarity

# Get the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

# Configure SQLite database - using 3 slashes for relative path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)

# Register routes
register_routes(app)

# Function to initialize database, change this to your own database initialization logic
def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Initialize database with data from init.json if empty
        if Candle.query.count() == 0:
            json_file_path = os.path.join(current_directory, 'init.json')
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                
                for key, candle_data in data.items():
                    # Determine liked status
                    liked = "1" if (candle_data['name'] == "Beach Walk®") or (candle_data['name'] == "Salted Caramel") else "0"
                    
                    candle = Candle(
                        id=key,
                        name=candle_data['name'],
                        category=candle_data['category'],
                        company=candle_data.get('company', ''),
                        link=candle_data['link'],
                        description=candle_data['description'],
                        overall_rating=candle_data['overall_rating'],
                        overall_reviewcount=candle_data['overall_reviewcount'],
                        img_url=candle_data['img_url'],
                        liked=liked
                    )
                    db.session.add(candle)
                    
                    # Add reviews for this candle
                    if 'reviews' in candle_data and candle_data['reviews']:
                        for review_id, review_data in candle_data['reviews'].items():
                            review = Review(
                                candle_id=key,
                                review_body=review_data['review_body'],
                                rating_value=review_data['rating_value']
                            )
                            db.session.add(review)
                
                db.session.commit()
                print("Database initialized with candles and reviews data")
        
        # Initialize similarity model after database is loaded
        initialize_similarity()
        print("Similarity model initialized")

init_db()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
