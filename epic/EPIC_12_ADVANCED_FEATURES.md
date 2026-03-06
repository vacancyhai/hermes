# Epic 12: Advanced Features & Performance Optimization

## 🎯 Epic Overview

**Epic ID**: EPIC-012  
**Epic Title**: Advanced Features & Performance Optimization  
**Epic Description**: Implementation of advanced performance optimization, caching strategies, real-time features, and enhanced security measures to ensure the platform operates at peak efficiency and security.  
**Business Value**: Delivers enterprise-grade performance, scalability, and security that enables the platform to handle high traffic loads while maintaining excellent user experience and data protection.  
**Priority**: MEDIUM  
**Estimated Timeline**: 5 weeks (Phase 6: Weeks 20-24)

## 📋 Epic Acceptance Criteria

- ✅ Redis caching system with intelligent cache invalidation
- ✅ Elasticsearch integration for advanced search capabilities
- ✅ Real-time features using WebSockets
- ✅ Advanced security features and threat protection
- ✅ System scalability and load handling

## 📊 Epic Metrics & Timeline Note

- **Story Count**: 5 stories
- **Story Points**: 45 (estimated)
- **Dependencies**: All previous epics (1-11)
- **⚠️ TIMELINE REALITY CHECK**: 
  - Currently scheduled for Weeks 20-24 (final phase)
  - HOWEVER: Security & Caching SHOULD START EARLIER
  - **RECOMMENDED REPLAN**: Start Stories 12.1-12.2 in Weeks 13-15 (Phase 4)
  - Reason: Cannot wait until end - need these features when API goes live
  - Security must be parallel with development, not deferred
  - Caching optimization needed after API stability (~Week 10+)
- **Success Metrics**:
  - API response time <100ms (p95) with cache
  - Search query performance <50ms
  - Real-time message latency <200ms
  - System uptime >99.9%
  - Security scan score >95/100

---

## 📝 User Stories

### Story 12.1: Redis Caching System

**Story ID**: EPIC-012-STORY-001  
**Story Title**: Redis Caching System  
**Priority**: HIGHEST  
**Story Points**: 10  
**Sprint**: Week 20-21

**As a** platform user  
**I want** fast response times  
**So that** I can browse jobs quickly without delays

#### Acceptance Criteria:
- [ ] Redis cache layer for frequently accessed data
- [ ] Intelligent cache invalidation strategies
- [ ] Cache warming on system startup
- [ ] TTL management for different data types
- [ ] Cache stampede prevention

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/cache/__init__.py              # Cache module
backend/app/cache/redis_client.py          # Redis connection management
backend/app/cache/cache_manager.py         # Cache operations
backend/app/cache/decorators.py            # Cache decorators
backend/app/cache/strategies.py            # Cache strategies
backend/app/cache/invalidation.py          # Cache invalidation
backend/app/tasks/cache_tasks.py           # Cache warming tasks
backend/app/middleware/cache_middleware.py # HTTP cache headers
```

#### Cache Strategy by Data Type:
```python
CACHE_STRATEGIES = {
    # Hot data - frequently accessed
    'job_listings': {
        'ttl': 300,  # 5 minutes
        'strategy': 'lazy_load',
        'invalidate_on': ['job_create', 'job_update', 'job_delete']
    },
    'job_detail': {
        'ttl': 600,  # 10 minutes
        'strategy': 'lazy_load',
        'invalidate_on': ['job_update', 'job_delete']
    },
    'user_profile': {
        'ttl': 1800,  # 30 minutes
        'strategy': 'write_through',
        'invalidate_on': ['profile_update']
    },
    
    # Static data - rarely changes
    'categories': {
        'ttl': 86400,  # 24 hours
        'strategy': 'cache_aside',
        'warm_on_startup': True
    },
    'organizations': {
        'ttl': 86400,  # 24 hours
        'strategy': 'cache_aside',
        'warm_on_startup': True
    },
    
    # Session data
    'user_sessions': {
        'ttl': 3600,  # 1 hour
        'strategy': 'write_through'
    },
    
    # Computed data
    'job_matches': {
        'ttl': 600,  # 10 minutes
        'strategy': 'lazy_load',
        'invalidate_on': ['profile_update', 'job_create']
    },
    'analytics': {
        'ttl': 1800,  # 30 minutes
        'strategy': 'lazy_load'
    }
}
```

#### Cache Invalidation Patterns:
```python
# Event-driven invalidation
@event_listener('job_created')
def invalidate_job_caches(job_data):
    cache.delete_pattern('job_listings:*')
    cache.delete_pattern('search_results:*')
    cache.delete('stats:total_jobs')

