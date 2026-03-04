from database import db
from flask_login import UserMixin
from datetime import datetime


# User Model: Represents user information
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    # Relationship to detection records
    detection_records = db.relationship('DetectionRecord', backref='user', lazy=True)


# EmailCaptchaModel Model: Represents email captcha information
class EmailCaptchaModel(db.Model):
    __tablename__ = "email_captcha"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), nullable=False)
    captcha = db.Column(db.String(100), nullable=False)


# DetectionRecord Model: Tracks water body detection history
class DetectionRecord(db.Model):
    __tablename__ = "detection_records"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Allow anonymous detections

    # Record type (single or comparison)
    record_type = db.Column(db.String(20), nullable=False)

    # Processing parameters
    process_type = db.Column(db.String(20), nullable=False)  # unet, grayscale, edge_detection
    levels = db.Column(db.Integer, nullable=False)
    spatial_resolution = db.Column(db.Float, nullable=False)
    water_threshold = db.Column(db.Integer, nullable=False)

    # File information - Single image analysis
    original_filename = db.Column(db.String(255), nullable=True)
    original_path = db.Column(db.String(255), nullable=True)
    processed_path = db.Column(db.String(255), nullable=True)
    discretized_path = db.Column(db.String(255), nullable=True)
    water_land_path = db.Column(db.String(255), nullable=True)

    # File information - Comparison analysis
    before_filename = db.Column(db.String(255), nullable=True)
    before_path = db.Column(db.String(255), nullable=True)
    before_processed_path = db.Column(db.String(255), nullable=True)
    before_discretized_path = db.Column(db.String(255), nullable=True)
    before_water_land_path = db.Column(db.String(255), nullable=True)

    after_filename = db.Column(db.String(255), nullable=True)
    after_path = db.Column(db.String(255), nullable=True)
    after_processed_path = db.Column(db.String(255), nullable=True)
    after_discretized_path = db.Column(db.String(255), nullable=True)
    after_water_land_path = db.Column(db.String(255), nullable=True)

    # Statistics - Single analysis
    water_pixels = db.Column(db.Integer, nullable=True)
    land_pixels = db.Column(db.Integer, nullable=True)
    water_percentage = db.Column(db.Float, nullable=True)
    land_percentage = db.Column(db.Float, nullable=True)
    water_area = db.Column(db.Float, nullable=True)
    land_area = db.Column(db.Float, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<DetectionRecord {self.id}>'