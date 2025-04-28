import os
from flask import render_template, flash, redirect, url_for, request, jsonify, abort
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy import or_
from werkzeug.security import generate_password_hash
from datetime import datetime, date

from app import app, db
from models import User, Role, Patient, Staff, MedicalRecord, Appointment, TriageAssessment, Department
from forms import (LoginForm, RegistrationForm, PatientForm, PatientSearchForm, 
                  StaffForm, StaffSearchForm, AppointmentForm, AppointmentSearchForm,
                  MedicalRecordForm, MedicalRecordSearchForm, TriageForm, TriageReviewForm,
                  DepartmentForm, DepartmentSearchForm, PasswordChangeForm, ProfileUpdateForm)
from utils import (get_patient_stats, get_appointment_stats, get_monthly_appointment_data,
                  get_record_type_distribution, get_staff_by_department, get_triage_stats, 
                  get_department_stats,
                  format_phone_number, generate_search_query)
from ai_services import assess_patient_symptoms

# Initialize roles and default users
def initialize_roles():
    roles = ['Admin', 'Doctor', 'Nurse', 'Receptionist']
    for role_name in roles:
        if not Role.query.filter_by(name=role_name).first():
            role = Role(name=role_name, description=f'{role_name} role')
            db.session.add(role)
    
    # Create admin user if no users exist
    if User.query.count() == 0:
        admin_role = Role.query.filter_by(name='Admin').first()
        admin_user = User(
            username='admin',
            email='admin@hospital.com',
            first_name='Admin',
            last_name='User',
            role=admin_role
        )
        admin_user.set_password('adminpassword')
        db.session.add(admin_user)
        
        # Also create a doctor user for convenience
        doctor_role = Role.query.filter_by(name='Doctor').first()
        doctor_user = User(
            username='doctor',
            email='doctor@hospital.com',
            first_name='John',
            last_name='Smith',
            role=doctor_role
        )
        doctor_user.set_password('doctorpassword')
        db.session.add(doctor_user)
        db.session.flush()  # Get user ID before creating staff profile
        
        # Create a staff profile for the doctor
        doctor_staff = Staff(
            user_id=doctor_user.id,
            specialization='Cardiology',
            position='Senior Physician',
            department='Cardiology',
            phone='555-123-4567',
            medical_license='MED-12345',
            years_experience='15',
            board_certified=True,
            availability='Full-time'
        )
        db.session.add(doctor_staff)
    
    db.session.commit()

# Initialize roles when the application starts
with app.app_context():
    initialize_roles()

# Authentication routes
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        flash('You have been logged in successfully!', 'success')
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard')
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Assign role (default to Receptionist for self-registration)
        role = Role.query.filter_by(name='Receptionist').first()
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=role
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    patient_stats = get_patient_stats()
    appointment_stats = get_appointment_stats()
    
    # Get recent patients
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    
    # Get today's appointments
    today = date.today()
    todays_appointments = Appointment.query.filter_by(date=today).all()
    
    # Get pending triage assessments
    pending_triage = TriageAssessment.query.filter_by(is_reviewed=False).order_by(TriageAssessment.created_at.desc()).limit(5).all()
    
    return render_template(
        'dashboard.html', 
        title='Dashboard',
        patient_stats=patient_stats,
        appointment_stats=appointment_stats,
        recent_patients=recent_patients,
        todays_appointments=todays_appointments,
        pending_triage=pending_triage
    )

# Patient routes
@app.route('/patients')
@login_required
def patients():
    search_form = PatientSearchForm(request.args)
    search_term = request.args.get('search_term', '')
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = generate_search_query(Patient, search_term)
    patients_pagination = query.order_by(Patient.last_name).paginate(page=page, per_page=per_page)
    
    return render_template(
        'patients/index.html',
        title='Patients',
        patients=patients_pagination.items,
        pagination=patients_pagination,
        search_form=search_form,
        search_term=search_term
    )

