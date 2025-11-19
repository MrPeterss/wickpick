from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Define Candle model
class Candle(db.Model):
    __tablename__ = 'candles'
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    category = db.Column(db.String(128), nullable=False)
    company = db.Column(db.String(128))
    link = db.Column(db.String(512))
    description = db.Column(db.Text)
    overall_rating = db.Column(db.String(16))
    overall_reviewcount = db.Column(db.String(16))
    img_url = db.Column(db.String(256))
    liked = db.Column(db.String(16), default="0")
    
    # Relationship to reviews
    reviews = db.relationship('Review', backref='candle', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Candle {self.id}: {self.name}>'

# Define Review model
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candle_id = db.Column(db.String(64), db.ForeignKey('candles.id'), nullable=False)
    review_body = db.Column(db.Text)
    rating_value = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<Review {self.id} for Candle {self.candle_id}>'

