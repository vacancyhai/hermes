# Epic 11: Extended Portal Features (Sarkari Results)

## 🎯 Epic Overview

**Epic ID**: EPIC-011  
**Epic Title**: Extended Portal Features (Sarkari Results)  
**Epic Description**: Comprehensive result management system for government job examination results, admit cards, answer keys, and ranking/merit lists with advanced search and filtering capabilities.  
**Business Value**: Provides centralized platform for government exam results, increasing user engagement and establishing platform as comprehensive government job resource.  
**Priority**: MEDIUM  
**Estimated Timeline**: 3 weeks (Phase 6: Weeks 20-22)

## 📋 Epic Acceptance Criteria

- ✅ Complete result management system
- ✅ Admit card download functionality  
- ✅ Answer key publication system
- ✅ Merit list and ranking displays
- ✅ Advanced search and filtering for results
- ✅ Result notification system

## 📊 Epic Metrics

- **Story Count**: 5 stories
- **Story Points**: 36 (estimated)
- **Dependencies**: Epic 5 (Job Management), Epic 8 (Notifications)
- **Success Metrics**:
  - Result search accuracy >95%
  - Document download success rate >98%
  - Result notification delivery >95%
  - User satisfaction with result features >85%
  - Page load time for results <2 seconds

---

## 📝 User Stories

### Story 11.1: Result Management System

**Story ID**: EPIC-011-STORY-001  
**Story Title**: Result Management System  
**Priority**: HIGHEST  
**Story Points**: 8  
**Sprint**: Week 20

**As an** exam candidate  
**I want** to search and view examination results  
**So that** I can check my performance and qualification status

