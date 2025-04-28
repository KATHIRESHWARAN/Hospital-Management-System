import calendar
from datetime import datetime, timedelta
from collections import defaultdict
from models import Patient, Appointment, MedicalRecord, Staff, TriageAssessment

def get_patient_stats():
    """Get statistics about patients"""
    total_patients = Patient.query.count()
    new_patients_last_month = Patient.query.filter(
        Patient.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    return {
        'total': total_patients,
        'new_last_month': new_patients_last_month
    }

def get_appointment_stats():
    """Get statistics about appointments"""
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    appointments_today = Appointment.query.filter(
        Appointment.date == today
    ).count()
    
    appointments_tomorrow = Appointment.query.filter(
        Appointment.date == tomorrow
    ).count()
    
    appointments_next_week = Appointment.query.filter(
        Appointment.date > today,
        Appointment.date <= next_week
    ).count()
    
    return {
        'today': appointments_today,
        'tomorrow': appointments_tomorrow,
        'next_week': appointments_next_week
    }

def get_monthly_appointment_data():
    """Get monthly appointment data for the current year"""
    current_year = datetime.utcnow().year
    appointment_counts = defaultdict(int)
    
    # Get all appointments for the current year
    appointments = Appointment.query.filter(
        datetime.strptime(f"{current_year}-01-01", "%Y-%m-%d").date() <= Appointment.date,
        Appointment.date <= datetime.strptime(f"{current_year}-12-31", "%Y-%m-%d").date()
    ).all()
    
    # Count appointments by month
    for appointment in appointments:
        month = appointment.date.month
        appointment_counts[month] += 1
    
    # Format data for Chart.js
    months = [calendar.month_name[i] for i in range(1, 13)]
    counts = [appointment_counts[i] for i in range(1, 13)]
    
    return {
        'labels': months,
        'data': counts
    }

def get_record_type_distribution():
    """Get distribution of medical record types"""
    record_types = MedicalRecord.query.with_entities(
        MedicalRecord.record_type, 
        db.func.count(MedicalRecord.id)
    ).group_by(MedicalRecord.record_type).all()
    
    # Format data for Chart.js
    labels = [record[0] for record in record_types]
    data = [record[1] for record in record_types]
    
    return {
        'labels': labels,
        'data': data
    }

def get_staff_by_department():
    """Get staff distribution by department"""
    staff_by_dept = Staff.query.with_entities(
        Staff.department, 
        db.func.count(Staff.id)
    ).group_by(Staff.department).all()
    
    # Format data for Chart.js
    labels = [dept[0] for dept in staff_by_dept]
    data = [dept[1] for dept in staff_by_dept]
    
    return {
        'labels': labels,
        'data': data
    }

def get_triage_stats():
    """Get triage assessment statistics"""
    total_assessments = TriageAssessment.query.count()
    reviewed = TriageAssessment.query.filter_by(is_reviewed=True).count()
    pending = total_assessments - reviewed
    
    severity_counts = TriageAssessment.query.with_entities(
        TriageAssessment.severity, 
        db.func.count(TriageAssessment.id)
    ).group_by(TriageAssessment.severity).all()
    
    # Format severity data for Chart.js
    severity_labels = [s[0] for s in severity_counts if s[0] is not None]
    severity_data = [s[1] for s in severity_counts if s[0] is not None]
    
    return {
        'total': total_assessments,
        'reviewed': reviewed,
        'pending': pending,
        'severity_labels': severity_labels,
        'severity_data': severity_data
    }

def format_phone_number(phone):
    """Format phone number for display"""
    if not phone:
        return ""
    
    # Remove non-numeric characters
    nums = ''.join(c for c in phone if c.isdigit())
    
    # Format based on length
    if len(nums) == 10:
        return f"({nums[:3]}) {nums[3:6]}-{nums[6:]}"
    elif len(nums) == 11 and nums[0] == '1':
        return f"({nums[1:4]}) {nums[4:7]}-{nums[7:]}"
    else:
        return phone

def generate_search_query(model, search_term, filters=None):
    """
    Generate a search query for a given model and search term
    
    Args:
        model: SQLAlchemy model class
        search_term: The search term
        filters: Optional additional filters as a dict
        
    Returns:
        A SQLAlchemy query object
    """
    query = model.query
    
    # Apply search term if provided
    if search_term:
        if model == Patient:
            query = query.filter(
                db.or_(
                    Patient.first_name.ilike(f"%{search_term}%"),
                    Patient.last_name.ilike(f"%{search_term}%"),
                    Patient.email.ilike(f"%{search_term}%"),
                    Patient.phone.ilike(f"%{search_term}%")
                )
            )
        elif model == Staff:
            # Join with User model to search user fields
            query = query.join(Staff.user).filter(
                db.or_(
                    User.first_name.ilike(f"%{search_term}%"),
                    User.last_name.ilike(f"%{search_term}%"),
                    User.email.ilike(f"%{search_term}%"),
                    Staff.position.ilike(f"%{search_term}%"),
                    Staff.department.ilike(f"%{search_term}%")
                )
            )
        elif model == Appointment:
            # Join with Patient model to search patient name
            query = query.join(Appointment.patient).filter(
                db.or_(
                    Patient.first_name.ilike(f"%{search_term}%"),
                    Patient.last_name.ilike(f"%{search_term}%"),
                    Appointment.reason.ilike(f"%{search_term}%")
                )
            )
        elif model == MedicalRecord:
            # Join with Patient model to search patient name
            query = query.join(MedicalRecord.patient).filter(
                db.or_(
                    Patient.first_name.ilike(f"%{search_term}%"),
                    Patient.last_name.ilike(f"%{search_term}%"),
                    MedicalRecord.diagnosis.ilike(f"%{search_term}%"),
                    MedicalRecord.treatment.ilike(f"%{search_term}%")
                )
            )
    
    # Apply additional filters
    if filters:
        for key, value in filters.items():
            if value:  # Only apply non-empty filters
                if hasattr(model, key):
                    if key.startswith('date') and key.endswith('from'):
                        # Handle date range "from" filter
                        date_field = getattr(model, key.replace('_from', ''))
                        query = query.filter(date_field >= value)
                    elif key.startswith('date') and key.endswith('to'):
                        # Handle date range "to" filter
                        date_field = getattr(model, key.replace('_to', ''))
                        query = query.filter(date_field <= value)
                    else:
                        # Handle exact match filter
                        query = query.filter(getattr(model, key) == value)
    
    return query

# Import for get_staff_by_department function
from app import db
from models import User