@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    form = PatientForm()
    if form.validate_on_submit():
        patient = Patient(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            blood_type=form.blood_type.data or None,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            emergency_contact=form.emergency_contact.data,
            emergency_phone=form.emergency_phone.data,
            insurance_provider=form.insurance_provider.data,
            insurance_id=form.insurance_id.data
        )
        db.session.add(patient)
        db.session.commit()
        
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients'))
    
    return render_template('patients/add.html', title='Add Patient', form=form)

@app.route('/patients/<int:id>')
@login_required
def view_patient(id):
    patient = Patient.query.get_or_404(id)
    
    # Get patient's medical records
    records = MedicalRecord.query.filter_by(patient_id=id).order_by(MedicalRecord.date.desc()).all()
    
    # Get patient's appointments
    appointments = Appointment.query.filter_by(patient_id=id).order_by(Appointment.date.desc(), Appointment.start_time.desc()).all()
    
    # Get patient's triage assessments
    triage_assessments = TriageAssessment.query.filter_by(patient_id=id).order_by(TriageAssessment.created_at.desc()).all()
    
    return render_template(
        'patients/view.html',
        title=f'Patient: {patient.first_name} {patient.last_name}',
        patient=patient,
        records=records,
        appointments=appointments,
        triage_assessments=triage_assessments,
        format_phone=format_phone_number
    )

@app.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    form = PatientForm(obj=patient)
    
    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        
        flash('Patient information updated!', 'success')
        return redirect(url_for('view_patient', id=patient.id))
    
    return render_template('patients/edit.html', title=f'Edit Patient: {patient.first_name} {patient.last_name}', form=form, patient=patient)

# Staff routes
@app.route('/staff')
@login_required
def staff():
    search_form = StaffSearchForm(request.args)
    search_term = request.args.get('search_term', '')
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = Staff.query
    if search_term:
        query = query.join(Staff.user).filter(
            or_(
                User.first_name.ilike(f'%{search_term}%'),
                User.last_name.ilike(f'%{search_term}%'),
                User.email.ilike(f'%{search_term}%'),
                Staff.position.ilike(f'%{search_term}%'),
                Staff.department.ilike(f'%{search_term}%')
            )
        )
    
    staff_pagination = query.order_by(Staff.id).paginate(page=page, per_page=per_page)
    
    return render_template(
        'staff/index.html',
        title='Staff Directory',
        staff=staff_pagination.items,
        pagination=staff_pagination,
        search_form=search_form,
        search_term=search_term
    )

@app.route('/staff/add', methods=['GET', 'POST'])
@login_required
def add_staff():
    # Allow all users to add staff in the testing environment
    # In production, you might want to restrict this to admins only
    # if current_user.role.name != 'Admin':
    #     flash('You do not have permission to add staff members.', 'danger')
    #     return redirect(url_for('staff'))
    
    form = StaffForm()
    form.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
    
    if form.validate_on_submit():
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role_id=form.role.data
        )
        
        # Set password
        if form.password.data:
            user.set_password(form.password.data)
        else:
            # Generate a default password using first initial + last name + 123
            default_password = (form.first_name.data[0] + form.last_name.data + "123").lower()
            user.set_password(default_password)
        
        db.session.add(user)
        db.session.flush()  # Get user ID before committing
        
        # Create staff profile with enhanced medical credentials
        staff = Staff(
            user_id=user.id,
            specialization=form.specialization.data,
            position=form.position.data,
            department=form.department.data,
            phone=form.phone.data,
            medical_license=form.medical_license.data,
            years_experience=form.years_experience.data,
            board_certified=form.board_certified.data,
            availability=form.availability.data
        )
        
        db.session.add(staff)
        db.session.commit()
        
        flash('Medical staff member added successfully!', 'success')
        return redirect(url_for('staff'))
    
    return render_template('staff/add.html', title='Add Medical Staff', form=form)

