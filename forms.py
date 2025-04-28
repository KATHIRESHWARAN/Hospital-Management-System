from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TimeField, TextAreaField, EmailField, BooleanField, HiddenField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from models import User, Patient
from datetime import date
from flask_login import current_user

# Authentication forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

# Patient forms
class PatientForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    blood_type = SelectField('Blood Type', choices=[
        ('', 'Unknown'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), 
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')
    ])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    email = EmailField('Email', validators=[Optional(), Email()])
    address = StringField('Address', validators=[DataRequired(), Length(max=200)])
    emergency_contact = StringField('Emergency Contact', validators=[Length(max=100)])
    emergency_phone = StringField('Emergency Phone', validators=[Length(max=20)])
    insurance_provider = StringField('Insurance Provider', validators=[Length(max=100)])
    insurance_id = StringField('Insurance ID', validators=[Length(max=100)])
    submit = SubmitField('Save Patient')
    
    def validate_date_of_birth(self, field):
        if field.data > date.today():
            raise ValidationError('Date of birth cannot be in the future.')

class PatientSearchForm(FlaskForm):
    search_term = StringField('Search Patients', validators=[DataRequired()])
    submit = SubmitField('Search')

# Staff forms
class StaffForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Password', validators=[Optional(), Length(min=8)])
    
    # Enhanced fields for specialization and medical credentials
    specialization = StringField('Medical Specialization', validators=[Length(max=100)])
    position = StringField('Position/Title', validators=[DataRequired(), Length(max=100)])
    department = SelectField('Department', 
                           choices=[
                               ('', 'Select Department'),
                               ('Cardiology', 'Cardiology'),
                               ('Dermatology', 'Dermatology'),
                               ('Emergency Medicine', 'Emergency Medicine'),
                               ('Family Medicine', 'Family Medicine'),
                               ('Gastroenterology', 'Gastroenterology'),
                               ('General Surgery', 'General Surgery'),
                               ('Gynecology', 'Gynecology'),
                               ('Internal Medicine', 'Internal Medicine'),
                               ('Neurology', 'Neurology'),
                               ('Obstetrics', 'Obstetrics'),
                               ('Oncology', 'Oncology'),
                               ('Ophthalmology', 'Ophthalmology'),
                               ('Orthopedics', 'Orthopedics'),
                               ('Pediatrics', 'Pediatrics'),
                               ('Psychiatry', 'Psychiatry'),
                               ('Radiology', 'Radiology'),
                               ('Urology', 'Urology'),
                               ('Administration', 'Administration'),
                               ('Nursing', 'Nursing'),
                               ('Pharmacy', 'Pharmacy'),
                               ('Laboratory', 'Laboratory'),
                               ('Other', 'Other')
                           ], 
                           validators=[DataRequired()])
    medical_license = StringField('Medical License/ID', validators=[Optional(), Length(max=50)])
    years_experience = StringField('Years of Experience', validators=[Optional(), Length(max=3)])
    board_certified = BooleanField('Board Certified', default=False)
    availability = SelectField('Availability', 
                             choices=[
                                 ('Full-time', 'Full-time'),
                                 ('Part-time', 'Part-time'),
                                 ('On-call', 'On-call'),
                                 ('Visiting', 'Visiting')
                             ],
                             default='Full-time')
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    role = SelectField('System Role', choices=[], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Staff')
    
    def validate_username(self, username):
        # Only check for username uniqueness if this is a new user or username changed
        if hasattr(self, 'user_id') and self.user_id.data:
            user = User.query.filter_by(username=username.data).filter(User.id != int(self.user_id.data)).first()
        else:
            user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        # Only check for email uniqueness if this is a new user or email changed
        if hasattr(self, 'user_id') and self.user_id.data:
            user = User.query.filter_by(email=email.data).filter(User.id != int(self.user_id.data)).first()
        else:
            user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class StaffSearchForm(FlaskForm):
    search_term = StringField('Search Staff', validators=[DataRequired()])
    submit = SubmitField('Search')

# Appointment forms
class AppointmentForm(FlaskForm):
    patient_id = SelectField('Patient', validators=[DataRequired()], coerce=int)
    staff_id = SelectField('Doctor/Staff', validators=[DataRequired()], coerce=int)
    date = DateField('Date', validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    reason = StringField('Reason for Visit', validators=[DataRequired(), Length(max=200)])
    notes = TextAreaField('Notes')
    status = SelectField('Status', choices=[
        ('Scheduled', 'Scheduled'), 
        ('Completed', 'Completed'), 
        ('Cancelled', 'Cancelled')
    ], default='Scheduled')
    submit = SubmitField('Save Appointment')
    
    def validate_date(self, field):
        if field.data < date.today():
            raise ValidationError('Appointment date cannot be in the past.')
    
    def validate_end_time(self, field):
        if self.start_time.data and field.data <= self.start_time.data:
            raise ValidationError('End time must be after start time.')

class AppointmentSearchForm(FlaskForm):
    search_term = StringField('Search Appointments', validators=[Optional()])
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('', 'All'), 
        ('Scheduled', 'Scheduled'), 
        ('Completed', 'Completed'), 
        ('Cancelled', 'Cancelled')
    ], validators=[Optional()])
    submit = SubmitField('Search')

