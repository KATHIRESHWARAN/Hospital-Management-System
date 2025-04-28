from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Role-based access control
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Staff model - extends user with medical staff information
class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    specialization = db.Column(db.String(100))
    position = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    user = db.relationship('User', backref=db.backref('staff_profile', uselist=False))
    appointments = db.relationship('Appointment', backref='staff', lazy='dynamic')
    
    def __repr__(self):
        return f'<Staff {self.user.first_name} {self.user.last_name}>'

# Patient model
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    blood_type = db.Column(db.String(10))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.String(200), nullable=False)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    insurance_provider = db.Column(db.String(100))
    insurance_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    records = db.relationship('MedicalRecord', backref='patient', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic')
    
    def __repr__(self):
        return f'<Patient {self.first_name} {self.last_name}>'
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def age(self):
        today = datetime.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

# Medical Record model
class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    prescriptions = db.Column(db.Text)
    follow_up = db.Column(db.Date)
    record_type = db.Column(db.String(50), nullable=False)  # e.g., 'Consultation', 'Surgery', 'Checkup'
    staff = db.relationship('Staff', backref='records')
    
    def __repr__(self):
        return f'<MedicalRecord {self.id} for Patient {self.patient_id}>'

# Appointment model
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='Scheduled')  # 'Scheduled', 'Completed', 'Cancelled'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Appointment {self.id} for Patient {self.patient_id} with Staff {self.staff_id}>'

# Triage Assessment model for the AI triage tool
class TriageAssessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20))  # 'Low', 'Medium', 'High', 'Critical'
    recommendation = db.Column(db.Text)
    ai_confidence = db.Column(db.Float)  # Confidence score from the AI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by_staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    is_reviewed = db.Column(db.Boolean, default=False)
    
    patient = db.relationship('Patient', backref='triage_assessments')
    reviewed_by_staff = db.relationship('Staff', foreign_keys=[reviewed_by_staff_id], backref='reviewed_assessments')
    
    def __repr__(self):
        return f'<TriageAssessment {self.id} for Patient {self.patient_id}>'
