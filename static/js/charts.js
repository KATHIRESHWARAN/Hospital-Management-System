// Charts for Hospital Management System
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all charts on the page
    initializeCharts();
});

function initializeCharts() {
    // Check for each chart type and initialize if present
    if (document.getElementById('appointmentsChart')) {
        initializeAppointmentsChart();
    }

    if (document.getElementById('recordTypesChart')) {
        initializeRecordTypesChart();
    }

    if (document.getElementById('staffDepartmentsChart')) {
        initializeStaffDepartmentsChart();
    }

    if (document.getElementById('triageSeverityChart')) {
        initializeTriageSeverityChart();
    }
}

// Monthly Appointments Chart
function initializeAppointmentsChart() {
    fetch('/api/chart/appointments')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('appointmentsChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Appointments',
                        data: data.data,
                        backgroundColor: 'rgba(0, 123, 255, 0.2)',
                        borderColor: 'rgba(0, 123, 255, 1)',
                        borderWidth: 2,
                        tension: 0.3,
                        pointBackgroundColor: 'rgba(0, 123, 255, 1)',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Monthly Appointments',
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            display: false
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(0, 0, 0, 0.7)'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error fetching appointment chart data:', error);
            document.getElementById('appointmentsChart').innerHTML = '<div class="alert alert-danger">Error loading chart data</div>';
        });
}

// Record Types Distribution Chart
function initializeRecordTypesChart() {
    fetch('/api/chart/record-types')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('recordTypesChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.data,
                        backgroundColor: [
                            'rgba(0, 123, 255, 0.7)',
                            'rgba(40, 167, 69, 0.7)',
                            'rgba(255, 193, 7, 0.7)',
                            'rgba(220, 53, 69, 0.7)',
                            'rgba(23, 162, 184, 0.7)',
                            'rgba(111, 66, 193, 0.7)',
                            'rgba(248, 108, 107, 0.7)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Medical Record Types',
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            display: true,
                            position: 'bottom'
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.7)'
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error fetching record types chart data:', error);
            document.getElementById('recordTypesChart').innerHTML = '<div class="alert alert-danger">Error loading chart data</div>';
        });
}

// Staff by Department Chart
function initializeStaffDepartmentsChart() {
    fetch('/api/chart/staff-departments')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('staffDepartmentsChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Staff Count',
                        data: data.data,
                        backgroundColor: 'rgba(23, 162, 184, 0.7)',
                        borderColor: 'rgba(23, 162, 184, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Staff by Department',
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.7)'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error fetching staff departments chart data:', error);
            document.getElementById('staffDepartmentsChart').innerHTML = '<div class="alert alert-danger">Error loading chart data</div>';
        });
}

// Triage Severity Chart
function initializeTriageSeverityChart() {
    fetch('/api/chart/triage-severity')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('triageSeverityChart').getContext('2d');
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.data,
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.7)',  // Low - green
                            'rgba(255, 193, 7, 0.7)',  // Medium - yellow
                            'rgba(255, 128, 0, 0.7)',  // High - orange
                            'rgba(220, 53, 69, 0.7)'   // Critical - red
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Triage Assessment Severity',
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            display: true,
                            position: 'bottom'
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.7)'
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error fetching triage severity chart data:', error);
            document.getElementById('triageSeverityChart').innerHTML = '<div class="alert alert-danger">Error loading chart data</div>';
        });
}