# Time-based invalidation (automatic via TTL)
cache.setex('job:123', ttl=300, value=json.dumps(job_data))

# Manual invalidation
@admin_required
def clear_all_cache():
    cache.flushdb()
```

#### Performance Optimization Techniques:
```python
# 1. Cache aside pattern (lazy loading)
def get_job_by_id(job_id):
    cache_key = f'job:{job_id}'
    cached_job = cache.get(cache_key)
    
    if cached_job:
        return json.loads(cached_job)
    
    job = Job.objects.get(id=job_id)
    cache.setex(cache_key, 600, json.dumps(job.to_dict()))
    return job

# 2. Write-through pattern
def update_user_profile(user_id, data):
    user = User.objects.get(id=user_id)
    user.update(**data)
    
    cache_key = f'user:{user_id}'
    cache.setex(cache_key, 1800, json.dumps(user.to_dict()))
    return user

# 3. Cache warming on startup
def warm_cache():
    # Load frequently accessed data
    categories = Category.objects.all()
    for cat in categories:
        cache.setex(f'category:{cat.id}', 86400, cat.to_json())
    
    organizations = Organization.objects.all()
    for org in organizations:
        cache.setex(f'org:{org.id}', 86400, org.to_json())

# 4. Cache stampede prevention (using mutex)
def get_expensive_data(key):
    data = cache.get(key)
    if data:
        return data
    
    # Try to acquire lock
    lock_key = f'lock:{key}'
    if cache.set(lock_key, '1', nx=True, ex=10):
        try:
            # First request fetches data
            data = compute_expensive_data()
            cache.setex(key, 300, data)
            return data
        finally:
            cache.delete(lock_key)
    else:
        # Other requests wait and retry
        time.sleep(0.1)
        return get_expensive_data(key)
```

#### Definition of Done:
- [ ] Redis cache client configured and tested
- [ ] Cache decorators working for API endpoints
- [ ] Cache invalidation triggers implemented
- [ ] Cache warming on startup functional
- [ ] Cache hit rate >80% for hot data
- [ ] Cache stampede prevention working

---

### Story 12.2: Elasticsearch Integration

**Story ID**: EPIC-012-STORY-002  
**Story Title**: Elasticsearch Integration  
**Priority**: HIGH  
**Story Points**: 10  
**Sprint**: Week 21-22

**As a** user  
**I want** powerful search capabilities  
**So that** I can find relevant jobs quickly with advanced filters

#### Acceptance Criteria:
- [ ] Elasticsearch cluster setup and configuration
- [ ] Full-text search across job descriptions
- [ ] Faceted search with filters
- [ ] Auto-suggest and typeahead search
- [ ] Search analytics and query logging
- [ ] Real-time indexing of new jobs
- [ ] Search result relevance scoring

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/search/__init__.py              # Search module
backend/app/search/elasticsearch_client.py  # ES connection
backend/app/search/indexer.py               # Document indexing
backend/app/search/query_builder.py         # Query construction
backend/app/search/aggregations.py          # Faceted search
backend/app/search/analyzers.py             # Custom analyzers
backend/app/api/v1/routes/search.py         # Search endpoints
backend/app/tasks/search_tasks.py           # Async indexing
```

