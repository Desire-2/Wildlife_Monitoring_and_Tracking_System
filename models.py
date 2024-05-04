from itsdangerous import URLSafeTimedSerializer
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import LargeBinary
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_token = db.Column(db.String(100), unique=True)

    # Define relationship with UserProfile model
    user_profile = db.relationship('UserProfile', back_populates='user', uselist=False)
    wildlife_sighting = db.relationship('WildlifeSighting', back_populates='user')

    def __init__(self, username, email, password, first_name, last_name):
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.generate_verification_token()

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def generate_verification_token(self):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        self.verification_token = s.dumps(self.email)

    def verify_email_token(self, token):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, max_age=86400)  # Token expires after 24 hours
        except:
            return False
        if email == self.email:
            self.is_verified = True
            self.verification_token = None
            db.session.commit()
            return True
        return False

    @classmethod
    def create_user(cls, username, email, password, first_name, last_name):
        user = cls(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
        db.session.add(user)
        db.session.commit()
        return user

# User Profile model
class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Add more fields as needed for user profile information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)

    # Define the back reference to the User model
    user = db.relationship('User', back_populates='user_profile')

# WildlifeSighting model
class WildlifeSighting(db.Model):
    __tablename__ = 'wildlife_sightings'
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    observation_id = db.Column(db.Integer, db.ForeignKey('observations.id'))  # Add this line

    species = db.relationship('Species', backref=db.backref('sightings', lazy=True))
    location = db.relationship('Location', backref=db.backref('sightings', lazy=True))
    user = db.relationship('User', back_populates='wildlife_sighting')

    # Define the relationship with Observation model
    observation = db.relationship('Observation', uselist=False, backref='sighting')
    
# Location model
class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

# Species model
class Species(db.Model):
    __tablename__ = 'species'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    # Define relationships
    images = db.relationship('Image', back_populates='species')
    videos = db.relationship('Video', back_populates='species')
    observations = db.relationship('WildlifeSighting', backref='observed_species', foreign_keys='WildlifeSighting.species_id')
    habitat_id = db.Column(db.Integer, db.ForeignKey('habitats.id'))

    # Define relationship with Habitat model
    habitat = db.relationship('Habitat', backref=db.backref('species', lazy=True))

# Habitat model
class Habitat(db.Model):
    __tablename__ = 'habitats'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

# Observation model
class Observation(db.Model):
    __tablename__ = 'observations'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)

# Image model
class Image(db.Model):
    __tablename__ = 'images'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    wildlife_sighting_id = db.Column(db.Integer, db.ForeignKey('wildlife_sighting.id'), nullable=False)
    wildlife_sighting = db.relationship('WildlifeSighting', backref=db.backref('images', lazy=True))

# Video model
class Video(db.Model):
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    wildlife_sighting_id = db.Column(db.Integer, db.ForeignKey('wildlife_sighting.id'), nullable=False)
    wildlife_sighting = db.relationship('WildlifeSighting', backref=db.backref('videos', lazy=True))

class GPSData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    animal_id = db.Column(db.Integer)

    def __repr__(self):
        return f'<GPSData {self.id}>'
