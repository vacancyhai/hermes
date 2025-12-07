# Flask Jinja2 Templates Guide - Sarkari Path

## Template Architecture Overview

The application uses **Flask Jinja2 templating engine** to render dynamic HTML pages. This guide provides template structure, Jinja2 syntax, and best practices.

## Template Hierarchy

```
templates/
├── base.html                 # Base template with common layout
├── index.html               # Homepage
├── admin/                   # Admin panel templates
├── auth/                    # Authentication pages
├── jobs/                    # Job-related pages
├── profile/                 # User profile pages
├── applications/            # Application tracking pages
├── notifications/           # Notification pages
└── components/              # Reusable components
```

## Base Template (`base.html`)

The base template provides the common structure for all pages.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Sarkari Path - Government Job Portal{% endblock %}</title>
    
    <!-- CSS Files -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_css %}{% endblock %}
    
    <!-- Favicon -->
    <link rel="icon" href="{{ url_for('static', filename='img/favicon.ico') }}">
</head>
<body>
    <!-- Include Navbar Component -->
    {% include 'components/navbar.html' %}
    
    <!-- Flash Messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="flash-messages">
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">
                        {{ message }}
                        <button class="close-btn">&times;</button>
                    </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}
    
    <!-- Main Content Area -->
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Include Footer Component -->
    {% include 'components/footer.html' %}
    
    <!-- JavaScript Files -->
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

## Component Templates

### Navbar Component (`components/navbar.html`)

```html
<nav class="navbar">
    <div class="container">
        <div class="navbar-brand">
            <a href="{{ url_for('main.index') }}">
                <img src="{{ url_for('static', filename='img/logo.png') }}" alt="Sarkari Path">
                <span>Sarkari Path</span>
            </a>
        </div>
        
        <div class="navbar-menu">
            <a href="{{ url_for('jobs.list') }}">Jobs</a>
            
            {% if current_user.is_authenticated %}
                <a href="{{ url_for('jobs.recommended') }}">Recommended</a>
                <a href="{{ url_for('applications.my_applications') }}">My Applications</a>
                <a href="{{ url_for('notifications.list') }}">
                    Notifications
                    {% if unread_count > 0 %}
                        <span class="badge">{{ unread_count }}</span>
                    {% endif %}
                </a>
                
                <div class="dropdown">
                    <button class="dropdown-toggle">
                        <img src="{{ current_user.avatar or url_for('static', filename='img/default-avatar.png') }}" 
                             alt="{{ current_user.full_name }}" class="avatar-sm">
                        {{ current_user.full_name }}
                    </button>
                    <div class="dropdown-menu">
                        <a href="{{ url_for('profile.view') }}">My Profile</a>
                        <a href="{{ url_for('profile.preferences') }}">Preferences</a>
                        {% if current_user.role == 'admin' %}
                            <a href="{{ url_for('admin.dashboard') }}">Admin Panel</a>
                        {% endif %}
                        <hr>
                        <a href="{{ url_for('auth.logout') }}">Logout</a>
                    </div>
                </div>
            {% else %}
                <a href="{{ url_for('auth.login') }}" class="btn btn-outline">Login</a>
                <a href="{{ url_for('auth.register') }}" class="btn btn-primary">Register</a>
            {% endif %}
        </div>
    </div>
</nav>
```

### Job Card Component (`components/job_card.html`)