#### Elasticsearch Index Mapping:
```json
{
  "job_vacancies": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 2,
      "analysis": {
        "analyzer": {
          "job_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": ["lowercase", "stop", "snowball"]
          },
          "autocomplete_analyzer": {
            "type": "custom",
            "tokenizer": "edge_ngram_tokenizer",
            "filter": ["lowercase"]
          }
        },
        "tokenizer": {
          "edge_ngram_tokenizer": {
            "type": "edge_ngram",
            "min_gram": 2,
            "max_gram": 10,
            "token_chars": ["letter", "digit"]
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "job_id": {"type": "keyword"},
        "title": {
          "type": "text",
          "analyzer": "job_analyzer",
          "fields": {
            "keyword": {"type": "keyword"},
            "autocomplete": {
              "type": "text",
              "analyzer": "autocomplete_analyzer"
            }
          }
        },
        "organization": {
          "type": "text",
          "analyzer": "job_analyzer",
          "fields": {"keyword": {"type": "keyword"}}
        },
        "description": {
          "type": "text",
          "analyzer": "job_analyzer"
        },
        "category": {"type": "keyword"},
        "job_type": {"type": "keyword"},
        "location": {
          "type": "text",
          "fields": {"keyword": {"type": "keyword"}}
        },
        "salary_min": {"type": "integer"},
        "salary_max": {"type": "integer"},
        "eligibility": {
          "properties": {
            "qualification": {"type": "keyword"},
            "min_age": {"type": "integer"},
            "max_age": {"type": "integer"}
          }
        },
        "application_deadline": {"type": "date"},
        "created_at": {"type": "date"},
        "status": {"type": "keyword"},
        "tags": {"type": "keyword"}
      }
    }
  }
}
```

#### Advanced Search Queries:
```python
# 1. Full-text search with filters
def search_jobs(query, filters=None):
    must_clauses = []
    
    # Text search
    if query:
        must_clauses.append({
            "multi_match": {
                "query": query,
                "fields": ["title^3", "organization^2", "description"],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        })
    
    # Apply filters
    filter_clauses = []
    if filters:
        if filters.get('category'):
            filter_clauses.append({"term": {"category": filters['category']}})
        if filters.get('job_type'):
            filter_clauses.append({"term": {"job_type": filters['job_type']}})
        if filters.get('location'):
            filter_clauses.append({"term": {"location.keyword": filters['location']}})
        if filters.get('salary_min'):
            filter_clauses.append({"range": {"salary_max": {"gte": filters['salary_min']}}})
    
    search_body = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        },
        "sort": [
            {"_score": "desc"},
            {"created_at": "desc"}
        ]
    }
    
    return es.search(index="job_vacancies", body=search_body)

# 2. Faceted search (aggregations)
def get_search_facets():
    agg_body = {
        "aggs": {
            "categories": {
                "terms": {"field": "category", "size": 20}
            },
            "job_types": {
                "terms": {"field": "job_type", "size": 10}
            },
            "organizations": {
                "terms": {"field": "organization.keyword", "size": 50}
            },
            "locations": {
                "terms": {"field": "location.keyword", "size": 100}
            },
            "salary_ranges": {
                "range": {
                    "field": "salary_max",
                    "ranges": [
                        {"to": 30000, "key": "0-30k"},
                        {"from": 30000, "to": 50000, "key": "30k-50k"},
                        {"from": 50000, "to": 100000, "key": "50k-100k"},
                        {"from": 100000, "key": "100k+"}
                    ]
                }
            }
        }
    }
    
    return es.search(index="job_vacancies", body=agg_body, size=0)

# 3. Auto-suggest (typeahead)
def autocomplete_search(prefix):
    body = {
        "query": {
            "multi_match": {
                "query": prefix,
                "fields": ["title.autocomplete", "organization.autocomplete"],
                "type": "phrase_prefix"
            }
        },
        "size": 10
    }
    
    return es.search(index="job_vacancies", body=body)

# 4. Search suggestions (did you mean?)
def search_suggestions(query):
    body = {
        "suggest": {
            "text": query,
            "title_suggest": {
                "term": {
                    "field": "title",
                    "suggest_mode": "always"
                }
            }
        }
    }
    
    return es.search(index="job_vacancies", body=body)
```

#### Real-time Indexing:
```python
# Index on job creation
@signal_handler('job_created')
def index_new_job(job):
    es.index(
        index='job_vacancies',
        id=str(job.id),
        document=job.to_search_dict()
    )

# Update index on job update
@signal_handler('job_updated')
def update_job_index(job):
    es.update(
        index='job_vacancies',
        id=str(job.id),
        doc=job.to_search_dict()
    )

# Remove from index on job delete
@signal_handler('job_deleted')
def remove_from_index(job_id):
    es.delete(index='job_vacancies', id=str(job_id))

# Bulk indexing for existing data
def reindex_all_jobs():
    jobs = Job.objects.filter(status='active').all()
    bulk_data = []
    
    for job in jobs:
        bulk_data.append({
            "index": {
                "_index": "job_vacancies",
                "_id": str(job.id)
            }
        })
        bulk_data.append(job.to_search_dict())
    
    es.bulk(body=bulk_data)
```