#### Acceptance Criteria:
- [ ] Result creation and management by admins
- [ ] Result search by exam name, date, organization
- [ ] Individual result checking with roll number/registration
- [ ] Result status tracking (declared, pending, cancelled)
- [ ] Bulk result upload from Excel/CSV
- [ ] Result publication scheduling

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/models/exam_result.py        # Result model
backend/app/models/candidate_result.py   # Individual result
backend/app/api/v1/routes/results.py     # Result API endpoints
backend/app/services/result_service.py   # Result business logic
backend/app/tasks/result_tasks.py        # Background result processing
backend/app/utils/result_parser.py       # Result file parsing
backend/app/validators/result_schemas.py  # Result validation
frontend/templates/pages/results/       # Result templates
frontend/static/js/result-search.js     # Result search functionality
```

#### Result Data Model:
```python
class ExamResult(db.Model):
    __tablename__ = 'exam_results'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_name = db.Column(db.String(200), nullable=False)
    organization = db.Column(db.String(100), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    result_date = db.Column(db.Date)
    status = db.Column(db.Enum('pending', 'declared', 'cancelled'), default='pending')
    result_type = db.Column(db.Enum('written', 'interview', 'final', 'preliminary'))
    
    # Result metadata
    total_candidates = db.Column(db.Integer)
    qualified_candidates = db.Column(db.Integer)
    cutoff_marks = db.Column(db.JSON)  # Category-wise cutoffs
    
    # File attachments
    result_file_url = db.Column(db.String(500))
    notification_url = db.Column(db.String(500))
    
    # Publishing control
    is_published = db.Column(db.Boolean, default=False)
    publish_date = db.Column(db.DateTime)
    
    # SEO and searchability
    seo_title = db.Column(db.String(200))
    seo_description = db.Column(db.Text)
    tags = db.Column(db.JSON)  # Search tags
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CandidateResult(db.Model):
    __tablename__ = 'candidate_results'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_result_id = db.Column(db.Integer, db.ForeignKey('exam_results.id'), nullable=False)
    
    # Candidate identification
    roll_number = db.Column(db.String(50), nullable=False)
    registration_number = db.Column(db.String(50))
    candidate_name = db.Column(db.String(100), nullable=False)
    
    # Result details
    total_marks = db.Column(db.Float)
    obtained_marks = db.Column(db.Float)
    percentage = db.Column(db.Float)
    rank = db.Column(db.Integer)
    category = db.Column(db.String(20))  # General, OBC, SC, ST, etc.
    
    # Qualification status
    is_qualified = db.Column(db.Boolean, default=False)
    qualification_status = db.Column(db.String(50))  # qualified, not_qualified, waiting_list
    
    # Subject-wise marks
    subject_marks = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Result Search API:
```python
@results_bp.route('/search', methods=['GET'])
def search_results():
    """Search exam results with filters"""
    query_params = request.args
    
    # Build search query
    results_query = ExamResult.query.filter(
        ExamResult.is_published == True
    )
    
    # Apply filters
    if query_params.get('exam_name'):
        results_query = results_query.filter(
            ExamResult.exam_name.ilike(f"%{query_params.get('exam_name')}%")
        )
    
    if query_params.get('organization'):
        results_query = results_query.filter(
            ExamResult.organization == query_params.get('organization')
        )
    
    if query_params.get('year'):
        year = int(query_params.get('year'))
        results_query = results_query.filter(
            db.extract('year', ExamResult.exam_date) == year
        )
    
    if query_params.get('month'):
        month = int(query_params.get('month'))
        results_query = results_query.filter(
            db.extract('month', ExamResult.exam_date) == month
        )
    
    # Pagination
    page = int(query_params.get('page', 1))
    per_page = int(query_params.get('per_page', 20))
    
    results = results_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'results': [format_result_summary(result) for result in results.items],
        'pagination': {
            'page': page,
            'pages': results.pages,
            'per_page': per_page,
            'total': results.total
        }
    })
```

#### Definition of Done:
- [ ] Result management system operational
- [ ] Search functionality with multiple filters
- [ ] Individual result checking working
- [ ] Bulk result upload functional
- [ ] Result publication scheduling active
- [ ] Performance optimized for large datasets

---

### Story 11.2: Admit Card Management & Download

**Story ID**: EPIC-011-STORY-002  
**Story Title**: Admit Card Management & Download  
**Priority**: HIGH  
**Story Points**: 7  
**Sprint**: Week 20-21

**As an** exam candidate  
**I want** to download my admit card  
**So that** I can appear for the examination

#### Acceptance Criteria:
- [ ] Admit card upload and management by admins
- [ ] Candidate admit card download with validation
- [ ] QR code generation for authenticity
- [ ] Download link sharing and notifications
- [ ] Exam-wise admit card organization
- [ ] Download analytics and tracking

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/models/admit_card.py         # Admit card model
backend/app/api/v1/routes/admit_cards.py # Admit card API
backend/app/services/admit_card_service.py # Admit card logic
backend/app/utils/pdf_generator.py       # PDF generation
backend/app/utils/qr_generator.py        # QR code generation
backend/app/tasks/admit_card_tasks.py    # Background processing
frontend/templates/pages/admit-cards/    # Admit card templates
frontend/static/js/admit-card.js         # Admit card functionality
```

#### Admit Card Model:
```python
class AdmitCard(db.Model):
    __tablename__ = 'admit_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    
    # Candidate details
    registration_number = db.Column(db.String(50), nullable=False, unique=True)
    candidate_name = db.Column(db.String(100), nullable=False)
    father_name = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    category = db.Column(db.String(20))
    
    # Exam details
    exam_center_code = db.Column(db.String(20))
    exam_center_name = db.Column(db.String(200))
    exam_center_address = db.Column(db.Text)
    exam_date = db.Column(db.Date)
    exam_time = db.Column(db.Time)
    reporting_time = db.Column(db.Time)
    
    # Document details
    photo_url = db.Column(db.String(500))
    signature_url = db.Column(db.String(500))
    
    # Authenticity and security
    qr_code_data = db.Column(db.Text)  # QR code content
    admit_card_number = db.Column(db.String(50), unique=True)
    security_hash = db.Column(db.String(256))
    
    # Download tracking
    download_count = db.Column(db.Integer, default=0)
    first_download_at = db.Column(db.DateTime)
    last_download_at = db.Column(db.DateTime)
    
    # Status and control
    is_active = db.Column(db.Boolean, default=True)
    download_start_date = db.Column(db.DateTime)
    download_end_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Admit Card Download Service:
```python
class AdmitCardService:
    
    @staticmethod
    def download_admit_card(registration_number, date_of_birth):
        """Download admit card with validation"""
        
        # Find admit card
        admit_card = AdmitCard.query.filter(
            AdmitCard.registration_number == registration_number,
            AdmitCard.date_of_birth == date_of_birth,
            AdmitCard.is_active == True
        ).first()
        
        if not admit_card:
            raise ValueError("Admit card not found or invalid details")
        
        # Check download window
        now = datetime.utcnow()
        if admit_card.download_start_date and now < admit_card.download_start_date:
            raise ValueError("Admit card download not yet available")
        
        if admit_card.download_end_date and now > admit_card.download_end_date:
            raise ValueError("Admit card download window has closed")
        
        # Generate QR code if not exists
        if not admit_card.qr_code_data:
            qr_data = {
                'registration_number': admit_card.registration_number,
                'exam_id': admit_card.exam_id,
                'candidate_name': admit_card.candidate_name,
                'exam_date': admit_card.exam_date.isoformat()
            }
            admit_card.qr_code_data = QRGenerator.generate_qr_code(qr_data)
            db.session.commit()
        
        # Update download tracking
        admit_card.download_count += 1
        if not admit_card.first_download_at:
            admit_card.first_download_at = now
        admit_card.last_download_at = now
        db.session.commit()
        
        # Generate PDF
        pdf_content = PDFGenerator.generate_admit_card_pdf(admit_card)
        
        # Send notification
        NotificationService.send_admit_card_download_confirmation(
            admit_card.registration_number
        )
        
        return pdf_content
    
    @staticmethod
    def bulk_upload_admit_cards(exam_id, admit_card_data):
        """Bulk upload admit cards from CSV/Excel"""
        
        created_cards = []
        errors = []
        
        for index, row in enumerate(admit_card_data):
            try:
                # Validate required fields
                required_fields = ['registration_number', 'candidate_name', 'date_of_birth']
                for field in required_fields:
                    if not row.get(field):
                        raise ValueError(f"Missing required field: {field}")
                
                # Create admit card
                admit_card = AdmitCard(
                    exam_id=exam_id,
                    registration_number=row['registration_number'],
                    candidate_name=row['candidate_name'],
                    father_name=row.get('father_name'),
                    date_of_birth=datetime.strptime(row['date_of_birth'], '%Y-%m-%d').date(),
                    category=row.get('category', 'General'),
                    exam_center_code=row.get('exam_center_code'),
                    exam_center_name=row.get('exam_center_name'),
                    exam_center_address=row.get('exam_center_address'),
                    exam_date=datetime.strptime(row['exam_date'], '%Y-%m-%d').date(),
                    exam_time=datetime.strptime(row['exam_time'], '%H:%M').time(),
                    reporting_time=datetime.strptime(row['reporting_time'], '%H:%M').time(),
                    admit_card_number=generate_admit_card_number()
                )
                
                db.session.add(admit_card)
                created_cards.append(admit_card)
                
            except Exception as e:
                errors.append({
                    'row': index + 1,
                    'error': str(e),
                    'data': row
                })
        
        if created_cards:
            db.session.commit()
        
        return {
            'created_count': len(created_cards),
            'error_count': len(errors),
            'errors': errors
        }
```

#### Definition of Done:
- [ ] Admit card management system operational
- [ ] Download with proper validation working
- [ ] QR code generation for security
- [ ] Bulk upload functionality complete
- [ ] Download analytics tracking active
- [ ] PDF generation working properly

---

### Story 11.3: Answer Key Publication System

**Story ID**: EPIC-011-STORY-003  
**Story Title**: Answer Key Publication System  
**Priority**: MEDIUM  
**Story Points**: 6  
**Sprint**: Week 21

**As an** exam candidate  
**I want** to view answer keys  
**So that** I can evaluate my performance

#### Acceptance Criteria:
- [ ] Answer key creation and management
- [ ] Multiple question paper sets support
- [ ] Answer key comparison and validation
- [ ] Objection/challenge submission system
- [ ] Provisional and final answer key versions
- [ ] Answer key download in multiple formats

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/models/answer_key.py         # Answer key model
backend/app/models/key_objection.py      # Objection model
backend/app/api/v1/routes/answer_keys.py # Answer key API
backend/app/services/answer_key_service.py # Answer key logic
backend/app/utils/answer_validator.py    # Answer validation
backend/app/tasks/objection_tasks.py     # Objection processing
frontend/templates/pages/answer-keys/    # Answer key templates
frontend/static/js/answer-key.js         # Answer key functionality
```

#### Answer Key Models:
```python
class AnswerKey(db.Model):
    __tablename__ = 'answer_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    
    # Answer key metadata
    question_paper_code = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100))
    version = db.Column(db.Enum('provisional', 'final'), default='provisional')
    
    # Answer data
    answers = db.Column(db.JSON)  # Question-wise answers
    total_questions = db.Column(db.Integer)
    marking_scheme = db.Column(db.JSON)  # Marking details
    
    # Publication details
    published_at = db.Column(db.DateTime)
    objection_deadline = db.Column(db.DateTime)
    is_published = db.Column(db.Boolean, default=False)
    
    # File attachments
    answer_key_pdf = db.Column(db.String(500))
    detailed_solution_pdf = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnswerKeyObjection(db.Model):
    __tablename__ = 'answer_key_objections'
    
    id = db.Column(db.Integer, primary_key=True)
    answer_key_id = db.Column(db.Integer, db.ForeignKey('answer_keys.id'), nullable=False)
    
    # Objection details
    question_number = db.Column(db.Integer, nullable=False)
    current_answer = db.Column(db.String(10))
    suggested_answer = db.Column(db.String(10))
    objection_reason = db.Column(db.Text, nullable=False)
    
    # Supporting documents
    supporting_documents = db.Column(db.JSON)  # File URLs
    
    # Objector details
    objector_name = db.Column(db.String(100))
    objector_email = db.Column(db.String(100))
    objector_phone = db.Column(db.String(20))
    
    # Processing status
    status = db.Column(db.Enum('submitted', 'under_review', 'accepted', 'rejected'), default='submitted')
    admin_response = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Answer Key Service:
