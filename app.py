import os
import logging
from flask import Flask, render_template, jsonify, redirect, url_for, request
from models import db, User, PropertyAlert, PropertyListing

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create and configure the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "avierpropertybotalertsecret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the database extension
db.init_app(app)

# Create templates folder if it doesn't exist
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

# Create a basic index.html template
index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Avier Homes Property Bot</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
</head>
<body class="bg-dark text-light">
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card bg-dark">
                    <div class="card-body">
                        <h1 class="card-title text-center mb-4">Avier Homes Property Bot</h1>
                        <p class="lead text-center">
                            Welcome to the Avier Homes Property Bot dashboard.
                        </p>
                        <div class="mt-4">
                            <h2>Bot Status</h2>
                            <p>The Telegram bot is currently running. Access it on Telegram by searching for <strong>@AvierHomesBot</strong>.</p>
                            
                            <h2 class="mt-4">Statistics</h2>
                            <ul class="list-group list-group-flush bg-dark">
                                <li class="list-group-item bg-dark">Users: <span class="badge bg-primary">{{ user_count }}</span></li>
                                <li class="list-group-item bg-dark">Properties: <span class="badge bg-success">{{ property_count }}</span></li>
                                <li class="list-group-item bg-dark">Alerts: <span class="badge bg-info">{{ alert_count }}</span></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Create the template file
with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
    f.write(index_html)

# Routes
@app.route('/')
def index():
    """Homepage with bot statistics"""
    # No need for app context here - we're already in a request
    user_count = User.query.count()
    property_count = PropertyListing.query.count()
    alert_count = PropertyAlert.query.count()
    
    return render_template('index.html', 
                          user_count=user_count,
                          property_count=property_count,
                          alert_count=alert_count)

@app.route('/status')
def status():
    """API status endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'Avier Homes Property Bot'
    })

# Initialize database tables
with app.app_context():
    logger.info("Creating database tables...")
    db.create_all()
    logger.info("Database tables created successfully")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)