@app.route('/staff/<int:id>')
@login_required
def view_staff(id):
    staff = Staff.query.get_or_404(id)
    
    # Get staff's appointments
    appointments = Appointment.query.filter_by(staff_id=id).order_by(Appointment.date.desc(), Appointment.start_time.desc()).all()
    
    # Get staff's medical records
    records = MedicalRecord.query.filter_by(staff_id=id).order_by(MedicalRecord.date.desc()).all()
    
    return render_template(
        'staff/view.html',
        title=f'Staff: {staff.user.first_name} {staff.user.last_name}',
        staff=staff,
        appointments=appointments,
        records=records,
        format_phone=format_phone_number
    )

@app.route('/staff/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_staff(id):
    staff = Staff.query.get_or_404(id)
    form = StaffForm(obj=staff)
    
    # Pre-populate with user data
    if request.method == 'GET':
        form.username.data = staff.user.username
        form.email.data = staff.user.email
        form.first_name.data = staff.user.first_name
        form.last_name.data = staff.user.last_name
        form.role.data = staff.user.role_id
    
    # Set role choices
    form.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
    
    if form.validate_on_submit():
        # Update user information
        staff.user.username = form.username.data
        staff.user.email = form.email.data
        staff.user.first_name = form.first_name.data
        staff.user.last_name = form.last_name.data
        staff.user.role_id = form.role.data
        
        # Update password if provided
        if form.password.data:
            staff.user.set_password(form.password.data)
        
        # Update staff profile
        staff.specialization = form.specialization.data
        staff.position = form.position.data
        staff.department = form.department.data
        staff.phone = form.phone.data
        staff.medical_license = form.medical_license.data
        staff.years_experience = form.years_experience.data
        staff.board_certified = form.board_certified.data
        staff.availability = form.availability.data
        
        db.session.commit()
        
        flash('Staff information updated successfully!', 'success')
        return redirect(url_for('view_staff', id=staff.id))
    
    return render_template('staff/edit.html', title='Edit Staff', form=form, staff=staff)

# Appointment routes
@app.route('/appointments')
@login_required
def appointments():
    search_form = AppointmentSearchForm(request.args)
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get search parameters
    search_term = request.args.get('search_term', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    status = request.args.get('status', '')
    
    # Convert string dates to date objects
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            date_from = None
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            date_to = None
    
    # Build query
    query = Appointment.query
    
    if search_term:
        query = query.join(Appointment.patient).filter(
            or_(
                Patient.first_name.ilike(f'%{search_term}%'),
                Patient.last_name.ilike(f'%{search_term}%'),
                Appointment.reason.ilike(f'%{search_term}%')
            )
        )
    
    if date_from:
        query = query.filter(Appointment.date >= date_from)
    
    if date_to:
        query = query.filter(Appointment.date <= date_to)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    # Order by date and time
    query = query.order_by(Appointment.date.desc(), Appointment.start_time.desc())
    
    # Paginate results
    appointments_pagination = query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'appointments/index.html',
        title='Appointments',
        appointments=appointments_pagination.items,
        pagination=appointments_pagination,
        search_form=search_form,
        search_term=search_term,
        date_from=date_from,
        date_to=date_to,
        status=status
    )

@app.route('/appointments/book', methods=['GET', 'POST'])
@login_required
def book_appointment():
    form = AppointmentForm()
    
    # Populate patient and staff choices
    form.patient_id.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in Patient.query.order_by(Patient.last_name).all()]
    
    # Only get doctors and nurses for staff choices
    staff_members = Staff.query.join(Staff.user).join(User.role).filter(
        Role.name.in_(['Doctor', 'Nurse'])
    ).all()
    form.staff_id.choices = [(s.id, f"Dr. {s.user.first_name} {s.user.last_name} ({s.position}, {s.department})") for s in staff_members]
    
    # Pre-select patient if provided in URL
    patient_id = request.args.get('patient_id')
    if patient_id and request.method == 'GET':
        form.patient_id.data = int(patient_id)
    
    if form.validate_on_submit():
        appointment = Appointment(
            patient_id=form.patient_id.data,
            staff_id=form.staff_id.data,
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            reason=form.reason.data,
            notes=form.notes.data,
            status=form.status.data
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('appointments'))
    
    return render_template('appointments/book.html', title='Book Appointment', form=form)