```python
class AnswerKeyService:
    
    @staticmethod
    def publish_answer_key(answer_key_data):
        """Publish answer key with validation"""
        
        # Validate answer key data
        if not answer_key_data.get('answers'):
            raise ValueError("Answer data is required")
        
        # Create answer key
        answer_key = AnswerKey(**answer_key_data)
        answer_key.published_at = datetime.utcnow()
        answer_key.is_published = True
        
        db.session.add(answer_key)
        db.session.commit()
        
        # Generate PDF if not provided
        if not answer_key.answer_key_pdf:
            pdf_url = PDFGenerator.generate_answer_key_pdf(answer_key)
            answer_key.answer_key_pdf = pdf_url
            db.session.commit()
        
        # Send notifications
        NotificationService.send_answer_key_published_notification(answer_key)
        
        return answer_key
    
    @staticmethod
    def submit_objection(answer_key_id, objection_data):
        """Submit objection to answer key"""
        
        answer_key = AnswerKey.query.get_or_404(answer_key_id)
        
        # Check if objection deadline has passed
        if answer_key.objection_deadline and datetime.utcnow() > answer_key.objection_deadline:
            raise ValueError("Objection deadline has passed")
        
        # Create objection
        objection = AnswerKeyObjection(
            answer_key_id=answer_key_id,
            **objection_data
        )
        
        db.session.add(objection)
        db.session.commit()
        
        # Send confirmation email
        NotificationService.send_objection_confirmation(objection)
        
        return objection
    
    @staticmethod
    def process_objections(answer_key_id):
        """Process all objections for an answer key"""
        
        objections = AnswerKeyObjection.query.filter(
            AnswerKeyObjection.answer_key_id == answer_key_id,
            AnswerKeyObjection.status == 'submitted'
        ).all()
        
        processed_count = 0
        
        for objection in objections:
            # Auto-review based on common patterns
            if objection.objection_reason and len(objection.objection_reason) > 100:
                objection.status = 'under_review'
            else:
                objection.status = 'rejected'
                objection.admin_response = "Insufficient justification provided"
            
            objection.reviewed_at = datetime.utcnow()
            processed_count += 1
        
        db.session.commit()
        
        return processed_count
```