```html
{# Usage: {% include 'components/job_card.html' with job=job_object %} #}

<div class="job-card">
    <div class="job-card-header">
        <h3 class="job-title">{{ job.job_title }}</h3>
        <span class="job-organization">{{ job.organization }}</span>
    </div>
    
    <div class="job-card-body">
        <div class="job-info">
            <span class="info-item">
                <i class="icon-vacancies"></i>
                {{ job.total_vacancies }} Vacancies
            </span>
            <span class="info-item">
                <i class="icon-education"></i>
                {{ job.eligibility.min_qualification }}
            </span>
            <span class="info-item">
                <i class="icon-calendar"></i>
                Apply by: {{ job.important_dates.application_end | date_format }}
            </span>
        </div>
        
        {% if job.eligibility.required_stream %}
            <div class="job-streams">
                {% for stream in job.eligibility.required_stream %}
                    <span class="badge badge-stream">{{ stream }}</span>
                {% endfor %}
            </div>
        {% endif %}
        
        <div class="job-description">
            {{ job.description | truncate(150) }}
        </div>
    </div>
    
    <div class="job-card-footer">
        <a href="{{ url_for('jobs.detail', job_id=job._id) }}" class="btn btn-outline">View Details</a>
        
        {% if current_user.is_authenticated %}
            <button class="btn btn-primary" onclick="addToTracker('{{ job._id }}')">
                Add to Tracker
            </button>
        {% endif %}
    </div>
</div>
```

## Page Templates

### Homepage (`index.html`)

```html
{% extends 'base.html' %}

{% block title %}Sarkari Path - Latest Government Jobs 2025{% endblock %}

{% block content %}
<!-- Hero Section -->
<section class="hero">
    <div class="container">
        <h1>Find Your Dream Government Job</h1>
        <p>Get personalized notifications for latest government job vacancies</p>
        
        <form action="{{ url_for('jobs.search') }}" method="GET" class="search-form">
            <input type="text" name="q" placeholder="Search for jobs, organizations..." 
                   value="{{ request.args.get('q', '') }}">
            <select name="organization">
                <option value="">All Organizations</option>
                {% for org in organizations %}
                    <option value="{{ org }}">{{ org }}</option>
                {% endfor %}
            </select>
            <button type="submit" class="btn btn-primary">Search Jobs</button>
        </form>
    </div>
</section>

<!-- Featured Jobs -->
<section class="featured-jobs">
    <div class="container">
        <h2>Latest Job Vacancies</h2>
        <div class="jobs-grid">
            {% for job in latest_jobs %}
                {% include 'components/job_card.html' %}
            {% endfor %}
        </div>
        
        <div class="text-center">
            <a href="{{ url_for('jobs.list') }}" class="btn btn-outline">View All Jobs</a>
        </div>
    </div>
</section>

<!-- Popular Organizations -->
<section class="organizations">
    <div class="container">
        <h2>Popular Organizations</h2>
        <div class="org-grid">
            {% for org in popular_organizations %}
                <a href="{{ url_for('jobs.list', organization=org.name) }}" class="org-card">
                    <img src="{{ org.logo }}" alt="{{ org.name }}">
                    <h3>{{ org.name }}</h3>
                    <p>{{ org.active_jobs }} Active Jobs</p>
                </a>
            {% endfor %}
        </div>
    </div>
</section>
{% endblock %}
```

### Job List Page (`jobs/job_list.html`)