@app.route('/appointments/<int:id>')
@login_required
def view_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    
    return render_template(
        'appointments/view.html',
        title=f'Appointment: {appointment.patient.first_name} {appointment.patient.last_name}',
        appointment=appointment
    )

@app.route('/appointments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    form = AppointmentForm(obj=appointment)
    
    # Populate patient and staff choices
    form.patient_id.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in Patient.query.order_by(Patient.last_name).all()]
    
    staff_members = Staff.query.join(Staff.user).join(User.role).filter(
        Role.name.in_(['Doctor', 'Nurse'])
    ).all()
    form.staff_id.choices = [(s.id, f"Dr. {s.user.first_name} {s.user.last_name} ({s.position}, {s.department})") for s in staff_members]
    
    if form.validate_on_submit():
        form.populate_obj(appointment)
        db.session.commit()
        
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('view_appointment', id=appointment.id))
    
    return render_template('appointments/book.html', title='Edit Appointment', form=form, appointment=appointment)

# Medical Record routes
@app.route('/records')
@login_required
def records():
    search_form = MedicalRecordSearchForm(request.args)
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get search parameters
    search_term = request.args.get('search_term', '')
    record_type = request.args.get('record_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Convert string dates to date objects
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            date_from = None
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            date_to = None
    
    # Build query
    query = MedicalRecord.query
    
    if search_term:
        query = query.join(MedicalRecord.patient).filter(
            or_(
                Patient.first_name.ilike(f'%{search_term}%'),
                Patient.last_name.ilike(f'%{search_term}%'),
                MedicalRecord.diagnosis.ilike(f'%{search_term}%'),
                MedicalRecord.treatment.ilike(f'%{search_term}%')
            )
        )
    
    if record_type:
        query = query.filter(MedicalRecord.record_type == record_type)
    
    if date_from:
        query = query.filter(MedicalRecord.date >= date_from)
    
    if date_to:
        query = query.filter(MedicalRecord.date <= date_to)
    
    # Order by date
    query = query.order_by(MedicalRecord.date.desc())
    
    # Paginate results
    records_pagination = query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'records/index.html',
        title='Medical Records',
        records=records_pagination.items,
        pagination=records_pagination,
        search_form=search_form,
        search_term=search_term,
        record_type=record_type,
        date_from=date_from,
        date_to=date_to
    )

@app.route('/records/add', methods=['GET', 'POST'])
@login_required
def add_record():
    # Allow all users to add records in the testing environment
    # In production, you might want to restrict this to medical staff only
    # if current_user.role.name not in ['Doctor', 'Nurse', 'Admin']:
    #     flash('You do not have permission to add medical records.', 'danger')
    #     return redirect(url_for('records'))
    
    form = MedicalRecordForm()
    
    # Populate patient and staff choices
    form.patient_id.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in Patient.query.order_by(Patient.last_name).all()]
    form.staff_id.choices = [(s.id, f"{s.user.first_name} {s.user.last_name} ({s.position})") for s in Staff.query.all()]
    
    # Pre-select patient if provided in URL
    patient_id = request.args.get('patient_id')
    if patient_id and request.method == 'GET':
        form.patient_id.data = int(patient_id)
    
    # If current user is medical staff, pre-select them
    if current_user.role.name in ['Doctor', 'Nurse'] and hasattr(current_user, 'staff_profile'):
        if request.method == 'GET':
            form.staff_id.data = current_user.staff_profile.id
    
    if form.validate_on_submit():
        record = MedicalRecord(
            patient_id=form.patient_id.data,
            staff_id=form.staff_id.data,
            date=form.date.data,
            diagnosis=form.diagnosis.data,
            treatment=form.treatment.data,
            notes=form.notes.data,
            prescriptions=form.prescriptions.data,
            follow_up=form.follow_up.data,
            record_type=form.record_type.data
        )
        
        db.session.add(record)
        db.session.commit()
        
        flash('Medical record added successfully!', 'success')
        return redirect(url_for('records'))
    
    return render_template('records/add.html', title='Add Medical Record', form=form)