#### Definition of Done:
- [ ] Answer key publication system operational
- [ ] Multiple question paper sets supported
- [ ] Objection submission system working
- [ ] Answer key versions managed properly
- [ ] PDF generation for answer keys functional
- [ ] Notification system for answer keys active

---

### Story 11.4: Merit List & Ranking System

**Story ID**: EPIC-011-STORY-004  
**Story Title**: Merit List & Ranking System  
**Priority**: MEDIUM  
**Story Points**: 7  
**Sprint**: Week 21-22

**As an** exam candidate  
**I want** to view merit lists and rankings  
**So that** I can understand my position and selection chances

#### Acceptance Criteria:
- [ ] Category-wise merit list generation
- [ ] Rank calculation with tie-breaking rules
- [ ] Cut-off marks display
- [ ] Waiting list management
- [ ] Merit list download functionality
- [ ] Rank movement tracking

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/models/merit_list.py         # Merit list model
backend/app/services/ranking_service.py  # Ranking algorithms
backend/app/utils/cutoff_calculator.py   # Cut-off calculation
backend/app/tasks/merit_list_tasks.py    # Background processing
backend/app/api/v1/routes/merit_lists.py # Merit list API
frontend/templates/pages/merit-lists/    # Merit list templates
frontend/static/js/merit-list.js         # Merit list functionality
```

#### Merit List Model:
```python
class MeritList(db.Model):
    __tablename__ = 'merit_lists'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_result_id = db.Column(db.Integer, db.ForeignKey('exam_results.id'), nullable=False)
    
    # List metadata
    category = db.Column(db.String(20), nullable=False)  # General, OBC, SC, ST, EWS
    list_type = db.Column(db.Enum('main', 'waiting'), default='main')
    
    # Selection details
    total_vacancies = db.Column(db.Integer)
    selected_candidates = db.Column(db.Integer)
    cutoff_marks = db.Column(db.Float)
    cutoff_percentage = db.Column(db.Float)
    
    # List data
    merit_data = db.Column(db.JSON)  # Candidate ranking data
    
    # Publication details
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    
    # File attachments
    merit_list_pdf = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CandidateRanking(db.Model):
    __tablename__ = 'candidate_rankings'
    
    id = db.Column(db.Integer, primary_key=True)
    merit_list_id = db.Column(db.Integer, db.ForeignKey('merit_lists.id'), nullable=False)
    candidate_result_id = db.Column(db.Integer, db.ForeignKey('candidate_results.id'), nullable=False)
    
    # Ranking details
    overall_rank = db.Column(db.Integer)
    category_rank = db.Column(db.Integer)
    
    # Selection status
    selection_status = db.Column(db.Enum('selected', 'waiting_list', 'not_selected'))
    
    # Tie-breaking details
    tie_breaker_scores = db.Column(db.JSON)  # Date of birth, subject marks, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Ranking Service:
```python
class RankingService:
    
    @staticmethod
    def generate_merit_list(exam_result_id, vacancies_data):
        """Generate merit list with proper ranking"""
        
        # Get all qualified candidates
        candidates = CandidateResult.query.filter(
            CandidateResult.exam_result_id == exam_result_id,
            CandidateResult.is_qualified == True
        ).all()
        
        # Group by category
        category_groups = {}
        for candidate in candidates:
            category = candidate.category or 'General'
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(candidate)
        
        merit_lists = []
        
        for category, category_candidates in category_groups.items():
            # Sort candidates by marks (with tie-breaking)
            sorted_candidates = sorted(
                category_candidates,
                key=lambda c: (
                    -c.obtained_marks,  # Higher marks first
                    c.date_of_birth,    # Older candidates first (if tie)
                    -c.subject_marks.get('mathematics', 0)  # Math marks as tie-breaker
                )
            )
            
            # Calculate ranks
            for index, candidate in enumerate(sorted_candidates):
                candidate.rank = index + 1
            
            # Determine cutoffs
            vacancies = vacancies_data.get(category, 0)
            if vacancies > 0:
                cutoff_candidate = sorted_candidates[min(vacancies - 1, len(sorted_candidates) - 1)]
                cutoff_marks = cutoff_candidate.obtained_marks
            else:
                cutoff_marks = sorted_candidates[0].obtained_marks if sorted_candidates else 0
            
            # Create merit list
            merit_list = MeritList(
                exam_result_id=exam_result_id,
                category=category,
                total_vacancies=vacancies,
                selected_candidates=min(vacancies, len(sorted_candidates)),
                cutoff_marks=cutoff_marks,
                cutoff_percentage=(cutoff_marks / sorted_candidates[0].total_marks * 100) if sorted_candidates else 0,
                merit_data={
                    'candidates': [
                        {
                            'registration_number': c.registration_number,
                            'name': c.candidate_name,
                            'marks': c.obtained_marks,
                            'rank': c.rank,
                            'status': 'selected' if c.rank <= vacancies else 'waiting_list'
                        }
                        for c in sorted_candidates
                    ]
                }
            )
            
            db.session.add(merit_list)
            merit_lists.append(merit_list)
        
        db.session.commit()
        
        return merit_lists
    
    @staticmethod
    def calculate_waiting_list_probability(candidate_rank, category, total_vacancies):
        """Calculate probability of selection from waiting list"""
        
        if candidate_rank <= total_vacancies:
            return 100  # Already selected
        
        # Historical data-based calculation
        waiting_position = candidate_rank - total_vacancies
        
        # Probability decreases exponentially with waiting position
        if waiting_position <= 10:
            probability = max(0, 80 - (waiting_position * 8))
        elif waiting_position <= 25:
            probability = max(0, 40 - ((waiting_position - 10) * 2.5))
        else:
            probability = max(0, 5 - ((waiting_position - 25) * 0.2))
        
        return round(probability, 2)
```