```html
{% extends 'base.html' %}

{% block title %}Government Jobs - Sarkari Path{% endblock %}

{% block content %}
<div class="container">
    <div class="page-header">
        <h1>Government Job Vacancies</h1>
        <p>{{ total_jobs }} jobs found</p>
    </div>
    
    <div class="content-layout">
        <!-- Filters Sidebar -->
        <aside class="filters-sidebar">
            <h3>Filters</h3>
            
            <form method="GET" id="filter-form">
                <!-- Organization Filter -->
                <div class="filter-group">
                    <h4>Organization</h4>
                    {% for org in organizations %}
                        <label class="checkbox-label">
                            <input type="checkbox" name="organization" value="{{ org }}"
                                   {% if org in selected_organizations %}checked{% endif %}>
                            {{ org }}
                        </label>
                    {% endfor %}
                </div>
                
                <!-- Qualification Filter -->
                <div class="filter-group">
                    <h4>Minimum Qualification</h4>
                    {% for qual in qualifications %}
                        <label class="radio-label">
                            <input type="radio" name="qualification" value="{{ qual }}"
                                   {% if qual == selected_qualification %}checked{% endif %}>
                            {{ qual }}
                        </label>
                    {% endfor %}
                </div>
                
                <!-- Stream Filter -->
                <div class="filter-group">
                    <h4>Stream</h4>
                    {% for stream in streams %}
                        <label class="checkbox-label">
                            <input type="checkbox" name="stream" value="{{ stream }}"
                                   {% if stream in selected_streams %}checked{% endif %}>
                            {{ stream }}
                        </label>
                    {% endfor %}
                </div>
                
                <button type="submit" class="btn btn-primary btn-block">Apply Filters</button>
                <a href="{{ url_for('jobs.list') }}" class="btn btn-outline btn-block">Clear Filters</a>
            </form>
        </aside>
        
        <!-- Jobs List -->
        <div class="jobs-content">
            <!-- Sorting Options -->
            <div class="sorting-bar">
                <select name="sort" id="sort-select" onchange="updateSort(this.value)">
                    <option value="latest" {% if sort_by == 'latest' %}selected{% endif %}>Latest First</option>
                    <option value="deadline" {% if sort_by == 'deadline' %}selected{% endif %}>Deadline Soon</option>
                    <option value="vacancies" {% if sort_by == 'vacancies' %}selected{% endif %}>Most Vacancies</option>
                    <option value="popular" {% if sort_by == 'popular' %}selected{% endif %}>Most Popular</option>
                </select>
            </div>
            
            <!-- Jobs Grid -->
            <div class="jobs-grid">
                {% if jobs %}
                    {% for job in jobs %}
                        {% include 'components/job_card.html' %}
                    {% endfor %}
                {% else %}
                    <div class="no-results">
                        <img src="{{ url_for('static', filename='img/no-results.svg') }}" alt="No jobs found">
                        <h3>No jobs found</h3>
                        <p>Try adjusting your filters or search criteria</p>
                    </div>
                {% endif %}
            </div>
            
            <!-- Pagination -->
            {% if pagination.pages > 1 %}
                <div class="pagination">
                    {% if pagination.has_prev %}
                        <a href="{{ url_for('jobs.list', page=pagination.prev_num, **request.args) }}" 
                           class="page-link">Previous</a>
                    {% endif %}
                    
                    {% for page_num in pagination.iter_pages(left_edge=1, right_edge=1, left_current=2, right_current=2) %}
                        {% if page_num %}
                            <a href="{{ url_for('jobs.list', page=page_num, **request.args) }}" 
                               class="page-link {% if page_num == pagination.page %}active{% endif %}">
                                {{ page_num }}
                            </a>
                        {% else %}
                            <span class="page-ellipsis">...</span>
                        {% endif %}
                    {% endfor %}
                    
                    {% if pagination.has_next %}
                        <a href="{{ url_for('jobs.list', page=pagination.next_num, **request.args) }}" 
                           class="page-link">Next</a>
                    {% endif %}
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
function updateSort(value) {
    const url = new URL(window.location);
    url.searchParams.set('sort', value);
    window.location = url.toString();
}

function addToTracker(jobId) {
    // AJAX call to add job to tracker
    fetch(`/api/applications`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ job_id: jobId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Job added to your tracker!');
        }
    });
}
</script>
{% endblock %}
```

### Job Detail Page (`jobs/job_detail.html`)