#### Definition of Done:
- [ ] Elasticsearch cluster operational
- [ ] Index mapping created and optimized
- [ ] Full-text search working with relevance scoring
- [ ] Faceted search filters functional
- [ ] Auto-suggest providing real-time suggestions
- [ ] Real-time indexing operational
- [ ] Search performance <50ms for p95
- [ ] Search analytics tracking queries

---

### Story 12.3: Real-time Features with WebSockets

**Story ID**: EPIC-012-STORY-003  
**Story Title**: Real-time Features with WebSockets  
**Priority**: MEDIUM  
**Story Points**: 8  
**Sprint**: Week 22-23

**As a** user  
**I want** real-time updates  
**So that** I see new notifications and job postings instantly

#### Acceptance Criteria:
- [ ] WebSocket server implementation
- [ ] Real-time notification delivery
- [ ] Live job posting updates
- [ ] Connection management and reconnection
- [ ] Room-based broadcasting
- [ ] Message queue for offline users

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/websocket/__init__.py           # WebSocket module
backend/app/websocket/server.py             # Socket.IO server
backend/app/websocket/handlers.py           # Event handlers
backend/app/websocket/rooms.py              # Room management
backend/app/websocket/middleware.py         # Auth middleware
backend/app/tasks/broadcast_tasks.py        # Broadcast tasks
frontend/static/js/websocket_client.js      # Client implementation
```

#### WebSocket Server Setup:
```python
# backend/app/websocket/server.py
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from app.utils.jwt_utils import verify_token

socketio = SocketIO(cors_allowed_origins="*", message_queue='redis://')

# Authentication middleware
@socketio.on('connect')
def handle_connect(auth):
    token = auth.get('token')
    if not token:
        return False
    
    try:
        user_data = verify_token(token)
        request.user_id = user_data['user_id']
        
        # Join user's personal room
        join_room(f"user_{user_data['user_id']}")
        
        emit('connected', {'message': 'Successfully connected'})
        return True
    except:
        return False

# Disconnect handler
@socketio.on('disconnect')
def handle_disconnect():
    if hasattr(request, 'user_id'):
        leave_room(f"user_{request.user_id}")

# Subscribe to job alerts
@socketio.on('subscribe_job_alerts')
def handle_subscribe(data):
    categories = data.get('categories', [])
    for category in categories:
        join_room(f"jobs_{category}")
    emit('subscribed', {'categories': categories})

# Unsubscribe from job alerts
@socketio.on('unsubscribe_job_alerts')
def handle_unsubscribe(data):
    categories = data.get('categories', [])
    for category in categories:
        leave_room(f"jobs_{category}")
    emit('unsubscribed', {'categories': categories})
```

#### Real-time Event Broadcasting:
```python
# backend/app/tasks/broadcast_tasks.py
from app.websocket.server import socketio
from celery import shared_task

# Broadcast new job posting
@shared_task
def broadcast_new_job(job_data):
    socketio.emit(
        'new_job',
        {'job': job_data},
        room=f"jobs_{job_data['category']}"
    )

# Send real-time notification to user
@shared_task
def send_realtime_notification(user_id, notification):
    socketio.emit(
        'notification',
        notification,
        room=f"user_{user_id}"
    )

# Broadcast system announcement
@shared_task
def broadcast_announcement(message):
    socketio.emit(
        'system_announcement',
        {'message': message},
        broadcast=True
    )

# Update job status in real-time
@shared_task
def broadcast_job_update(job_id, updates):
    socketio.emit(
        'job_updated',
        {'job_id': job_id, 'updates': updates},
        room=f"job_{job_id}"
    )