#### Definition of Done:
- [ ] Merit list generation system operational
- [ ] Category-wise ranking working correctly
- [ ] Cut-off calculation automated
- [ ] Waiting list management functional
- [ ] Merit list download working
- [ ] Rank tracking system active

---

### Story 11.5: Advanced Search & Filtering for Results

**Story ID**: EPIC-011-STORY-005  
**Story Title**: Advanced Search & Filtering for Results  
**Priority**: MEDIUM  
**Story Points**: 8  
**Sprint**: Week 22

**As a** portal user  
**I want** advanced search capabilities  
**So that** I can quickly find specific results and information

#### Acceptance Criteria:
- [ ] Multi-criteria search functionality
- [ ] Auto-complete and suggestions
- [ ] Saved search preferences
- [ ] Search history and bookmarks
- [ ] Advanced filters for date, organization, type
- [ ] Search analytics and trending searches

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/services/search_service.py   # Advanced search logic
backend/app/models/search_history.py     # Search tracking
backend/app/utils/search_indexer.py      # Search indexing
backend/app/tasks/search_tasks.py        # Background search tasks
backend/app/api/v1/routes/search.py      # Search API endpoints
frontend/static/js/advanced-search.js    # Search functionality
frontend/templates/components/search/    # Search components
```

#### Advanced Search Service:
```python
class AdvancedSearchService:
    
    @staticmethod
    def search_results(query_params, user_id=None):
        """Perform advanced search with multiple filters"""
        
        # Parse search parameters
        search_text = query_params.get('q', '').strip()
        filters = {
            'organization': query_params.getlist('org'),
            'year': query_params.get('year'),
            'month': query_params.get('month'),
            'result_type': query_params.getlist('type'),
            'status': query_params.getlist('status'),
            'category': query_params.getlist('category')
        }
        
        # Build base query
        query = db.session.query(ExamResult).filter(
            ExamResult.is_published == True
        )
        
        # Text search
        if search_text:
            search_vector = func.to_tsvector('english', 
                ExamResult.exam_name + ' ' + 
                ExamResult.organization + ' ' + 
                func.coalesce(ExamResult.seo_description, '')
            )
            search_query = func.plainto_tsquery('english', search_text)
            
            query = query.filter(search_vector.match(search_query))
            
            # Add relevance scoring
            query = query.add_columns(
                func.ts_rank(search_vector, search_query).label('relevance')
            ).order_by(desc('relevance'))
        
        # Apply filters
        if filters['organization']:
            query = query.filter(ExamResult.organization.in_(filters['organization']))
        
        if filters['year']:
            query = query.filter(
                func.extract('year', ExamResult.exam_date) == int(filters['year'])
            )
        
        if filters['month']:
            query = query.filter(
                func.extract('month', ExamResult.exam_date) == int(filters['month'])
            )
        
        if filters['result_type']:
            query = query.filter(ExamResult.result_type.in_(filters['result_type']))
        
        if filters['status']:
            query = query.filter(ExamResult.status.in_(filters['status']))
        
        # Execute query with pagination
        page = int(query_params.get('page', 1))
        per_page = min(int(query_params.get('per_page', 20)), 100)
        
        results = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Track search history
        if user_id and search_text:
            SearchService.track_search_history(user_id, search_text, filters)
        
        return {
            'results': [format_search_result(r) for r in results.items],
            'pagination': {
                'page': page,
                'pages': results.pages,
                'per_page': per_page,
                'total': results.total
            },
            'filters_applied': {k: v for k, v in filters.items() if v},
            'search_suggestions': SearchService.get_search_suggestions(search_text)
        }
    
    @staticmethod
    def get_search_suggestions(partial_query):
        """Get auto-complete suggestions"""
        
        if len(partial_query) < 2:
            return []
        
        # Search in exam names and organizations
        suggestions = db.session.query(
            ExamResult.exam_name,
            ExamResult.organization,
            func.count().label('frequency')
        ).filter(
            or_(
                ExamResult.exam_name.ilike(f'%{partial_query}%'),
                ExamResult.organization.ilike(f'%{partial_query}%')
            ),
            ExamResult.is_published == True
        ).group_by(
            ExamResult.exam_name,
            ExamResult.organization
        ).order_by(
            desc('frequency')
        ).limit(10).all()
        
        formatted_suggestions = []
        for suggestion in suggestions:
            if partial_query.lower() in suggestion.exam_name.lower():
                formatted_suggestions.append({
                    'text': suggestion.exam_name,
                    'type': 'exam',
                    'frequency': suggestion.frequency
                })
            if partial_query.lower() in suggestion.organization.lower():
                formatted_suggestions.append({
                    'text': suggestion.organization,
                    'type': 'organization',
                    'frequency': suggestion.frequency
                })
        
        return sorted(formatted_suggestions, key=lambda x: x['frequency'], reverse=True)[:5]
    
    @staticmethod
    def get_trending_searches():
        """Get trending search queries"""
        
        # Get searches from last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        trending = db.session.query(
            SearchHistory.search_query,
            func.count().label('search_count')
        ).filter(
            SearchHistory.created_at >= week_ago,
            SearchHistory.search_query.isnot(None)
        ).group_by(
            SearchHistory.search_query
        ).order_by(
            desc('search_count')
        ).limit(10).all()
        
        return [
            {
                'query': trend.search_query,
                'count': trend.search_count
            }
            for trend in trending
        ]