```html
{% extends 'base.html' %}

{% block title %}{{ job.job_title }} - {{ job.organization }} - Sarkari Path{% endblock %}

{% block content %}
<div class="container">
    <!-- Breadcrumb -->
    <nav class="breadcrumb">
        <a href="{{ url_for('main.index') }}">Home</a> /
        <a href="{{ url_for('jobs.list') }}">Jobs</a> /
        <span>{{ job.job_title }}</span>
    </nav>
    
    <div class="job-detail-layout">
        <!-- Job Header -->
        <div class="job-header">
            <div class="job-title-section">
                <h1>{{ job.job_title }}</h1>
                <div class="job-meta">
                    <span class="organization">{{ job.organization }}</span>
                    <span class="department">{{ job.department }}</span>
                    <span class="post-code">{{ job.post_code }}</span>
                </div>
            </div>
            
            <div class="job-actions">
                {% if current_user.is_authenticated %}
                    <button class="btn btn-primary" onclick="openTrackerModal('{{ job._id }}')">
                        <i class="icon-bookmark"></i> Add to Tracker
                    </button>
                    <button class="btn btn-outline" onclick="shareJob()">
                        <i class="icon-share"></i> Share
                    </button>
                {% else %}
                    <a href="{{ url_for('auth.login') }}" class="btn btn-primary">
                        Login to Track Job
                    </a>
                {% endif %}
            </div>
        </div>
        
        <!-- Important Dates -->
        <div class="important-dates-card">
            <h2>Important Dates</h2>
            <div class="dates-grid">
                <div class="date-item">
                    <span class="date-label">Notification Date</span>
                    <span class="date-value">{{ job.important_dates.notification_date | date_format }}</span>
                </div>
                <div class="date-item">
                    <span class="date-label">Application Start</span>
                    <span class="date-value">{{ job.important_dates.application_start | date_format }}</span>
                </div>
                <div class="date-item highlight">
                    <span class="date-label">Application End</span>
                    <span class="date-value">{{ job.important_dates.application_end | date_format }}</span>
                </div>
                <div class="date-item">
                    <span class="date-label">Exam Date</span>
                    <span class="date-value">{{ job.important_dates.exam_date | date_format }}</span>
                </div>
            </div>
        </div>
        
        <!-- Eligibility Criteria -->
        <div class="section-card">
            <h2>Eligibility Criteria</h2>
            
            <div class="eligibility-section">
                <h3>Educational Qualification</h3>
                <p><strong>Minimum:</strong> {{ job.eligibility.min_qualification }}</p>
                {% if job.eligibility.required_stream %}
                    <p><strong>Required Stream:</strong> 
                        {% for stream in job.eligibility.required_stream %}
                            <span class="badge">{{ stream }}</span>
                        {% endfor %}
                    </p>
                {% endif %}
            </div>
            
            <div class="eligibility-section">
                <h3>Age Limit</h3>
                <p><strong>Minimum Age:</strong> {{ job.eligibility.age_limit.min }} years</p>
                <p><strong>Maximum Age:</strong> {{ job.eligibility.age_limit.max }} years</p>
                
                {% if job.eligibility.age_limit.relaxation %}
                    <h4>Age Relaxation</h4>
                    <ul>
                        {% for category, years in job.eligibility.age_limit.relaxation.items() %}
                            <li>{{ category }}: {{ years }} years</li>
                        {% endfor %}
                    </ul>
                {% endif %}
            </div>
            
            <div class="eligibility-section">
                <h3>Category-wise Vacancies</h3>
                <table class="vacancies-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Vacancies</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for category, count in job.eligibility.category_wise_vacancies.items() %}
                            <tr>
                                <td>{{ category }}</td>
                                <td>{{ count }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td><strong>Total</strong></td>
                            <td><strong>{{ job.total_vacancies }}</strong></td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
        
        <!-- Application Details -->
        <div class="section-card">
            <h2>Application Details</h2>
            
            <div class="application-info">
                <h3>Application Fee</h3>
                <ul>
                    {% for category, fee in job.application_details.application_fee.items() %}
                        <li>{{ category }}: ₹{{ fee if fee > 0 else 'No Fee' }}</li>
                    {% endfor %}
                </ul>
                
                <h3>Application Mode</h3>
                <p>{{ job.application_details.application_mode }}</p>
                
                <h3>Official Website</h3>
                <a href="{{ job.application_details.official_website }}" target="_blank" class="btn btn-primary">
                    Apply on Official Website <i class="icon-external"></i>
                </a>
            </div>
        </div>
        
        <!-- Selection Process -->
        <div class="section-card">
            <h2>Selection Process</h2>
            <ol class="selection-process-list">
                {% for step in job.selection_process %}
                    <li>{{ step }}</li>
                {% endfor %}
            </ol>
        </div>
        
        <!-- Documents Required -->
        <div class="section-card">
            <h2>Documents Required</h2>
            <ul class="documents-list">
                {% for doc in job.documents_required %}
                    <li><i class="icon-document"></i> {{ doc }}</li>
                {% endfor %}
            </ul>
        </div>
        
        <!-- Job Description -->
        <div class="section-card">
            <h2>Job Description</h2>
            <div class="job-description">
                {{ job.description | safe }}
            </div>
        </div>
    </div>
</div>

<!-- Tracker Modal -->
<div id="trackerModal" class="modal">
    <div class="modal-content">
        <span class="modal-close">&times;</span>
        <h2>Add to Application Tracker</h2>
        
        <form id="trackerForm" onsubmit="submitTrackerForm(event)">
            <div class="form-group">
                <label for="application_number">Application Number (Optional)</label>
                <input type="text" id="application_number" name="application_number" 
                       placeholder="Enter your application number">
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" name="is_priority" value="true">
                    Mark as Priority Job
                </label>
            </div>
            
            <div class="form-group">
                <label for="notes">Personal Notes</label>
                <textarea id="notes" name="notes" rows="3" 
                          placeholder="Add any personal notes about this job..."></textarea>
            </div>
            
            <div class="form-group">
                <label>Enable Reminders for:</label>
                <label><input type="checkbox" name="reminder_deadline" checked> Application Deadline</label>
                <label><input type="checkbox" name="reminder_admit" checked> Admit Card Release</label>
                <label><input type="checkbox" name="reminder_exam" checked> Exam Date</label>
                <label><input type="checkbox" name="reminder_result" checked> Result Declaration</label>
            </div>
            
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Add to Tracker</button>
                <button type="button" class="btn btn-outline" onclick="closeTrackerModal()">Cancel</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{{ url_for('static', filename='js/job_detail.js') }}"></script>
{% endblock %}
```