```

#### Client-side Implementation:
```javascript
// frontend/static/js/websocket_client.js
class HermesWebSocket {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect(token) {
        this.socket = io('wss://api.hermes.com', {
            auth: { token: token },
            transports: ['websocket'],
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000
        });
        
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        // Connection events
        this.socket.on('connected', (data) => {
            console.log('WebSocket connected:', data);
            this.reconnectAttempts = 0;
        });
        
        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.handleReconnect();
        });
        
        // Real-time notifications
        this.socket.on('notification', (notification) => {
            this.showNotification(notification);
        });
        
        // New job postings
        this.socket.on('new_job', (data) => {
            this.appendJobToList(data.job);
            this.showToast(`New job posted: ${data.job.title}`);
        });
        
        // Job updates
        this.socket.on('job_updated', (data) => {
            this.updateJobInList(data.job_id, data.updates);
        });
        
        // System announcements
        this.socket.on('system_announcement', (data) => {
            this.showSystemAnnouncement(data.message);
        });
    }
    
    subscribeToJobAlerts(categories) {
        this.socket.emit('subscribe_job_alerts', {
            categories: categories
        });
    }
    
    unsubscribeFromJobAlerts(categories) {
        this.socket.emit('unsubscribe_job_alerts', {
            categories: categories
        });
    }
    
    showNotification(notification) {
        // Create notification UI element
        const notifElement = document.createElement('div');
        notifElement.className = 'notification toast';
        notifElement.innerHTML = `
            <div class="notification-icon">${notification.icon}</div>
            <div class="notification-content">
                <h4>${notification.title}</h4>
                <p>${notification.message}</p>
            </div>
        `;
        
        document.getElementById('notification-container').appendChild(notifElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => notifElement.remove(), 5000);
    }
    
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnection attempt ${this.reconnectAttempts}`);
        } else {
            console.error('Max reconnection attempts reached');
            this.showReconnectionError();
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Initialize WebSocket connection
const wsClient = new HermesWebSocket();
const token = localStorage.getItem('auth_token');
if (token) {
    wsClient.connect(token);
}
```

#### Performance Optimization:
```python
# Message queue for offline users
class MessageQueue:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def queue_message(self, user_id, message):
        key = f"offline_messages:{user_id}"
        self.redis.lpush(key, json.dumps(message))
        self.redis.expire(key, 86400)  # 24 hours
    
    def get_queued_messages(self, user_id):
        key = f"offline_messages:{user_id}"
        messages = self.redis.lrange(key, 0, -1)
        self.redis.delete(key)
        return [json.loads(msg) for msg in messages]

# Send queued messages on connect
@socketio.on('connect')
def send_queued_messages():
    if hasattr(request, 'user_id'):
        queue = MessageQueue(redis_client)
        messages = queue.get_queued_messages(request.user_id)
        for msg in messages:
            emit('queued_message', msg)
```

#### Definition of Done:
- [ ] WebSocket server operational
- [ ] Client connection and authentication working
- [ ] Real-time notifications delivered instantly
- [ ] Job posting updates broadcast in real-time
- [ ] Reconnection logic handling disconnects
- [ ] Message queue for offline users functional
- [ ] Connection latency <200ms
- [ ] Load testing completed for 10k concurrent connections


---

### Story 12.5: Advanced Security Features

**Story ID**: EPIC-012-STORY-005  
**Story Title**: Advanced Security Features  
**Priority**: HIGH  
**Story Points**: 8  
**Sprint**: Week 24

**As a** platform owner  
**I want** advanced security measures  
**So that** user data is protected from threats

#### Acceptance Criteria:
- [ ] Rate limiting and DDoS protection
- [ ] SQL/NoSQL injection prevention
- [ ] XSS and CSRF protection
- [ ] Security headers implementation
- [ ] API key management system
- [ ] Security audit logging
- [ ] Vulnerability scanning integration

#### Technical Implementation Tasks:
```python
# Files to implement:
backend/app/security/__init__.py            # Security module
backend/app/security/rate_limiter.py        # Rate limiting
backend/app/security/input_sanitizer.py     # Input sanitization
backend/app/security/encryption.py          # Data encryption
backend/app/security/api_keys.py            # API key management
backend/app/security/csrf_protection.py     # CSRF tokens
backend/app/middleware/security.py          # Security middleware
backend/app/models/security_audit.py        # Audit logging
```

