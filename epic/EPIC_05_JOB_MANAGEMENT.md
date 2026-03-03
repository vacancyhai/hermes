# Epic 5: Job Management & CRUD Operations

## 🎯 Epic Overview

**Epic ID**: EPIC-005  
**Epic Title**: Job Management & CRUD Operations  
**Epic Description**: Implement comprehensive job posting management system for admins with full CRUD operations, validation, and workflow management.  
**Business Value**: Enables admins to efficiently manage job postings and maintain accurate job information for users.  
**Priority**: HIGH  
**Estimated Timeline**: 4 weeks (Phase 3: Weeks 8-11)

## 📋 Epic Acceptance Criteria

- ✅ Complete job model with all required fields
- ✅ Full CRUD operations for job management
- ✅ Job search and filtering capabilities
- ✅ Job lifecycle and status management
- ✅ Performance optimization for job queries

## 📊 Epic Metrics

- **Story Count**: 6 stories
- **Story Points**: 48 (estimated)
- **Dependencies**: Epic 4 (RBAC System), Epic 2 (Backend API)
- **Success Metrics**:
  - Job creation time <2 seconds
  - Job search results <500ms
  - 100% data validation coverage
  - Job lifecycle automation working

---

## 📝 User Stories

### Story 5.1: Basic Job Model & Database Schema

**Story ID**: EPIC-005-STORY-001  
**Story Title**: Basic Job Model & Database Schema  
**Priority**: HIGHEST  
**Story Points**: 8  
**Sprint**: Week 8

**As a** backend developer  
**I want** a comprehensive job model  
**So that** all job information is properly structured

#### Acceptance Criteria:
- [ ] Job model with all required fields
- [ ] MongoDB indexes for performance
- [ ] Data validation rules
- [ ] Relationship with other models
- [ ] Job status management
- [ ] Audit trail for job changes

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/models/job.py            # Complete job model
backend/app/models/job_category.py   # Job categorization
backend/app/models/organization.py   # Organization model
backend/scripts/job-indexes.py      # Database indexes
backend/app/validators/job_validators.py # Job validation
backend/app/utils/job_utils.py       # Job utilities
```

#### Job Model Structure:
```python
class Job(Document):
    # Basic Information
    title = StringField(required=True, max_length=200)
    organization = StringField(required=True, max_length=150)
    post_name = StringField(required=True, max_length=150)
    total_posts = IntField(default=1)
    
    # Dates
    notification_date = DateTimeField()
    application_start = DateTimeField()
    application_end = DateTimeField(required=True)
    exam_date = DateTimeField()
    result_date = DateTimeField()
    
    # Eligibility
    min_age = IntField(default=18)
    max_age = IntField(default=35)
    education_qualification = ListField(StringField())
    experience_required = BooleanField(default=False)
    
    # Location & Category
    location = ListField(StringField())
    job_type = StringField(choices=['permanent', 'temporary', 'contract'])
    category = StringField(choices=['general', 'obc', 'sc', 'st', 'ews'])
    
    # Application Details
    application_fee = DictField()  # {general: 500, sc_st: 0, etc}
    how_to_apply = StringField(choices=['online', 'offline', 'both'])
    application_link = URLField()
    
    # Content
    description = StringField()
    selection_process = ListField(StringField())
    important_links = ListField(DictField())
    
    # Metadata
    status = StringField(choices=['draft', 'active', 'closed', 'cancelled'], default='draft')
    created_by = ObjectIdField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
```

#### Definition of Done:
- [ ] Job model implemented with validation
- [ ] Database indexes created for performance
- [ ] Relationships with other models established
- [ ] Status management working
- [ ] Audit trail tracking changes
- [ ] Data validation preventing invalid entries

---

### Story 5.2: Job Creation API Endpoint

**Story ID**: EPIC-005-STORY-002  
**Story Title**: Job Creation API Endpoint  
**Priority**: HIGH  
**Story Points**: 8  
**Sprint**: Week 8-9

**As an** admin  
**I want** to create new job postings  
**So that** job seekers can discover opportunities

#### Acceptance Criteria:
- [ ] POST /api/v1/admin/jobs endpoint
- [ ] Input validation for all job fields
- [ ] File upload for job notifications
- [ ] Job scheduling for future publication
- [ ] Duplicate job detection
- [ ] Job creation notification to relevant users

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/api/v1/routes/admin/jobs.py # Job creation endpoint
backend/app/services/job_service.py   # Job business logic
backend/app/validators/job_schemas.py # Job validation schemas
backend/app/utils/file_upload.py     # File handling utilities
backend/app/tasks/job_tasks.py       # Background job processing
backend/app/utils/duplicate_detector.py # Duplicate detection
```

