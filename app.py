# Import necessary modules
from flask import Flask, render_template, redirect, url_for, flash, request
from datetime import datetime
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from forms import SightingForm, LoginForm, RegistrationForm, UserProfileForm
from werkzeug.utils import secure_filename
import os
from io import BytesIO
import secrets
import time
from flask_migrate import Migrate
from sqlalchemy import or_
from flask_login import login_user, current_user, login_required
from flask_mail import Message
from flask_mail import Mail
from sqlalchemy.exc import IntegrityError


# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = '3398c019976ffdefa09991e7255d60aa'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wildlife.db'

app.config['MAIL_SERVER'] = 'smtp.mail.yahoo.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'bikorimanadesire@yahoo.com'
app.config['MAIL_PASSWORD'] = 'Raisa@#1'

mail = Mail(app)

from models import User, WildlifeSighting, db, Location, Species, Observation, Image, Video
# Initialize SQLAlchemy for database operations
db.init_app(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)

# Set up the directory where images and videos will be stored
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize Flask-Login for user authentication
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Routes for authentication
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data
        password = form.password.data
        
        # Check if the identifier is an email
        user = User.query.filter_by(email=identifier).first()
        
        # If not found by email, check by username
        if not user:
            user = User.query.filter_by(username=identifier).first()
        
        if user and user.check_password(password):
            # Log the user in using Flask-Login's login_user function
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email/username or password.', 'danger')
    
    return render_template('login.html', title='Login', form=form)
# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create a new user instance
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )

            # Add user to the database
            db.session.add(new_user)
            db.session.commit()

            # Send email verification message
            send_verification_email(new_user)

            flash('Account created successfully. Please check your email to verify your account.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            # Handle IntegrityError (duplicate email)
            db.session.rollback()
            flash('Email address already exists.', 'danger')
            return redirect(url_for('register'))
    return render_template('register.html', title='Register', form=form)

def send_verification_email(user):
    token = user.verification_token
    msg = Message('Verify Your Email', recipients=[user.email])
    verification_url = url_for('verify_email', token=token, _external=True)
    msg.body = f'Click the following link to verify your email: {verification_url}'
    mail.send(msg)

@app.route('/verify_email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        if user.is_verified:
            flash('Your email has already been verified.', 'info')
        else:
            if user.verify_email_token(token):
                flash('Your email has been verified successfully.', 'success')
            else:
                flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('login'))
    else:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('login'))
# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# User profile route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UserProfileForm()

    # Check if the current user has a profile
    if not hasattr(current_user, 'profile'):
        current_user.profile = UserProfile()

    if form.validate_on_submit():
        # Update user's profile
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.profile_image.data:
            # Handle profile image upload
            profile_image = save_profile_image(form.profile_image.data)
            current_user.profile.profile_image = profile_image
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        # Populate the form with current user's data
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('profile.html', form=form)

# Function to save profile image
def save_profile_image(form_profile_image):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_profile_image.filename)
    profile_image_fn = random_hex + f_ext
    profile_image_path = os.path.join(app.root_path, 'static/profile_pics', profile_image_fn)

    # Create the 'static/profile_pics' directory if it doesn't exist
    os.makedirs(os.path.join(app.root_path, 'static/profile_pics'), exist_ok=True)

    form_profile_image.save(profile_image_path)
    return profile_image_fn
@app.route('/dashboard')
@login_required
def dashboard():
    # Retrieve all wildlife sightings associated with the current user
    user_sightings = WildlifeSighting.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', title='Dashboard', sightings=user_sightings)


class GPSData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default =datetime.utcnow)
    animal_id = db.Column(db.Integer)

    def __repr__(self):
        return f'<GPSData {self.id}>'