### User Profile Page (`profile/profile.html`)

```html
{% extends 'base.html' %}

{% block title %}My Profile - Sarkari Path{% endblock %}

{% block content %}
<div class="container">
    <div class="profile-layout">
        <!-- Sidebar -->
        <aside class="profile-sidebar">
            <div class="profile-card">
                <img src="{{ current_user.avatar or url_for('static', filename='img/default-avatar.png') }}" 
                     alt="{{ current_user.full_name }}" class="profile-avatar">
                <h2>{{ current_user.full_name }}</h2>
                <p class="profile-email">{{ current_user.email }}</p>
                <p class="profile-join-date">Member since {{ current_user.created_at | date_format }}</p>
            </div>
            
            <nav class="profile-nav">
                <a href="{{ url_for('profile.view') }}" class="active">Profile</a>
                <a href="{{ url_for('profile.edit') }}">Edit Profile</a>
                <a href="{{ url_for('profile.preferences') }}">Notification Preferences</a>
                <a href="{{ url_for('applications.my_applications') }}">My Applications</a>
                <a href="{{ url_for('auth.change_password') }}">Change Password</a>
            </nav>
        </aside>
        
        <!-- Main Content -->
        <div class="profile-content">
            <!-- Personal Information -->
            <div class="section-card">
                <h2>Personal Information</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <label>Full Name</label>
                        <p>{{ profile.personal_info.full_name or current_user.full_name }}</p>
                    </div>
                    <div class="info-item">
                        <label>Date of Birth</label>
                        <p>{{ profile.personal_info.date_of_birth | date_format if profile.personal_info.date_of_birth else 'Not provided' }}</p>
                    </div>
                    <div class="info-item">
                        <label>Gender</label>
                        <p>{{ profile.personal_info.gender or 'Not provided' }}</p>
                    </div>
                    <div class="info-item">
                        <label>Category</label>
                        <p>{{ profile.personal_info.category or 'Not provided' }}</p>
                    </div>
                    <div class="info-item">
                        <label>PWD Status</label>
                        <p>{{ 'Yes' if profile.personal_info.pwd else 'No' }}</p>
                    </div>
                    <div class="info-item">
                        <label>Location</label>
                        <p>{{ profile.personal_info.city }}, {{ profile.personal_info.state }}</p>
                    </div>
                </div>
            </div>
            
            <!-- Education Details -->
            <div class="section-card">
                <h2>Education Details</h2>
                
                <div class="education-card">
                    <h3>10th Standard</h3>
                    {% if profile.education.get('10th', {}).get('completed') %}
                        <p><strong>Percentage:</strong> {{ profile.education['10th'].percentage }}%</p>
                        <p><strong>Year:</strong> {{ profile.education['10th'].year }}</p>
                    {% else %}
                        <p class="text-muted">Not provided</p>
                    {% endif %}
                </div>
                
                <div class="education-card">
                    <h3>12th Standard</h3>
                    {% if profile.education.get('12th', {}).get('completed') %}
                        <p><strong>Stream:</strong> {{ profile.education['12th'].stream }}</p>
                        <p><strong>Percentage:</strong> {{ profile.education['12th'].percentage }}%</p>
                        <p><strong>Year:</strong> {{ profile.education['12th'].year }}</p>
                    {% else %}
                        <p class="text-muted">Not provided</p>
                    {% endif %}
                </div>
                
                <div class="education-card">
                    <h3>Graduation</h3>
                    {% if profile.education.get('graduation', {}).get('completed') %}
                        <p><strong>Degree:</strong> {{ profile.education.graduation.degree }}</p>
                        <p><strong>Specialization:</strong> {{ profile.education.graduation.specialization }}</p>
                        <p><strong>Percentage:</strong> {{ profile.education.graduation.percentage }}%</p>
                        <p><strong>Year:</strong> {{ profile.education.graduation.year }}</p>
                    {% else %}
                        <p class="text-muted">Not provided</p>
                    {% endif %}
                </div>
            </div>
            
            <!-- Notification Preferences -->
            <div class="section-card">
                <h2>Notification Preferences</h2>
                <div class="preferences-summary">
                    <div class="pref-item">
                        <label>Preferred Organizations</label>
                        <div class="tags">
                            {% for org in profile.notification_preferences.organizations %}
                                <span class="tag">{{ org }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div class="pref-item">
                        <label>Job Types</label>
                        <div class="tags">
                            {% for type in profile.notification_preferences.job_types %}
                                <span class="tag">{{ type }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div class="pref-item">
                        <label>Preferred Locations</label>
                        <div class="tags">
                            {% for loc in profile.notification_preferences.locations %}
                                <span class="tag">{{ loc }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    
                    <div class="pref-item">
                        <label>Notification Channels</label>
                        <p>
                            Email: {{ 'Enabled' if profile.notification_preferences.email_enabled else 'Disabled' }} | 
                            SMS: {{ 'Enabled' if profile.notification_preferences.sms_enabled else 'Disabled' }} | 
                            Push: {{ 'Enabled' if profile.notification_preferences.push_enabled else 'Disabled' }}
                        </p>
                    </div>
                </div>
                
                <a href="{{ url_for('profile.preferences') }}" class="btn btn-outline">
                    Edit Preferences
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## Jinja2 Filters & Functions

### Custom Filters (defined in `app/utils/template_filters.py`)

```python
from datetime import datetime
from flask import Blueprint

