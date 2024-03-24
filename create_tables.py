from app import app, db
from models import User, WildlifeSighting, UserProfile, Location, Species, Habitat, Observation, Image, Video, GPSData

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