#### Rate Limiting Implementation:
```python
# backend/app/security/rate_limiter.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis

redis_client = Redis(host='redis', port=6379, db=1)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis:6379/1",
    default_limits=["1000 per hour", "100 per minute"]
)

# Per-endpoint rate limits
@app.route('/api/v1/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Prevent brute force
def login():
    pass

@app.route('/api/v1/auth/register', methods=['POST'])
@limiter.limit("3 per hour")  # Prevent spam registrations
def register():
    pass

@app.route('/api/v1/jobs', methods=['GET'])
@limiter.limit("100 per minute")  # Public endpoint
def get_jobs():
    pass

# Dynamic rate limiting based on user tier
def get_user_limit():
    user_id = g.get('user_id')
    if not user_id:
        return "100 per hour"  # Anonymous users
    
    user = User.get(user_id)
    if user.is_premium:
        return "10000 per hour"  # Premium users
    return "1000 per hour"  # Regular users

@app.route('/api/v1/search')
@limiter.limit(get_user_limit)
def search():
    pass
```

#### Input Sanitization:
```python
# backend/app/security/input_sanitizer.py
import bleach
import re
from markupsafe import escape

class InputSanitizer:
    # Allowed HTML tags for rich text
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
    ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
    
    @staticmethod
    def sanitize_html(text):
        """Remove dangerous HTML/JavaScript"""
        if not text:
            return text
        return bleach.clean(
            text,
            tags=InputSanitizer.ALLOWED_TAGS,
            attributes=InputSanitizer.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def sanitize_string(text):
        """Basic string sanitization"""
        if not text:
            return text
        # Remove null bytes
        text = text.replace('\x00', '')
        # Escape HTML
        return escape(text)
    
    @staticmethod
    def validate_sql_identifier(identifier):
        """Prevent SQL injection via identifiers (column names, table names)"""
        # Only allow alphanumeric and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', identifier):
            raise ValueError(f"Invalid SQL identifier: {identifier}")
        return identifier
    
    @staticmethod
    def validate_sql_value(value):
        """SQLAlchemy automatically parameterizes queries - use ORM methods"""
        # Never concatenate user input into SQL strings
        # Always use SQLAlchemy's query builder or parameterized queries
        if isinstance(value, str):
            # Check for common SQL injection patterns
            dangerous_patterns = ['--', '/*', '*/', 'xp_', 'sp_', ';']
            for pattern in dangerous_patterns:
                if pattern.lower() in value.lower():
                    raise ValueError(f"Dangerous SQL pattern detected: {pattern}")
        return value
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("Invalid email format")
        return email.lower()
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number"""
        # Remove non-digits
        phone = re.sub(r'\D', '', phone)
        if len(phone) < 10 or len(phone) > 15:
            raise ValueError("Invalid phone number")
        return phone

# Apply sanitization decorator
from functools import wraps

def sanitize_input(fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            for field in fields:
                if field in data:
                    data[field] = InputSanitizer.sanitize_string(data[field])
            request._cached_json = data
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@app.route('/api/v1/profile', methods=['PUT'])
@sanitize_input(['full_name', 'bio', 'address'])
def update_profile():
    data = request.get_json()
    # Data is now sanitized
    pass
```

#### Security Headers Middleware:
```python
# backend/app/middleware/security.py
class SecurityHeadersMiddleware:
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        app.after_request(self.add_security_headers)
    
    def add_security_headers(self, response):
        # PreventClickJacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # XSS Protection
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss:;"
        )
        
        # HSTS (HTTP Strict Transport Security)
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains'
        )
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=()'
        )
        
        return response
```