filters = Blueprint('filters', __name__)

@filters.app_template_filter('date_format')
def date_format(value, format='%d %b %Y'):
    """Format datetime object or string to readable date"""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime(format)

@filters.app_template_filter('time_ago')
def time_ago(value):
    """Convert datetime to 'time ago' format"""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    
    diff = datetime.now() - value
    
    if diff.days > 365:
        return f"{diff.days // 365} year{'s' if diff.days // 365 > 1 else ''} ago"
    elif diff.days > 30:
        return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 > 1 else ''} ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 > 1 else ''} ago"
    else:
        return "just now"

@filters.app_template_filter('truncate')
def truncate(value, length=100, suffix='...'):
    """Truncate text to specified length"""
    if len(value) <= length:
        return value
    return value[:length].rsplit(' ', 1)[0] + suffix

@filters.app_template_filter('currency')
def currency_format(value):
    """Format number as Indian currency"""
    return f"₹{value:,.2f}"
```

### Context Processors (globally available variables)

```python
from flask import g
from app.models.notification import Notification

@app.context_processor
def inject_global_vars():
    """Inject variables available in all templates"""
    unread_count = 0
    if current_user.is_authenticated:
        unread_count = Notification.count_unread(current_user.id)
    
    return {
        'unread_count': unread_count,
        'current_year': datetime.now().year,
        'site_name': 'Sarkari Path'
    }