```

#### Search History Model:
```python
class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Search details
    search_query = db.Column(db.String(500))
    filters_applied = db.Column(db.JSON)
    results_count = db.Column(db.Integer)
    
    # User interaction
    clicked_results = db.Column(db.JSON)  # Track which results were clicked
    search_session_id = db.Column(db.String(100))
    
    # Analytics
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Definition of Done:
- [ ] Advanced search with multiple criteria working
- [ ] Auto-complete suggestions functional
- [ ] Search history tracking operational
- [ ] Saved search preferences working
- [ ] Advanced filters applied correctly
- [ ] Search analytics collecting data

---

## 🔄 Epic Dependencies

### Dependencies FROM other epics:
- **Epic 5**: Job Management (requires job/exam data model)
- **Epic 8**: Notification System (requires notification for results)
- **Epic 9**: Admin Panel (requires admin interface for result management)

### Dependencies TO other epics:
- **Epic 12**: Performance Optimization (requires result search optimization)

---

## 📈 Epic Progress Tracking

### Week 20 Goals:
- [ ] Stories 11.1, 11.2 started
- [ ] Result management system operational
- [ ] Admit card management functional

### Week 21 Goals:
- [ ] Stories 11.2, 11.3 completed
- [ ] Answer key publication system working
- [ ] Merit list generation operational

