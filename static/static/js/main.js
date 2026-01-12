// Main JavaScript functionality for Hospital Management System
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize date pickers
    initializeDatePickers();
    
    // Search form functionality
    initializeSearchForms();
    
    // Toggle sidebar on mobile
    initializeSidebarToggle();
    
    // Initialize appointment time validation
    initializeAppointmentTimeValidation();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// Initialize date picker inputs
function initializeDatePickers() {
    // Modern browsers use the native date picker for inputs with type="date"
    // This function is kept for any future custom date picker implementation
    
    // Add min date (today) for appointment booking
    const appointmentDateInputs = document.querySelectorAll('.appointment-date');
    const today = new Date().toISOString().split('T')[0];
    
    appointmentDateInputs.forEach(input => {
        if (!input.min) {
            input.min = today;
        }
    });
}

// Initialize search form functionality
function initializeSearchForms() {
    // Clear search button functionality
    const clearSearchButtons = document.querySelectorAll('.clear-search');
    clearSearchButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const form = this.closest('form');
            const inputs = form.querySelectorAll('input, select');
            
            inputs.forEach(input => {
                if (input.type === 'search' || input.type === 'text' || input.type === 'date' || input.tagName === 'SELECT') {
                    input.value = '';
                }
            });
            
            form.submit();
        });
    });
}

// Initialize sidebar toggle for mobile views
function initializeSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.body.classList.toggle('sb-sidenav-toggled');
        });
    }
}

// Validate appointment start and end times
function initializeAppointmentTimeValidation() {
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');
    
    if (startTimeInput && endTimeInput) {
        // Validate end time is after start time
        endTimeInput.addEventListener('change', function() {
            if (startTimeInput.value && endTimeInput.value) {
                if (endTimeInput.value <= startTimeInput.value) {
                    alert('End time must be after start time');
                    endTimeInput.value = '';
                }
            }
        });
        
        // Update end time if start time changes
        startTimeInput.addEventListener('change', function() {
            if (startTimeInput.value && endTimeInput.value) {
                if (endTimeInput.value <= startTimeInput.value) {
                    // Set end time to 30 minutes after start time
                    const startTime = new Date(`2000-01-01T${startTimeInput.value}`);
                    startTime.setMinutes(startTime.getMinutes() + 30);
                    const hours = String(startTime.getHours()).padStart(2, '0');
                    const minutes = String(startTime.getMinutes()).padStart(2, '0');
                    endTimeInput.value = `${hours}:${minutes}`;
                }
            } else if (startTimeInput.value && !endTimeInput.value) {
                // Set default appointment duration to 30 minutes
                const startTime = new Date(`2000-01-01T${startTimeInput.value}`);
                startTime.setMinutes(startTime.getMinutes() + 30);
                const hours = String(startTime.getHours()).padStart(2, '0');
                const minutes = String(startTime.getMinutes()).padStart(2, '0');
                endTimeInput.value = `${hours}:${minutes}`;
            }
        });
    }
}

// Format phone numbers as they are typed
function formatPhoneNumber(input) {
    let value = input.value.replace(/\D/g, ''); // Remove all non-digits
    
    if (value.length > 10) {
        value = value.substring(0, 10);
    }
    
    // Format the number as (XXX) XXX-XXXX
    if (value.length >= 6) {
        input.value = `(${value.substring(0, 3)}) ${value.substring(3, 6)}-${value.substring(6)}`;
    } else if (value.length >= 3) {
        input.value = `(${value.substring(0, 3)}) ${value.substring(3)}`;
    } else if (value.length > 0) {
        input.value = `(${value}`;
    }
}

// Show/hide password toggle
function togglePasswordVisibility(inputId) {
    const passwordInput = document.getElementById(inputId);
    const toggleIcon = document.querySelector(`[onclick="togglePasswordVisibility('${inputId}')"] i`);
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.remove('fa-eye');
        toggleIcon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.remove('fa-eye-slash');
        toggleIcon.classList.add('fa-eye');
    }
}

// Function to generate confidence color class for triage AI
function getConfidenceClass(confidence) {
    if (confidence >= 0.8) return 'ai-confidence-high';
    if (confidence >= 0.6) return 'ai-confidence-medium';
    return 'ai-confidence-low';
}

// Function to generate severity color class
function getSeverityClass(severity) {
    switch(severity) {
        case 'Low': return 'severity-low';
        case 'Medium': return 'severity-medium';
        case 'High': return 'severity-high';
        case 'Critical': return 'severity-critical';
        default: return '';
    }
}