```

## Email Templates (Flask-Mail)

### Job Notification Email (`templates/emails/job_notification.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .job-card { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .btn { display: inline-block; padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 New Job Alert!</h1>
        </div>
        
        <div class="content">
            <p>Hi {{ user.full_name }},</p>
            <p>A new job matching your profile has been posted:</p>
            
            <div class="job-card">
                <h2>{{ job.job_title }}</h2>
                <p><strong>Organization:</strong> {{ job.organization }}</p>
                <p><strong>Vacancies:</strong> {{ job.total_vacancies }}</p>
                <p><strong>Qualification:</strong> {{ job.eligibility.min_qualification }}</p>
                <p><strong>Last Date:</strong> {{ job.important_dates.application_end }}</p>
                
                <a href="{{ url_for('jobs.detail', job_id=job._id, _external=True) }}" class="btn">
                    View Job Details
                </a>
            </div>
            
            <p>Don't miss this opportunity! Apply before the deadline.</p>
        </div>
        
        <div class="footer">
            <p>© {{ current_year }} Sarkari Path. All rights reserved.</p>
            <p>
                <a href="{{ url_for('profile.preferences', _external=True) }}">Update Preferences</a> | 
                <a href="{{ url_for('auth.unsubscribe', _external=True) }}">Unsubscribe</a>
            </p>
        </div>
    </div>
</body>
</html>
```

### Reminder Email Template (`templates/emails/reminder.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #FF9800; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .reminder-card { background: white; padding: 20px; margin: 20px 0; border-left: 4px solid #FF9800; }
        .btn { display: inline-block; padding: 10px 20px; background: #FF9800; color: white; text-decoration: none; border-radius: 5px; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Important Reminder!</h1>
        </div>
        
        <div class="content">
            <p>Hi {{ user.full_name }},</p>
            
            <div class="reminder-card">
                <h2>{{ reminder_type }}</h2>
                <p><strong>Job:</strong> {{ application.job.job_title }}</p>
                <p><strong>Organization:</strong> {{ application.job.organization }}</p>
                
                {% if reminder_type == 'Application Deadline' %}
                    <p><strong>Last Date:</strong> {{ application.job.important_dates.application_end }}</p>
                    <p>⚠️ Don't forget to submit your application!</p>
                {% elif reminder_type == 'Admit Card' %}
                    <p><strong>Admit Card Date:</strong> {{ application.job.important_dates.admit_card_date }}</p>
                    <p>📄 Your admit card will be available soon!</p>
                {% elif reminder_type == 'Exam Date' %}
                    <p><strong>Exam Date:</strong> {{ application.job.important_dates.exam_date }}</p>
                    <p>📝 Prepare well for your exam!</p>
                {% elif reminder_type == 'Result' %}
                    <p><strong>Result Date:</strong> {{ application.job.important_dates.result_date }}</p>
                    <p>🎓 Results are expected soon!</p>
                {% endif %}
                
                <a href="{{ url_for('applications.detail', app_id=application._id, _external=True) }}" class="btn">
                    View Application
                </a>
            </div>
        </div>
        
        <div class="footer">
            <p>© {{ current_year }} Sarkari Path. All rights reserved.</p>
            <p>
                <a href="{{ url_for('applications.my_applications', _external=True) }}">Manage Applications</a>
            </p>
        </div>
    </div>
</body>
</html>
```

### Welcome Email Template (`templates/emails/welcome.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #2196F3; color: white; padding: 30px; text-align: center; }
        .content { padding: 30px; background: #f9f9f9; }
        .feature { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .btn { display: inline-block; padding: 12px 30px; background: #2196F3; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Sarkari Path! 🎉</h1>
        </div>
        
        <div class="content">
            <p>Hi {{ user.full_name }},</p>
            <p>Thank you for registering with Sarkari Path - your one-stop destination for government job opportunities!</p>
            
            <h3>What's Next?</h3>
            
            <div class="feature">
                <strong>📝 Complete Your Profile</strong>
                <p>Add your education details and preferences to get personalized job recommendations.</p>
            </div>
            
            <div class="feature">
                <strong>🔔 Set Notification Preferences</strong>
                <p>Choose organizations and job types you're interested in to receive relevant alerts.</p>
            </div>
            
            <div class="feature">
                <strong>💼 Browse Latest Jobs</strong>
                <p>Explore thousands of government job vacancies updated daily.</p>
            </div>
            
            <div class="feature">
                <strong>📊 Track Applications</strong>
                <p>Keep track of your applications and never miss important dates.</p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ url_for('profile.edit', _external=True) }}" class="btn">
                    Complete Your Profile
                </a>
            </div>
            
            <p>If you have any questions, feel free to contact our support team.</p>
            <p>Best wishes for your job search!</p>
        </div>
        
        <div class="footer">
            <p>© {{ current_year }} Sarkari Path. All rights reserved.</p>
            <p><a href="{{ url_for('main.index', _external=True) }}">Visit Website</a></p>
        </div>
    </div>
</body>
</html>
```

## Best Practices

### 1. Template Inheritance
- Use `{% extends 'base.html' %}` for consistent layout
- Override specific blocks: `{% block content %}...{% endblock %}`

### 2. Include Components
- Reusable components: `{% include 'components/navbar.html' %}`
- Pass context: `{% include 'components/job_card.html' with job=job_object %}`

### 3. URL Generation
- Always use `url_for()`: `{{ url_for('jobs.list') }}`
- Pass parameters: `{{ url_for('jobs.detail', job_id=job._id) }}`

### 4. Static Files
- CSS: `{{ url_for('static', filename='css/style.css') }}`
- JS: `{{ url_for('static', filename='js/main.js') }}`
- Images: `{{ url_for('static', filename='img/logo.png') }}`

### 5. Conditional Rendering
```jinja2
{% if current_user.is_authenticated %}
    <!-- Logged in content -->
{% else %}
    <!-- Guest content -->
{% endif %}
```

### 6. Loop Handling
```jinja2
{% for job in jobs %}
    {{ job.job_title }}
{% else %}
    <p>No jobs found</p>
{% endfor %}
```

### 7. Safe Content Rendering
- Escape by default: `{{ user_input }}`
- Trust HTML: `{{ trusted_html | safe }}`

### 8. Flash Messages
```python
# In route
flash('Job added successfully!', 'success')
flash('Error occurred', 'error')
```

```jinja2
<!-- In template -->
{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        {% for category, message in messages %}
            <div class="alert alert-{{ category }}">{{ message }}</div>
        {% endfor %}
    {% endif %}
{% endwith %}
```

## MongoDB Integration with Jinja2

### Passing Data from Routes

```python
from flask import render_template
from app.models.job import Job

@jobs_bp.route('/jobs')
def list():
    jobs = Job.find({'status': 'active'}).limit(20)
    return render_template('jobs/job_list.html', 
                         jobs=jobs,
                         total_jobs=Job.count())
```

### Template Rendering with MongoDB Data

```jinja2
{% for job in jobs %}
    <h3>{{ job.job_title }}</h3>
    <p>{{ job.organization }}</p>
    
    {# Access nested MongoDB documents #}
    <p>Apply by: {{ job.important_dates.application_end }}</p>
    
    {# Loop through arrays #}
    {% for stream in job.eligibility.required_stream %}
        <span>{{ stream }}</span>
    {% endfor %}
{% endfor %}
```

---

This guide provides the foundation for building Flask Jinja2 templates for the Sarkari Path application with MongoDB backend integration.