@app.route('/records/<int:id>')
@login_required
def view_record(id):
    record = MedicalRecord.query.get_or_404(id)
    
    return render_template(
        'records/view.html',
        title=f'Medical Record: {record.patient.first_name} {record.patient.last_name}',
        record=record
    )

# Triage routes
@app.route('/triage')
@login_required
def triage():
    # Allow all users to access triage in the testing environment
    # In production, you might want to restrict this to medical staff only
    # if current_user.role.name not in ['Doctor', 'Nurse', 'Admin']:
    #     flash('You do not have permission to access the triage tool.', 'danger')
    #     return redirect(url_for('dashboard'))
    
    form = TriageForm()
    
    # Populate patient choices
    form.patient_id.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in Patient.query.order_by(Patient.last_name).all()]
    
    # Get unreviewed triage assessments
    unreviewed = TriageAssessment.query.filter_by(is_reviewed=False).order_by(TriageAssessment.created_at.desc()).all()
    
    # Get recently reviewed triage assessments
    reviewed = TriageAssessment.query.filter_by(is_reviewed=True).order_by(TriageAssessment.created_at.desc()).limit(5).all()
    
    return render_template(
        'triage/index.html',
        title='AI Triage Tool',
        form=form,
        unreviewed=unreviewed,
        reviewed=reviewed
    )

@app.route('/triage/assess', methods=['POST'])
@login_required
def assess_triage():
    # Allow all users to access triage assessment in the testing environment
    # In production, you might want to restrict this to medical staff only
    # if current_user.role.name not in ['Doctor', 'Nurse', 'Admin']:
    #     flash('You do not have permission to use the triage tool.', 'danger')
    #     return redirect(url_for('dashboard'))
    
    form = TriageForm()
    
    # Populate patient choices
    form.patient_id.choices = [(p.id, f"{p.first_name} {p.last_name}") for p in Patient.query.order_by(Patient.last_name).all()]
    
    if form.validate_on_submit():
        patient_id = form.patient_id.data
        symptoms = form.symptoms.data
        
        # Assess symptoms with AI
        assessment = assess_patient_symptoms(symptoms)
        
        # Create triage assessment
        triage = TriageAssessment(
            patient_id=patient_id,
            symptoms=symptoms,
            severity=assessment['severity'],
            recommendation=assessment['recommendation'],
            ai_confidence=assessment['confidence']
        )
        
        db.session.add(triage)
        db.session.commit()
        
        flash(f'Triage assessment complete. AI suggests {assessment["severity"]} severity.', 'success')
        return redirect(url_for('triage'))
    
    flash('There was an error processing the triage request.', 'danger')
    return redirect(url_for('triage'))

@app.route('/triage/<int:id>/review', methods=['GET', 'POST'])
@login_required
def review_triage(id):
    # Allow all users to review triage assessments in the testing environment
    # In production, you might want to restrict this to medical staff only
    # if current_user.role.name not in ['Doctor', 'Nurse', 'Admin']:
    #     flash('You do not have permission to review triage assessments.', 'danger')
    #     return redirect(url_for('dashboard'))
    
    assessment = TriageAssessment.query.get_or_404(id)
    
    # Skip staff profile check in testing environment
    # In production, you might want to uncomment this check
    # if not hasattr(current_user, 'staff_profile'):
    #     flash('Only staff members can review triage assessments.', 'danger')
    #     return redirect(url_for('triage'))
    
    form = TriageReviewForm(obj=assessment)
    
    if form.validate_on_submit():
        assessment.severity = form.severity.data
        assessment.recommendation = form.recommendation.data
        assessment.is_reviewed = form.is_reviewed.data
        
        # Check if user has a staff profile
        if hasattr(current_user, 'staff_profile'):
            assessment.reviewed_by_staff_id = current_user.staff_profile.id
        else:
            # For testing, use a default staff ID if available
            default_staff = Staff.query.first()
            if default_staff:
                assessment.reviewed_by_staff_id = default_staff.id
        
        db.session.commit()
        
        flash('Triage assessment has been reviewed.', 'success')
        return redirect(url_for('triage'))
    
    return render_template(
        'triage/review.html',
        title='Review Triage Assessment',
        assessment=assessment,
        form=form
    )