#### API Endpoint Specification:
```python
@bp.route('/jobs', methods=['POST'])
@require_role('admin', 'operator')
@validate_json('job_creation_schema')
def create_job():
    """
    Create new job posting
    
    Request Body:
    {
        "title": "Staff Selection Commission - Multi Tasking Staff",
        "organization": "SSC",
        "post_name": "Multi Tasking Staff (Non-Technical)",
        "total_posts": 3261,
        "application_end": "2026-04-15T23:59:59Z",
        "min_age": 18,
        "max_age": 25,
        "education_qualification": ["10th Pass"],
        "location": ["All India"],
        "application_fee": {"general": 100, "sc_st": 0},
        "how_to_apply": "online",
        "application_link": "https://ssc.nic.in/apply"
    }
    
    Response:
    {
        "success": true,
        "job_id": "507f1f77bcf86cd799439011",
        "message": "Job created successfully",
        "status": "draft"
    }
    """
```

#### Definition of Done:
- [ ] Job creation endpoint working
- [ ] All input validation implemented
- [ ] File uploads handled securely
- [ ] Job scheduling operational
- [ ] Duplicate detection preventing duplicates
- [ ] Notifications sent to relevant users

---

### Story 5.3: Job Listing & Search API

**Story ID**: EPIC-005-STORY-003  
**Story Title**: Job Listing & Search API  
**Priority**: HIGH  
**Story Points**: 8  
**Sprint**: Week 9

**As a** user  
**I want** to view and search job listings  
**So that** I can find relevant opportunities

#### Acceptance Criteria:
- [ ] GET /api/v1/jobs endpoint with pagination
- [ ] Search functionality across job titles and descriptions
- [ ] Filter by organization, location, qualification
- [ ] Sort by date, relevance, deadline
- [ ] Job status filtering (active, closed)
- [ ] Response caching for performance

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/api/v1/routes/jobs.py    # Job listing endpoints
backend/app/services/search_service.py # Search logic
backend/app/utils/pagination.py     # Pagination helpers
backend/app/cache/job_cache.py      # Job caching
backend/app/services/filter_service.py # Job filtering
backend/app/utils/sort_utils.py     # Sorting utilities
```

#### API Endpoint Specification:
```python
@bp.route('/jobs', methods=['GET'])
def list_jobs():
    """
    Get paginated job listings with search and filters
    
    Query Parameters:
    - page: int (default: 1)
    - limit: int (default: 20, max: 100)
    - search: str (search in title, organization, description)
    - organization: str (filter by organization)
    - location: str (filter by location)
    - qualification: str (filter by education requirement)
    - status: str (active, closed)
    - sort: str (date, relevance, deadline)
    - order: str (asc, desc)
    
    Response:
    {
        "success": true,
        "jobs": [...],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 150,
            "pages": 8
        },
        "cache_hit": true
    }
    """
```

#### Definition of Done:
- [ ] Job listing API working with pagination
- [ ] Search functionality operational across fields
- [ ] Filtering working for all specified criteria
- [ ] Sorting implemented for all options
- [ ] Status filtering preventing closed job display
- [ ] Response caching improving performance

---

### Story 5.4: Job Detail & View API

**Story ID**: EPIC-005-STORY-004  
**Story Title**: Job Detail & View API  
**Priority**: MEDIUM  
**Story Points**: 6  
**Sprint**: Week 9-10

**As a** user  
**I want** to view detailed job information  
**So that** I can understand job requirements

#### Acceptance Criteria:
- [ ] GET /api/v1/jobs/{id} endpoint
- [ ] Complete job information display
- [ ] Related jobs suggestions
- [ ] View count tracking
- [ ] Job sharing functionality
- [ ] Print-friendly format

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/api/v1/routes/jobs.py    # Job detail endpoint
backend/app/services/recommendation_service.py # Related jobs
backend/app/models/job_view.py       # View tracking
backend/app/utils/share_utils.py     # Sharing functionality
backend/app/utils/print_formatter.py # Print formatting
backend/app/cache/job_detail_cache.py # Detail caching
```

#### Definition of Done:
- [ ] Job detail endpoint returning complete information
- [ ] Related jobs suggestions working
- [ ] View count incrementing correctly
- [ ] Sharing functionality operational
- [ ] Print-friendly format available
- [ ] Detail caching improving performance

---

### Story 5.5: Job Update & Management API

**Story ID**: EPIC-005-STORY-005  
**Story Title**: Job Update & Management API  
**Priority**: HIGH  
**Story Points**: 9  
**Sprint**: Week 10

**As an** admin  
**I want** to update existing job postings  
**So that** job information remains accurate

