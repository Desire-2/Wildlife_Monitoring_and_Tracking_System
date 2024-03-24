# Import necessary modules
from flask import Flask, render_template, redirect, url_for, flash, request
from datetime import datetime
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from forms import WildlifeSightingForm, LoginForm, RegistrationForm, UserProfileForm
from werkzeug.utils import secure_filename
import os
import secrets
import time
from flask_migrate import Migrate
from sqlalchemy import or_
# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = '3398c019976ffdefa09991e7255d60aa'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wildlife.db'

# Initialize SQLAlchemy for database operations
db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)

# Set up the directory where images and videos will be stored
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Define User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Define WildlifeSighting model
class WildlifeSighting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('sightings', lazy=True))
    images = db.relationship('Image', backref='sighting', lazy=True)
    videos = db.relationship('Video', backref='sighting', lazy=True)

# Define Image model
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    sighting_id = db.Column(db.Integer, db.ForeignKey('wildlife_sighting.id'), nullable=False)

# Define Video model
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    sighting_id = db.Column(db.Integer, db.ForeignKey('wildlife_sighting.id'), nullable=False)

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
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', form=form)

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

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
class GPSData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
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
    form = WildlifeSightingForm()
    if form.validate_on_submit():
        species = form.species.data
        location = form.location.data
        date = form.date.data

        # Create a new WildlifeSighting object
        new_sighting = WildlifeSighting(species=species, location=location, date=date, user_id=current_user.id)
        db.session.add(new_sighting)
        db.session.commit()

        # Handle image files
        for file in request.files.getlist('images'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Create an Image object and associate it with the new sighting
                new_image = Image(filename=filename, sighting_id=new_sighting.id)
                db.session.add(new_image)
        
        # Handle video files
        for file in request.files.getlist('videos'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Create a Video object and associate it with the new sighting
                new_video = Video(filename=filename, sighting_id=new_sighting.id)
                db.session.add(new_video)

        db.session.commit()
        flash('New wildlife sighting added!', 'success')
        return redirect(url_for('index'))
    return render_template('add_sighting.html', form=form)

# Route for updating a wildlife sighting
@app.route('/update_sighting/<int:sighting_id>', methods=['GET', 'POST'])
@login_required
def update_sighting(sighting_id):
    sighting = WildlifeSighting.query.get_or_404(sighting_id)
    form = WildlifeSightingForm(obj=sighting)
    if form.validate_on_submit():
        form.populate_obj(sighting)

        # Handle image files
        for file in request.files.getlist('images'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Create an Image object and associate it with the updated sighting
                new_image = Image(filename=filename, sighting_id=sighting.id)
                db.session.add(new_image)
        
        # Handle video files
        for file in request.files.getlist('videos'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Create a Video object and associate it with the updated sighting
                new_video = Video(filename=filename, sighting_id=sighting.id)
                db.session.add(new_video)

        db.session.commit()
        flash('Wildlife sighting updated!', 'success')
        return redirect(url_for('index'))
    return render_template('update_sighting.html', form=form)

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
    return render_template('index.html', sightings=sightings,  sighting_id = 123)

if __name__ == '__main__':
    app.run(debug=True)