# Medical Record forms
class MedicalRecordForm(FlaskForm):
    patient_id = SelectField('Patient', validators=[DataRequired()], coerce=int)
    staff_id = SelectField('Doctor/Staff', validators=[DataRequired()], coerce=int)
    date = DateField('Date', validators=[DataRequired()], default=date.today)
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    treatment = TextAreaField('Treatment', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    prescriptions = TextAreaField('Prescriptions')
    follow_up = DateField('Follow-up Date', validators=[Optional()])
    record_type = SelectField('Record Type', choices=[
        ('Consultation', 'Consultation'), 
        ('Surgery', 'Surgery'), 
        ('Checkup', 'Regular Checkup'),
        ('Emergency', 'Emergency'),
        ('Laboratory', 'Laboratory'),
        ('Imaging', 'Imaging'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Record')

class MedicalRecordSearchForm(FlaskForm):
    search_term = StringField('Search Medical Records', validators=[Optional()])
    record_type = SelectField('Record Type', choices=[
        ('', 'All'), 
        ('Consultation', 'Consultation'), 
        ('Surgery', 'Surgery'), 
        ('Checkup', 'Regular Checkup'),
        ('Emergency', 'Emergency'),
        ('Laboratory', 'Laboratory'),
        ('Imaging', 'Imaging'),
        ('Other', 'Other')
    ], validators=[Optional()])
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    submit = SubmitField('Search')

# Triage form
class TriageForm(FlaskForm):
    patient_id = SelectField('Patient', validators=[DataRequired()], coerce=int)
    symptoms = TextAreaField('Symptoms', validators=[DataRequired()])
    submit = SubmitField('Perform AI Assessment')

class TriageReviewForm(FlaskForm):
    triage_id = HiddenField('Triage ID', validators=[DataRequired()])
    severity = SelectField('Severity', choices=[
        ('Low', 'Low'), 
        ('Medium', 'Medium'), 
        ('High', 'High'), 
        ('Critical', 'Critical')
    ], validators=[DataRequired()])
    recommendation = TextAreaField('Medical Recommendation', validators=[DataRequired()])
    is_reviewed = BooleanField('Mark as Reviewed')
    submit = SubmitField('Save Review')

class DepartmentForm(FlaskForm):
    name = StringField('Department Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    head_doctor_id = SelectField('Head Doctor', coerce=int, validators=[Optional()])
    location = StringField('Location', validators=[Length(max=100)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    email = EmailField('Email', validators=[Optional(), Email()])
    budget = FloatField('Annual Budget', validators=[Optional()])
    capacity = IntegerField('Capacity (Beds)', validators=[Optional()])
    is_active = BooleanField('Active Department', default=True)
    submit = SubmitField('Save Department')

class DepartmentSearchForm(FlaskForm):
    search_term = StringField('Search Departments', validators=[Optional()])
    submit = SubmitField('Search')

# User Profile and Settings Forms
class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')
    
    def validate_current_password(self, field):
        # Password verification will be done in the route

        pass  # Validation is handled in the route function

class ProfileUpdateForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Save Changes')
    
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')