# Analytics route
@app.route('/analytics')
@login_required
def analytics():
    # Allow all users to view analytics in the testing environment
    # In production, you might want to restrict this to admins only
    # if current_user.role.name != 'Admin':
    #     flash('You do not have permission to view analytics.', 'danger')
    #     return redirect(url_for('dashboard'))
    
    # Get statistics
    patient_stats = get_patient_stats()
    appointment_stats = get_appointment_stats()
    monthly_appointments = get_monthly_appointment_data()
    record_types = get_record_type_distribution()
    staff_by_dept = get_staff_by_department()
    triage_stats = get_triage_stats()
    department_stats = get_department_stats()
    
    return render_template(
        'analytics/index.html',
        title='Analytics Dashboard',
        patient_stats=patient_stats,
        appointment_stats=appointment_stats,
        monthly_appointments=monthly_appointments,
        record_types=record_types,
        staff_by_dept=staff_by_dept,
        triage_stats=triage_stats,
        department_stats=department_stats
    )

# API routes for charts
@app.route('/api/chart/appointments')
@login_required
def api_appointments_chart():
    data = get_monthly_appointment_data()
    return jsonify(data)

@app.route('/api/chart/record-types')
@login_required
def api_record_types_chart():
    data = get_record_type_distribution()
    return jsonify(data)

@app.route('/api/chart/staff-departments')
@login_required
def api_staff_departments_chart():
    data = get_staff_by_department()
    return jsonify(data)

@app.route('/api/chart/triage-severity')
@login_required
def api_triage_severity_chart():
    data = get_triage_stats()
    return jsonify({
        'labels': data['severity_labels'],
        'data': data['severity_data']
    })

# Department routes
@app.route('/departments')
@login_required
def departments():
    search_form = DepartmentSearchForm(request.args)
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get search parameters
    search_term = request.args.get('search_term', '')
    
    # Build query
    query = Department.query
    
    if search_term:
        query = query.filter(Department.name.ilike(f'%{search_term}%') | 
                            Department.description.ilike(f'%{search_term}%') |
                            Department.location.ilike(f'%{search_term}%'))
    
    # Order by name
    query = query.order_by(Department.name)
    
    # Paginate results
    departments_pagination = query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'departments/index.html',
        title='Departments',
        departments=departments_pagination.items,
        pagination=departments_pagination,
        search_form=search_form,
        search_term=search_term
    )

@app.route('/departments/add', methods=['GET', 'POST'])
@login_required
def add_department():
    # In a production environment, you might want to restrict this to admin users
    # if current_user.role.name != 'Admin':
    #     flash('You do not have permission to add departments.', 'danger')
    #     return redirect(url_for('departments'))
    
    form = DepartmentForm()
    
    # Get all doctors for the head doctor selection
    doctors = Staff.query.join(Staff.user).join(User.role).filter(
        Role.name == 'Doctor'
    ).all()
    
    form.head_doctor_id.choices = [(0, 'Select Head Doctor')] + [(d.id, f"Dr. {d.user.first_name} {d.user.last_name}") for d in doctors]
    
    if form.validate_on_submit():
        # Handle the case where no head doctor is selected
        head_doctor_id = form.head_doctor_id.data if form.head_doctor_id.data != 0 else None
        
        department = Department(
            name=form.name.data,
            description=form.description.data,
            head_doctor_id=head_doctor_id,
            location=form.location.data,
            phone=form.phone.data,
            email=form.email.data,
            budget=form.budget.data,
            capacity=form.capacity.data,
            is_active=form.is_active.data
        )
        
        db.session.add(department)
        db.session.commit()
        
        flash('Department added successfully!', 'success')
        return redirect(url_for('departments'))
    
    return render_template('departments/add.html', title='Add Department', form=form)