@app.route('/realtime')
def realtime():
    return render_template('realtime.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('subscribe')
def handle_subscribe(room):
    join_room(room)

@socketio.on('unsubscribe')
def handle_unsubscribe(room):
    leave_room(room)

def emit_data():
    while True:
        # Mock data for demonstration purposes
        data = {'latitude': 51.505, 'longitude': -0.09, 'animal_id': 1}
        
        # Save data to the database
        gps_data = GPSData(latitude=data['latitude'], longitude=data['longitude'], animal_id=data['animal_id'])
        db.session.add(gps_data)
        db.session.commit()
        
        # Emit data to subscribers in real-time
        socketio.emit('update_data', data, room='wildlife_tracking')
        time.sleep(5)

# Route for adding a wildlife sighting

@app.route('/add_sighting', methods=['GET', 'POST'])
@login_required
def add_sighting():
    form = SightingForm()

    if form.validate_on_submit():
        species_name = form.species.data
        location_name = form.location.data
        date = form.date.data
        observation_notes = form.observation_notes.data

        # Check if species already exists in the database
        species = Species.query.filter_by(name=species_name).first()
        if not species:
            # If species does not exist, create a new one
            species = Species(name=species_name)
            db.session.add(species)

        # Check if location already exists in the database
        location = Location.query.filter_by(name=location_name).first()
        if not location:
            # If location does not exist, create a new one
            location = Location(name=location_name)
            db.session.add(location)

        # Create a new WildlifeSighting object
        new_sighting = WildlifeSighting(
            species=species,
            location=location,
            date=date,
            user=current_user,
        )

        # Create a new Observation object
        observation = Observation(date=date, notes=observation_notes)

        # Add the observation to the sighting
        new_sighting.observation = observation

        # Handle images
        if form.image.data:
            image_file = form.image.data
            image_data = image_file.read()
            filename = secure_filename(image_file.filename)
            image = Image(filename=filename, data=image_data, species=species)
            image.sighting = new_sighting
            db.session.add(image)

        # Handle videos
        if form.videos.data:
            filename = secure_filename(form.videos.data.filename)
            video_data = form.videos.data.read()  # Read binary data of the video file
            video = Video(filename=filename, data=video_data, species_id=species.id)  # Pass species_id instead of species
            video.sighting = new_sighting
            db.session.add(video)

        # Commit the new sighting and associated data to the database
        db.session.add(new_sighting)
        db.session.commit()

        flash('Sighting added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_sighting.html', title='Add Sighting', form=form)

# Route for deleting a wildlife sighting
@app.route('/delete_sighting/<int:sighting_id>', methods=['POST'])
@login_required
def delete_sighting(sighting_id):
    sighting = WildlifeSighting.query.get_or_404(sighting_id)
    db.session.delete(sighting)
    db.session.commit()
    flash('Wildlife sighting deleted!', 'success')
    return redirect(url_for('index'))

# Route for the index page with sightings and search functionality
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_term = request.form.get('search_term')
        sightings = WildlifeSighting.query.filter(
            or_(WildlifeSighting.species.ilike(f"%{search_term}%"), WildlifeSighting.location.ilike(f"%{search_term}%"))
        ).all()
    else:
        sightings = WildlifeSighting.query.all()
    return render_template('index.html', sightings=sightings)

# Route for the about us page
@app.route('/about')
def about():
    return render_template('about.html')

# Route for the wildlife page
@app.route('/wildlife')
def wildlife():
    return render_template('wildlife.html')

# Route for the wildlife species page
# Route for displaying nearby wildlife species
@app.route('/wildlife/species')
def wildlife_species():
    # Check if latitude and longitude are provided in the query parameters
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')

    # Check if latitude and longitude are provided
    if not latitude or not longitude:
        # Render the template without species data
        return render_template('wildlife_species.html', error='Latitude and longitude are required parameters.')

    try:
        # Call the IUCN Red List API to get nearby species
        url = f'https://apiv3.iucnredlist.org/api/v3/nearest_species/latitude/{latitude}/longitude/{longitude}'
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the JSON response
        data = response.json()
        # Extract relevant information (e.g., species name, threat status)
        nearby_species = [{'scientific_name': species['scientific_name'], 'threat_status': species['category']} for species in data['result']]

        # Render the template with species data
        return render_template('wildlife_species.html', nearby_species=nearby_species)

    except requests.RequestException as e:
        # Render the template with an error message
        return render_template('wildlife_species.html', error='Failed to retrieve nearby species. Error: ' + str(e))

# Route for the wildlife sightings page
@app.route('/wildlife/sightings')
def wildlife_sightings():
    return render_template('wildlife_sightings.html')

# Route for displaying nearby conservation areas
@app.route('/conservation_areas')
def conservation_areas():
    try:
        # Get user's location from request
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')

        # Make a nearby search request to Google Places API
        places_result = gmaps.places_nearby(location=(latitude, longitude), radius=10000, type='park')

        # Extract relevant information from the API response
        conservation_areas = []
        for place in places_result['results']:
            name = place['name']
            location = place['geometry']['location']
            address = place.get('vicinity', 'Address not available')
            rating = place.get('rating', 'Rating not available')
            opening_hours = place.get('opening_hours', {}).get('weekday_text', ['Opening hours not available'])
            photos = place.get('photos', [])
            photo_url = photos[0]['photo_reference'] if photos else None

            conservation_areas.append({
                'name': name,
                'latitude': location['lat'],
                'longitude': location['lng'],
                'address': address,
                'rating': rating,
                'opening_hours': opening_hours,
                'photo_url': photo_url
            })

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = 10
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_areas = conservation_areas[start_idx:end_idx]

        # Render the template with the list of conservation areas
        return render_template('conservation_areas.html', conservation_areas=paginated_areas)

    except Exception as e:
        # Handle any errors that occur during the process
        return render_template('error.html', error_message=str(e))

# Route for the map page
@app.route('/map')
def map():
    return render_template('map.html')

# Route for the real-time map page
@app.route('/map/real-time')
def real_time_map():
    return render_template('real_time_map.html')

# Route for the historical data page
@app.route('/map/historical-data')
def historical_data():
    return render_template('historical_data.html')

# Route for the notifications page
@app.route('/notifications')
def notifications():
    return render_template('notifications.html')

# Route for the admin dashboard page
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

# Route for the contact us page
@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)