### Week 22 Goals:
- [ ] Stories 11.4, 11.5 completed
- [ ] Advanced search functionality complete
- [ ] All result features fully operational

---

## 🧪 Testing Strategy

### Unit Tests:
- Result parsing and validation
- Ranking algorithm accuracy
- Search functionality precision
- Merit list calculation correctness

### Integration Tests:
- End-to-end result publication workflow
- Search performance with large datasets
- Multi-user concurrent access
- File download functionality

### Performance Tests:
- Large result dataset handling
- Search response time optimization
- Concurrent user load testing
- Database query performance

---

## 📚 Documentation Requirements

### Technical Documentation:
- [ ] Result management system architecture
- [ ] Search algorithm documentation
- [ ] Merit list calculation procedures
- [ ] API documentation for all endpoints

### User Documentation:
- [ ] Result search guide
- [ ] Admit card download instructions
- [ ] Merit list interpretation guide
- [ ] FAQ for common result queries

---

## ⚠️ Risks & Mitigation

### High Risk:
- **Large dataset performance**: Mitigation - Database optimization, caching, pagination
- **Result accuracy**: Mitigation - Multiple validation layers, audit trails

### Medium Risk:
- **Search performance degradation**: Mitigation - Full-text search indexes, query optimization
- **File storage costs**: Mitigation - Efficient file compression, CDN usage

### Low Risk:
- **User interface complexity**: Mitigation - Progressive disclosure, user testing
- **Mobile responsiveness**: Mitigation - Mobile-first design approach

---

**Epic Owner**: Backend Development Team, Data Team  
**Stakeholders**: Government Organizations, Exam Candidates, Operations Team  
**Epic Status**: Not Started  
**Last Updated**: March 3, 2026