#### Acceptance Criteria:
- [ ] PUT /api/v1/admin/jobs/{id} endpoint
- [ ] Partial update capability with PATCH
- [ ] Version history tracking
- [ ] Change notification to subscribed users
- [ ] Approval workflow for sensitive changes
- [ ] Bulk update operations

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/api/v1/routes/admin/jobs.py # Update endpoints
backend/app/models/job_history.py    # Change tracking
backend/app/services/notification_service.py # Change alerts
backend/app/decorators/approval.py   # Approval workflow
backend/app/services/bulk_service.py # Bulk operations
backend/app/utils/change_detector.py # Change detection
```

#### Definition of Done:
- [ ] Job update endpoint working completely
- [ ] Partial updates with PATCH working
- [ ] Version history tracking all changes
- [ ] Notifications sent to affected users
- [ ] Approval workflow operational for sensitive changes
- [ ] Bulk update operations functional

---

### Story 5.6: Job Status & Lifecycle Management

**Story ID**: EPIC-005-STORY-006  
**Story Title**: Job Status & Lifecycle Management  
**Priority**: MEDIUM  
**Story Points**: 9  
**Sprint**: Week 10-11

**As an** admin  
**I want** to manage job statuses and lifecycle  
**So that** jobs progress through proper workflow

#### Acceptance Criteria:
- [ ] Job status transitions (draft → published → closed)
- [ ] Automatic status changes based on dates
- [ ] Status-based access controls
- [ ] Lifecycle event notifications
- [ ] Job archiving and restoration
- [ ] Status audit trail

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/models/job_status.py     # Status model
backend/app/services/lifecycle_service.py # Lifecycle logic
backend/app/tasks/job_tasks.py       # Automated status updates
backend/app/api/v1/routes/admin/job_status.py # Status API
backend/app/utils/status_manager.py  # Status management
backend/app/services/archive_service.py # Job archiving
```

#### Job Lifecycle States:
```python
JOB_LIFECYCLE = {
    'draft': {
        'next_states': ['active', 'cancelled'],
        'permissions': ['admin', 'operator'],
        'auto_transition': False
    },
    'active': {
        'next_states': ['closed', 'cancelled'],
        'permissions': ['admin'],
        'auto_transition': True,  # Based on application_end date
        'notifications': ['new_job_alert']
    },
    'closed': {
        'next_states': ['archived'],
        'permissions': ['admin'],
        'auto_transition': True,  # 30 days after closing
        'notifications': ['job_closed_alert']
    },
    'cancelled': {
        'next_states': ['archived'],
        'permissions': ['admin'],
        'auto_transition': False,
        'notifications': ['job_cancelled_alert']
    },
    'archived': {
        'next_states': [],
        'permissions': ['admin'],
        'auto_transition': False
    }
}
```

#### Definition of Done:
- [ ] Status transitions working correctly
- [ ] Automatic status changes based on dates
- [ ] Access controls enforced by status
- [ ] Lifecycle notifications sent appropriately
- [ ] Job archiving and restoration functional
- [ ] Complete status audit trail maintained

---

## 🔄 Epic Dependencies

### Dependencies FROM other epics:
- **Epic 4**: RBAC System (requires admin/operator roles)
- **Epic 2**: Backend API Foundation (requires API structure)
- **Epic 1**: Docker Infrastructure (requires database)

### Dependencies TO other epics:
- **Epic 6**: Job Matching System (requires job data)
- **Epic 8**: Notification System (requires job updates)
- **Epic 9**: Admin Panel (requires job management APIs)

---

## 📈 Epic Progress Tracking

### Week 8 Goals:
- [ ] Stories 5.1, 5.2 completed
- [ ] Job model and creation working
- [ ] Basic job management operational

### Week 9 Goals:
- [ ] Stories 5.3, 5.4 completed
- [ ] Job listing and search functional
- [ ] Job detail views working

### Week 10 Goals:
- [ ] Story 5.5 completed
- [ ] Job update management working
- [ ] Bulk operations functional

### Week 11 Goals:
- [ ] Story 5.6 completed
- [ ] Job lifecycle automation active
- [ ] Full job management tested

---

## 🧪 Testing Strategy

### Unit Tests:
- Job model validation
- CRUD operation functions
- Status transition logic
- Search and filter functions

### Integration Tests:
- End-to-end job creation flow
- Job lifecycle automation
- Search performance tests
- Bulk operation tests

### Performance Tests:
- Job listing with large datasets
- Search query optimization
- Cache effectiveness
- Database index performance

---

## 📚 Documentation Requirements

### Technical Documentation:
- [ ] Job model schema documentation
- [ ] API endpoint documentation
- [ ] Job lifecycle documentation
- [ ] Search and filter documentation

### Administrative Documentation:
- [ ] Job creation guide
- [ ] Job management procedures
- [ ] Status management guide
- [ ] Bulk operation procedures

---

## ⚠️ Risks & Mitigation

### High Risk:
- **Performance degradation with large datasets**: Mitigation - Proper indexing, caching, pagination
- **Data validation bypass**: Mitigation - Comprehensive validation at multiple layers

### Medium Risk:
- **Job duplicate creation**: Mitigation - Duplicate detection algorithms
- **Status transition errors**: Mitigation - State machine validation

### Low Risk:
- **Cache inconsistency**: Mitigation - Smart cache invalidation strategies
- **File upload vulnerabilities**: Mitigation - File type validation, virus scanning

---

**Epic Owner**: Backend Development Team  
**Stakeholders**: Admin Users, Content Managers, End Users  
**Epic Status**: Not Started  
**Last Updated**: March 3, 2026