#### API Key Management:
```python
# backend/app/security/api_keys.py
import secrets
import hashlib
from datetime import datetime, timedelta

class APIKeyManager:
    @staticmethod
    def generate_api_key():
        """Generate cryptographically secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key):
        """Hash API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def create_api_key(user_id, name, permissions=None):
        """Create new API key for user"""
        api_key = APIKeyManager.generate_api_key()
        api_key_hash = APIKeyManager.hash_api_key(api_key)
        
        key_record = APIKey(
            user_id=user_id,
            name=name,
            key_hash=api_key_hash,
            permissions=permissions or [],
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365)
        )
        key_record.save()
        
        # Return unhashed key only once
        return api_key, key_record.id
    
    @staticmethod
    def validate_api_key(api_key):
        """Validate API key and return associated user"""
        api_key_hash = APIKeyManager.hash_api_key(api_key)
        
        key_record = APIKey.objects(
            key_hash=api_key_hash,
            is_active=True,
            expires_at__gt=datetime.utcnow()
        ).first()
        
        if not key_record:
            return None
        
        # Update last used timestamp
        key_record.update(last_used_at=datetime.utcnow())
        
        return key_record

# API Key authentication decorator
def require_api_key(permissions=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            key_record = APIKeyManager.validate_api_key(api_key)
            if not key_record:
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Check permissions
            if permissions and not set(permissions).issubset(set(key_record.permissions)):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            g.api_key = key_record
            g.user_id = key_record.user_id
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@app.route('/api/v1/jobs/create', methods=['POST'])
@require_api_key(permissions=['jobs:write'])
def create_job_via_api():
    pass
```

#### Security Audit Logging:
```python
# backend/app/models/security_audit.py
class SecurityAudit(Document):
    event_type = StringField(required=True)  # login, logout, permission_change, etc.
    user_id = ObjectIdField()
    ip_address = StringField()
    user_agent = StringField()
    request_method = StringField()
    request_path = StringField()
    status_code = IntField()
    details = DictField()
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'security_audits',
        'indexes': [
            'user_id',
            'event_type',
            'created_at',
            {'fields': ['created_at'], 'expireAfterSeconds': 7776000}  # 90 days
        ]
    }

# Audit logging decorator
def audit_log(event_type):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)
            
            SecurityAudit(
                event_type=event_type,
                user_id=g.get('user_id'),
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                request_method=request.method,
                request_path=request.path,
                status_code=getattr(result, 'status_code', 200),
                details={
                    'request_id': g.get('request_id'),
                    'data': request.get_json() if request.is_json else {}
                }
            ).save()
            
            return result
        return decorated_function
    return decorator

# Usage
@app.route('/api/v1/auth/login', methods=['POST'])
@audit_log('login_attempt')
def login():
    pass

@app.route('/api/v1/admin/users/<user_id>/role', methods=['PUT'])
@audit_log('role_change')
@admin_required
def change_user_role(user_id):
    pass
```

#### Definition of Done:
- [ ] Rate limiting preventing abuse
- [ ] Input sanitization blocking injection attacks
- [ ] Security headers properly configured
- [ ] API key management system operational
- [ ] CSRF protection implemented
- [ ] Security audit logging tracking all events
- [ ] Vulnerability scanning passing all checks
- [ ] Security score >95/100 on external audit

---

## 🎯 Epic Summary

### Key Deliverables:
1. **Redis Caching**: 80%+ cache hit rate, <100ms API responses
2. **Elasticsearch**: Full-text search with <50ms query time
3. **WebSockets**: Real-time notifications with <200ms latency
4. **APM**: Complete observability with distributed tracing
5. **Security**: Enterprise-grade protection with 99.9% threat prevention

### Performance Targets:
- API Response: <100ms (p95)
- Search Queries: <50ms
- Cache Hit Rate: >80%
- Real-time Latency: <200ms
- System Uptime: >99.9%

### Dependencies:
- All previous epics (1-11) must be completed
- Infrastructure supporting increased load

### Success Criteria:
- [ ] All performance targets achieved
- [ ] Security audit passing
- [ ] Load testing successful (10k concurrent users)
- [ ] Real-time features operational

---

## 📚 Related Documentation

- [Epic 1: Docker Infrastructure](./EPIC_01_DOCKER_INFRASTRUCTURE.md)
- [Epic 2: Backend API Foundation](./EPIC_02_BACKEND_API_FOUNDATION.md)
- [Development Roadmap](../docs/DEVELOPMENT_ROADMAP.md)
- [Docker Deployment Guide](../docs/DOCKER_DEPLOYMENT.md)

---

**Epic Status**: ⏳ Not Started  
**Last Updated**: 2025-03-03  
**Next Review**: After Epic 11 completion