@app.route('/departments/<int:id>')
@login_required
def view_department(id):
    department = Department.query.get_or_404(id)
    
    # Get staff members in this department
    staff_members = Staff.query.filter(Staff.department == department.name).all()
    
    # Get some statistics
    stats = {
        'staff_count': len(staff_members),
        'doctors_count': sum(1 for s in staff_members if s.user.role.name == 'Doctor'),
        'nurses_count': sum(1 for s in staff_members if s.user.role.name == 'Nurse'),
        'utilization': 0  # Will be calculated if capacity is available
    }
    
    # Calculate bed utilization if capacity is set
    if department.capacity:
        # This is simplified - in a real application, you would track actual bed usage
        # Here we'll use a random number between 30% and 90% for demonstration
        import random
        stats['utilization'] = round((random.randint(30, 90) / 100) * department.capacity)
        
    return render_template(
        'departments/view.html',
        title=f'Department: {department.name}',
        department=department,
        staff_members=staff_members,
        stats=stats
    )

@app.route('/departments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_department(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)
    
    # Get all doctors for the head doctor selection
    doctors = Staff.query.join(Staff.user).join(User.role).filter(
        Role.name == 'Doctor'
    ).all()
    
    form.head_doctor_id.choices = [(0, 'Select Head Doctor')] + [(d.id, f"Dr. {d.user.first_name} {d.user.last_name}") for d in doctors]
    
    # Set current head doctor if exists
    if request.method == 'GET' and department.head_doctor_id is None:
        form.head_doctor_id.data = 0
    
    if form.validate_on_submit():
        # Handle the case where no head doctor is selected
        head_doctor_id = form.head_doctor_id.data if form.head_doctor_id.data != 0 else None
        
        department.name = form.name.data
        department.description = form.description.data
        department.head_doctor_id = head_doctor_id
        department.location = form.location.data
        department.phone = form.phone.data
        department.email = form.email.data
        department.budget = form.budget.data
        department.capacity = form.capacity.data
        department.is_active = form.is_active.data
        
        db.session.commit()
        
        flash('Department updated successfully!', 'success')
        return redirect(url_for('view_department', id=department.id))
    
    return render_template('departments/edit.html', title='Edit Department', form=form, department=department)

# Add department statistics to API
@app.route('/api/chart/departments-stats')
@login_required
def api_department_stats():
    departments = Department.query.all()
    
    # Get department names and staff counts
    dep_names = []
    staff_counts = []
    capacities = []
    
    for dept in departments:
        dep_names.append(dept.name)
        staff_counts.append(dept.staff_count())
        capacities.append(dept.capacity or 0)
    
    return jsonify({
        'labels': dep_names,
        'datasets': [
            {
                'label': 'Staff Count',
                'data': staff_counts,
                'backgroundColor': 'rgba(23, 162, 184, 0.7)',
                'borderColor': 'rgba(23, 162, 184, 1)',
                'borderWidth': 1
            },
            {
                'label': 'Capacity (Beds)',
                'data': capacities,
                'backgroundColor': 'rgba(111, 66, 193, 0.7)',
                'borderColor': 'rgba(111, 66, 193, 1)',
                'borderWidth': 1
            }
        ]
    })

# User Profile and Settings Routes
@app.route('/profile')
@login_required
def profile():
    # Import the Appointment model here to avoid circular imports
    from models import Appointment
    
    return render_template(
        'profile.html', 
        title='User Profile',
        Appointment=Appointment
    )

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    profile_form = ProfileUpdateForm(obj=current_user)
    password_form = PasswordChangeForm()
    
    return render_template(
        'settings.html', 
        title='User Settings',
        profile_form=profile_form,
        password_form=password_form
    )

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated successfully!', 'success')
        else:
            flash('Current password is incorrect', 'danger')
    
    return redirect(url_for('settings'))

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    form = ProfileUpdateForm()
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        
        # Update staff profile if exists
        if current_user.staff_profile and form.phone.data:
            current_user.staff_profile.phone = form.phone.data
            
        db.session.commit()
        flash('Your profile has been updated successfully!', 'success')
    
    return redirect(url_for('profile'))
