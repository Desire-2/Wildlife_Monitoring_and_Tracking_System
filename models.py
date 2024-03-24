from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

from app import db
db = SQLAlchemy()

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # Define relationship with UserProfile model
    profile = db.relationship('UserProfile', backref=db.backref('user', uselist=False), uselist=False)
# User Profile model
class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Add more fields as needed for user profile information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)

     # Define the back reference to the User model
    user = db.relationship('User', back_populates='profile')

# WildlifeSighting model
class WildlifeSighting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('sightings', lazy=True))
    species = db.relationship('Species', backref=db.backref('sightings', lazy=True))
    location = db.relationship('Location', backref=db.backref('sightings', lazy=True))


# Location model
class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

# Species model
class Species(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

# Habitat model
class Habitat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

# Observation model
class Observation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    wildlife_sighting_id = db.Column(db.Integer, db.ForeignKey('wildlife_sighting.id'), nullable=False)
    wildlife_sighting = db.relationship('WildlifeSighting', backref=db.backref('observations', lazy=True))

# Image model
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    wildlife_sighting_id = db.Column(db.Integer, db.ForeignKey('wildlife_sighting.id'), nullable=False)
    wildlife_sighting = db.relationship('WildlifeSighting', backref=db.backref('images', lazy=True))

# Video model
class Video(db.Model):
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
