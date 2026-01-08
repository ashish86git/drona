from flask import Flask, render_template, request, jsonify, url_for, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

# Initialize Flask app
app = Flask(__name__)

# --- आपके PostgreSQL डेटाबेस क्रेडेंशियल्स का उपयोग करके कॉन्फ़िगरेशन ---
# यह कॉन्फ़िगरेशन सीधे आपके दिए गए क्रेडेंशियल्स का उपयोग करता है।
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://{user}:{password}@{host}:{port}/{database}'.format(
        user='u7tqojjihbpn7s',
        password='p1b1897f6356bab4e52b727ee100290a84e4bf71d02e064e90c2c705bfd26f4a5',
        host='c7s7ncbk19n97r.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com',
        port=5432,
        database='d8lp4hr6fmvb9m'
    )
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure the secret key for session management
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_super_secret_key')

# Configure the directory for image uploads
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'blog_images')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the database
db = SQLAlchemy(app)

# Define a simple admin username and password for this example
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'password123')


# Define the Blog Post database model
class BlogPost(db.Model):
    __tablename__ = 'blog_post'  # PostgreSQL के लिए तालिका का नाम
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        """Converts the model instance to a dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url
        }


# Create the database tables
with app.app_context():
    # यह लाइन डेटाबेस में 'blog_post' तालिका बनाती है अगर यह पहले से मौजूद नहीं है।
    db.create_all()


# Main route to render the HTML template
@app.route('/')
def home():
    """Renders the main index page."""
    return render_template('index.html')


# Admin login route
@app.route('/admin', methods=['POST'])
def admin_login():
    """Handles admin login requests."""
    username = request.form.get('username')
    password = request.form.get('password')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        return jsonify({'message': 'Login successful!'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


# Admin logout route
@app.route('/logout', methods=['POST'])
def admin_logout():
    """Handles admin logout requests."""
    session.pop('logged_in', None)
    return jsonify({'message': 'Logout successful!'}), 200


# Check login status
@app.route('/is_logged_in')
def is_logged_in():
    """Checks if the user is logged in."""
    if session.get('logged_in'):
        return "Logged In", 200
    else:
        return "Not Logged In", 401


# API endpoint to get all blog posts
@app.route('/api/blogs', methods=['GET'])
def get_blogs():
    """
    Fetches all blog posts from the database and returns them as a JSON array.
    """
    blogs = BlogPost.query.all()
    return jsonify([blog.to_dict() for blog in blogs])


# API endpoint to add a new blog post (admin-only)
@app.route('/api/add_blog', methods=['POST'])
def add_blog():
    """
    Receives new blog post data and saves it to the database,
    only if the user is authenticated as an admin.
    """
    # Check if the user is logged in
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized. Please log in as admin.'}), 401

    # Check if a file was sent
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided.'}), 400

    image = request.files['image']
    title = request.form.get('title')
    content = request.form.get('content')

    # Validate inputs
    if not title or not content:
        return jsonify({'error': 'Title and content are required.'}), 400

    # Secure the filename before saving
    filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(image_path)

    # Get the URL for the saved image
    image_url = url_for('static', filename=f'blog_images/{filename}')

    # Create and save the new blog post to the database
    new_post = BlogPost(title=title, content=content, image_url=image_url)
    db.session.add(new_post)
    db.session.commit()

    return jsonify({
        'message': 'Blog added successfully!',
        'post': new_post.to_dict()
    }), 201


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
