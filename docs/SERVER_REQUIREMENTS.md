# Server Requirements - Sarkari Path 2.0

## 🖥️ Overview

This document outlines server requirements for **Sarkari Path 2.0** microservices architecture with 8 Docker containers. Requirements are scaled from development to large production environments.

### 🎯 Understanding Your Traffic: Two User Types

Your platform will have two distinct user types with **very different** resource needs:

```
┌─────────────────────────────────────────────────────────────────┐
│                     YOUR USER BASE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  70-80% VISITORS (Browse Only)          20-30% REGISTERED       │
│  ═══════════════════════════            ═══════════════         │
│                                                                 │
│  👁️  View job listings                  👤 Create account      │
│  🔍 Search and filter                   📝 Profile + preferences│
│  📄 Read job details                    📊 Personalized dashboard│
│  ❌ No login required                   📬 Email/push notifications│
│                                         📌 Track applications   │
│                                         ⏰ Deadline reminders   │
│  Resource Usage: LOW                    Resource Usage: HIGH    │
│  ─────────────────────                  ──────────────────────  │
│  • No database writes                   • Heavy DB reads/writes │
│  • Cached responses                     • Session storage       │
│  • Minimal CPU/RAM                      • Background jobs       │
│  • 2-3 MB bandwidth                     • 4-10 MB bandwidth     │
│                                                                 │
│  100 visitors = ~20 registered users in resource cost          │
└─────────────────────────────────────────────────────────────────┘
```

**Critical for Planning:** 
- Server specs below are based on **registered users** (the resource-intensive group)
- Multiply registered users by 3-4× to get total visitor capacity
- Example: 16 GB server handles 1,000 registered users OR 4,000 total visitors (70/30 mix)

---

## 📊 Quick Reference Table

### User Types Explained

**Two Types of Users:**
1. **Visitors** - Browse jobs without account (70-80% of traffic)
   - View job listings
   - Search and filter
   - No personalization
   - Minimal resource usage

2. **Registered Users** - Create account and track jobs (20-30% of traffic)
   - Personalized dashboard
   - Job tracking and notifications
   - Profile with preferences
   - Higher resource usage (database writes, sessions, notifications)

**Note:** Server specs below are based on **registered users**. Multiply by 3-4× for total visitors.

| Environment | Registered Users | Total Visitors | CPU | RAM | Storage | Bandwidth | Monthly Cost |
|-------------|------------------|----------------|-----|-----|---------|-----------|--------------|
| **Development** | Testing | Testing | 2-4 cores | 8 GB | 40 GB SSD | 10 Mbps | Local (Free) |
| **Small Production** | 100-1K | 300-4K | 4-6 cores | 16 GB | 100 GB SSD | 50 Mbps | $40-60 |
| **Medium Production** | 1K-10K | 3K-40K | 8-12 cores | 32 GB | 250 GB SSD | 100 Mbps | $100-200 |
| **Large Production** | 10K-50K | 30K-200K | 16-32 cores | 64 GB | 500 GB SSD | 1 Gbps | $300-500 |
| **Enterprise** | 50K+ | 150K+ | Multi-server | 128+ GB | 1 TB+ | Multi-Gbps | $1,000+ |

---

## 🏗️ Container Resource Allocation

### 8 Docker Containers Overview

| Container | Idle RAM | Active RAM | CPU Usage | Storage | Scalable? |
|-----------|----------|------------|-----------|---------|-----------|
| **Nginx** | 50 MB | 200-500 MB | 5-10% | 100 MB | No (single reverse proxy) |
| **Frontend** | 200 MB | 500 MB-1 GB | 10-20% | 500 MB | Yes (2-5 instances) |
| **Backend** | 300 MB | 1-2 GB | 20-40% | 500 MB | Yes (2-10 instances) |
| **MongoDB** | 1 GB | 4-16 GB | 10-30% | 20-500 GB | Yes (replica set) |
| **Redis** | 100 MB | 500 MB-2 GB | 5-15% | 1-10 GB | Yes (cluster) |
| **Celery Worker** | 200 MB | 500 MB-1 GB | 10-30% | 200 MB | Yes (2-20 instances) |
| **Celery Beat** | 50 MB | 100-200 MB | 2-5% | 100 MB | No (only 1 scheduler) |
| **Monitoring** | 500 MB | 2-4 GB | 10-20% | 5-50 GB | Optional (ELK/Prometheus) |

---

## � User Types: Resource Impact Analysis

### Why User Type Matters for Server Planning

**Visitors vs Registered Users have very different resource footprints:**

### Type 1: Visitors (70-80% of traffic)

**What they do:**
- Browse job listings (read-only)
- Use search and filters
- View job details
- No login, no account creation

**Resource Impact:**
- ✅ **CPU:** Low (static page rendering, cached responses)
- ✅ **RAM:** Very Low (no session data stored)
- ✅ **Database Reads:** Medium (job listings cached in Redis)
- ❌ **Database Writes:** None (no data saved)
- ✅ **Bandwidth:** Low (2-3 MB per visit)
- ✅ **Storage:** Minimal (~1 MB per 1,000 visitors - just analytics)

**Optimization:**
- Nginx caching serves 80% of visitor requests
- Redis caches job listings (1-hour TTL)
- CDN for static assets
- **Result:** 100 visitors ≈ resource cost of 20-30 registered users

### Type 2: Registered Users (20-30% of traffic)

**What they do:**
- Create account and profile
- Set job preferences
- Track job applications
- Receive notifications (email/push)
- Daily dashboard visits

**Resource Impact:**
- 🔴 **CPU:** High (personalized content, notification generation)
- 🔴 **RAM:** High (session storage, user preferences in cache)
- 🔴 **Database Reads:** High (profile, applications, preferences)
- 🔴 **Database Writes:** High (applications, notifications, updates)
- 🔴 **Bandwidth:** Medium-High (4-10 MB per session)
- 🔴 **Storage:** High (~240 KB per user in database)
- 🔴 **Background Jobs:** Celery processes notifications for each user

**Extra Services Used:**
- Celery workers for notifications
- Redis for session storage
- Email service (SMTP costs)
- Firebase for push notifications

**Result:** Registered users are **3-5× more resource-intensive** than visitors

### Planning Your Server Based on User Mix

**Scenario 1: Content Site (90% visitors, 10% registered)**
- Total users: 10,000 (9,000 visitors + 1,000 registered)
- Equivalent Load: ~3,000 registered users
- **Server Needed:** Small Production (16 GB RAM)

**Scenario 2: Engagement Focus (70% visitors, 30% registered)**
- Total users: 10,000 (7,000 visitors + 3,000 registered)
- Equivalent Load: ~5,000 registered users
- **Server Needed:** Medium Production (32 GB RAM)

**Scenario 3: High Registration (50% visitors, 50% registered)**
- Total users: 10,000 (5,000 visitors + 5,000 registered)
- Equivalent Load: ~7,000 registered users
- **Server Needed:** Medium-Large Production (32-64 GB RAM)

### Conversion Rate Impact on Infrastructure

**Registration Rate Matters:**

| Visitors | Conversion % | Registered Users | Server Specs | Monthly Cost |
|----------|--------------|------------------|--------------|--------------|
| 10,000 | 10% | 1,000 | 16 GB RAM, 4 cores | $40-50 |
| 10,000 | 20% | 2,000 | 16 GB RAM, 6 cores | $50-70 |
| 10,000 | 30% | 3,000 | 32 GB RAM, 8 cores | $100-120 |
| 10,000 | 50% | 5,000 | 32 GB RAM, 12 cores | $150-180 |

**Takeaway:** Higher registration rate = more powerful server needed

---

## �💻 Environment-Specific Requirements

### 1. Development/Testing Environment

**Purpose:** Local development, testing, debugging

**Minimum Specifications:**
- **CPU**: 2-4 cores
- **RAM**: 8 GB
- **Storage**: 40 GB SSD
- **Bandwidth**: 10 Mbps
- **OS**: Ubuntu 22.04 LTS / macOS / Windows with WSL2

**Container Allocation:**
```yaml
services:
  nginx:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
  
  frontend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
  
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
  
  mongodb:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
  
  redis:
    deploy:
      resources:
        limits:
          cpus: '0.25'
          memory: 512M
  
  celery_worker:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
  
  celery_beat:
    deploy:
      resources:
        limits:
          cpus: '0.25'
          memory: 256M
```

**Development Setup Commands:**
```bash
# Check system resources
docker system info
docker stats

# Start with resource limits
docker compose up -d

# Monitor resource usage
docker stats --no-stream
```

---

### 2. Small Production (100-1,000 Registered Users)

**Purpose:** Initial launch, beta testing, small user base

**User Breakdown:**
- **Registered Users:** 100-1,000
- **Total Visitors:** 300-4,000 (includes registered users)
- **Daily Active Users:** 50-200 registered
- **Concurrent Users:** 10-50 at peak times

**Recommended Specifications:**
- **CPU**: 4-6 cores @ 2.5+ GHz
- **RAM**: 16 GB DDR4
- **Storage**: 100 GB SSD (NVMe preferred)
- **Bandwidth**: 50 Mbps (1-2 TB/month)
- **OS**: Ubuntu 22.04 LTS Server

**Container Allocation:**
```
Nginx:           512 MB RAM, 0.5 CPU
Frontend:        1 GB RAM, 1 CPU (1 instance)
Backend:         2 GB RAM, 2 CPU (3 Gunicorn workers)
MongoDB:         4 GB RAM, 2 CPU
Redis:           1 GB RAM, 0.5 CPU
Celery Worker:   2 GB RAM, 1 CPU (2 worker processes)
Celery Beat:     512 MB RAM, 0.25 CPU
System Reserve:  1 GB RAM
─────────────────────────────────────
Total:           ~11 GB RAM, 7.75 CPU cores
```

**Expected Performance:**
- API Response Time: < 200ms
- Concurrent Users: 100-200
- Daily Jobs/Notifications: 500-1,000
- Database Size: 1-5 GB

**Suitable Providers:**
- **Hostinger VPS Plan 4**: $40/month (4 cores, 16 GB RAM, 100 GB SSD)
- **DigitalOcean Droplet**: $48/month (4 cores, 16 GB RAM, 100 GB SSD)
- **AWS Lightsail**: $40/month (2 cores, 16 GB RAM, 80 GB SSD)
- **Vultr High Frequency**: $48/month (4 cores, 16 GB RAM, 128 GB NVMe)

---

### 3. Medium Production (1,000-10,000 Registered Users)

**Purpose:** Growing user base, increased traffic, production-ready

**User Breakdown:**
- **Registered Users:** 1,000-10,000
- **Total Visitors:** 3,000-40,000 (includes registered users)
- **Daily Active Users:** 500-2,000 registered
- **Concurrent Users:** 100-500 at peak times

**Recommended Specifications:**
- **CPU**: 8-12 cores @ 3.0+ GHz
- **RAM**: 32 GB DDR4
- **Storage**: 250 GB SSD (NVMe required) + 100 GB backup
- **Bandwidth**: 100 Mbps (5-10 TB/month)
- **OS**: Ubuntu 22.04 LTS Server

**Container Scaling:**
```
Nginx:              1 GB RAM, 1 CPU
Frontend:           2 GB RAM, 2 CPU (2 instances)
Backend:            4 GB RAM, 4 CPU (5 Gunicorn workers × 2 instances)
MongoDB:            8 GB RAM, 4 CPU (consider replica set)
Redis:              2 GB RAM, 1 CPU
Celery Workers:     4 GB RAM, 2 CPU (4 worker instances)
Celery Beat:        512 MB RAM, 0.25 CPU
Monitoring (ELK):   2 GB RAM, 1 CPU
System Reserve:     2 GB RAM
─────────────────────────────────────────────
Total:              ~25 GB RAM, 15.25 CPU cores
```

**Scaling Commands:**
```bash
# Scale backend API
docker compose up -d --scale backend=2

# Scale celery workers for notifications
docker compose up -d --scale celery_worker=4

# Scale frontend for load distribution
docker compose up -d --scale frontend=2

# Check scaling status
docker compose ps
```

**Expected Performance:**
- API Response Time: < 150ms
- Concurrent Users: 500-1,000
- Daily Jobs/Notifications: 5,000-10,000
- Database Size: 10-50 GB

**Suitable Providers:**
- **Dedicated Server (Hetzner)**: €100/month (8 cores, 32 GB RAM, 512 GB SSD)
- **DigitalOcean Premium Droplet**: $160/month (8 cores, 32 GB RAM, 400 GB SSD)
- **AWS EC2 (t3.2xlarge)**: ~$120/month (8 cores, 32 GB RAM)
- **Linode Dedicated CPU**: $120/month (8 cores, 32 GB RAM, 640 GB SSD)

**Optimization Tips:**
- Enable Redis caching for job listings (1-hour TTL)
- Implement CDN for static assets (CloudFlare free tier)
- Setup MongoDB replica set for high availability
- Enable Nginx cache for frequently accessed pages

---

### 4. Large Production (10,000-50,000 Registered Users)

**Purpose:** Large user base, high traffic, enterprise-grade

**User Breakdown:**
- **Registered Users:** 10,000-50,000
- **Total Visitors:** 30,000-200,000 (includes registered users)
- **Daily Active Users:** 2,000-10,000 registered
- **Concurrent Users:** 500-2,000 at peak times

**Recommended Architecture:** Multi-Server Setup

#### **Web Server (Frontend + Backend)**
- **CPU**: 8-16 cores @ 3.5+ GHz
- **RAM**: 32-64 GB DDR4
- **Storage**: 100 GB SSD
- **Instances**: 2-3 with load balancer

#### **Database Server (MongoDB)**
- **CPU**: 8-16 cores @ 3.0+ GHz
- **RAM**: 32-64 GB DDR4
- **Storage**: 500 GB NVMe SSD (IOPS optimized)
- **Setup**: 3-node replica set (Primary + 2 Secondaries)

#### **Cache Server (Redis)**
- **CPU**: 4-8 cores
- **RAM**: 16-32 GB DDR4
- **Storage**: 50 GB SSD
- **Setup**: Redis Cluster or Sentinel for HA

#### **Worker Server (Celery)**
- **CPU**: 8-16 cores
- **RAM**: 16-32 GB
- **Storage**: 50 GB SSD
- **Workers**: 10-20 Celery worker processes

#### **Load Balancer**
- **Type**: Nginx / HAProxy / AWS ALB
- **Setup**: Round-robin or least-connections
- **SSL**: Centralized SSL termination

**Total Infrastructure Cost:** $300-500/month

**Expected Performance:**
- API Response Time: < 100ms
- Concurrent Users: 2,000-5,000
- Daily Jobs/Notifications: 50,000-100,000
- Database Size: 100-500 GB

**Suitable Providers:**
- **AWS (with Auto Scaling)**: $300-500/month
- **Google Cloud Platform**: $300-500/month
- **Azure**: $300-500/month
- **Hetzner Dedicated Servers**: €200-300/month (best price/performance)

---

### 5. Enterprise (50,000+ Users)

**Recommended Architecture:** Cloud-Native with Auto Scaling

**Infrastructure Components:**
- **Kubernetes Cluster**: For container orchestration
- **Load Balancer**: Multi-region with DDoS protection
- **Database**: MongoDB Atlas (Managed, 3+ regions)
- **Cache**: Redis Enterprise or AWS ElastiCache
- **CDN**: CloudFlare / AWS CloudFront
- **Monitoring**: Datadog / New Relic / Prometheus + Grafana
- **Logging**: ELK Stack or AWS CloudWatch
- **Backup**: Automated daily backups with 30-day retention

**Total Infrastructure Cost:** $1,000-5,000/month

---

## 💾 Storage Requirements in Detail

### Database Growth Estimates

**Important:** Only **registered users** generate database records. Visitors don't create any persistent data.

**MongoDB Collections (15 total) - Per 10,000 Registered Users:**

| Collection | Size per Record | Records (10K users) | Total Size | TTL Cleanup | Only for Registered? |
|------------|----------------|---------------------|------------|-------------|----------------------|
| **Users** | 1 KB | 10,000 | 10 MB | None | ✅ Yes |
| **Profiles** | 3 KB | 10,000 | 30 MB | None | ✅ Yes |
| **Jobs** | 10 KB | 1,000 | 10 MB | None | ❌ No (all users see) |
| **Applications** | 2 KB | 50,000 | 100 MB | None | ✅ Yes |
| **Notifications** | 1 KB | 100,000 | 100 MB | 90 days | ✅ Yes |
| **Results** | 5 KB | 5,000 | 25 MB | None | ❌ No (all users see) |
| **Admit Cards** | 3 KB | 10,000 | 30 MB | None | ❌ No (all users see) |
| **Answer Keys** | 2 KB | 5,000 | 10 MB | None | ❌ No (all users see) |
| **Admissions** | 5 KB | 3,000 | 15 MB | None | ❌ No (all users see) |
| **Yojanas** | 8 KB | 500 | 4 MB | None | ❌ No (all users see) |
| **Board Results** | 3 KB | 20,000 | 60 MB | None | ❌ No (all users see) |
| **Analytics** | 1 KB | 500,000 | 500 MB | None | ⚠️ Both (page views) |
| **Search Logs** | 500 B | 100,000 | 50 MB | 6 months | ⚠️ Both |
| **Admin Logs** | 800 B | 50,000 | 40 MB | 1 year | ❌ No (system) |
| **Page Views** | 300 B | 1,000,000 | 300 MB | None | ⚠️ Both |

**Database Size Breakdown:**
- **Base Content (Jobs, Results, etc.):** ~200 MB (same regardless of user count)
- **Per Registered User Data:** ~240 KB per user (profile + applications + notifications)
- **Analytics/Logs (Both user types):** Grows with total traffic

**Formula:** `Database Size = 200 MB + (Registered Users × 240 KB) + (Total Visitors × 1 KB)`

**Examples:**
- 1,000 registered users + 3,000 visitors = 200 MB + 240 MB + 3 MB = **443 MB**
- 10,000 registered users + 30,000 visitors = 200 MB + 2.4 GB + 30 MB = **2.6 GB**
- 50,000 registered users + 150,000 visitors = 200 MB + 12 GB + 150 MB = **12.3 GB**

**Monthly Growth:**
- Registered users: ~20 KB/month per user (new applications, notifications)
- Visitors: ~200 bytes/month (page view logs only)
- Content updates: ~50 MB/month (new jobs, results)

**Total for 10K Users + 30K Visitors:** ~2.6 GB
**Monthly Growth:** ~130 MB/month (registered) + 50 MB (content) = **180 MB/month**
**With TTL Cleanup:** Saves 75% on notifications/logs (prevents runaway growth)

### Storage Recommendations by Scale

**Based on 70% visitors + 30% registered users:**

| Scale | Registered Users | Total Visitors | Database | Logs | Backups | Total Required |
|-------|------------------|----------------|----------|------|---------|----------------|
| **Small** | 300 | 1,000 | 300 MB | 2 GB | 5 GB | **40-60 GB** |
| **Medium** | 3,000 | 10,000 | 3 GB | 10 GB | 30 GB | **100-150 GB** |
| **Large** | 15,000 | 50,000 | 15 GB | 30 GB | 100 GB | **250-400 GB** |
| **Enterprise** | 50,000+ | 150,000+ | 50 GB+ | 100 GB | 500 GB | **1+ TB** |

**Key Insight:** Storage grows primarily with **registered users**, not total traffic. 
- 1,000 visitors = ~1 MB database storage (just page view logs)
- 1,000 registered users = ~240 MB database storage (profiles, applications, notifications)

**Storage Type Recommendations:**
- **Development:** HDD acceptable
- **Small Production:** SATA SSD minimum
- **Medium Production:** NVMe SSD recommended
- **Large Production:** NVMe SSD with RAID 10
- **Enterprise:** Distributed storage (Ceph, GlusterFS) or cloud storage (EBS, Persistent Disks)

---

## 🌐 Network Bandwidth Requirements

### User Type Comparison

**Visitors (No Account):**
- Can view job listings and search
- No login, no profile, no notifications
- Lower bandwidth per session
- Typically visit 2-3 times, don't return regularly

**Registered Users (With Account):**
- Personalized dashboard and recommendations
- Job tracking and notifications
- Multiple daily visits to check updates
- Higher engagement and bandwidth

### Bandwidth Calculation by User Type

#### Type 1: Visitors (Browse Only)

**Single Visitor Session:**
- Initial Homepage Load: 1.5 MB (HTML, CSS, JS, images)
- Job Listing Page: 400 KB (browsing jobs)
- Job Detail Pages: 200 KB × 2-3 views = 400-600 KB
- **Total per visit:** ~2-2.5 MB

**Typical Behavior:**
- Visits per month: 1-3 times
- Pages viewed: 3-5 per visit
- Monthly bandwidth per visitor: ~5-7 MB

#### Type 2: Registered Users (With Account)

**Single User Session:**
- Initial Page Load: 1.5 MB
- Dashboard Load: 600 KB (personalized data from API)
- Job Listing + Filters: 500 KB
- Job Detail Pages: 300 KB × 3-5 = 900-1,500 KB
- Profile/Applications: 400 KB
- API Requests: 50 requests × 20 KB = 1 MB
- Notifications: 5-10 KB × 3 = 15-30 KB
- **Total per session:** ~4-5 MB

**Typical Behavior (Engaged Users):**
- Daily visits: 1-2 times per day
- Pages viewed: 5-10 per session
- Daily bandwidth: 4-10 MB per user
- Monthly bandwidth: 120-300 MB per user

### Bandwidth by Scale

**Assuming 70% Visitors + 30% Registered Users:**

| Scale | Registered Users | Visitors (3-4×) | Daily Bandwidth | Monthly Bandwidth | Required Plan |
|-------|------------------|-----------------|-----------------|-------------------|---------------|
| **Small** | 500 | 1,500-2,000 | Visitors: 5 GB<br>Users: 2 GB<br>**Total: 7 GB** | 210 GB | 500 GB/month |
| **Medium** | 5,000 | 15,000-20,000 | Visitors: 50 GB<br>Users: 25 GB<br>**Total: 75 GB** | 2.25 TB | 5 TB/month |
| **Large** | 25,000 | 75,000-100,000 | Visitors: 250 GB<br>Users: 125 GB<br>**Total: 375 GB** | 11 TB | 20 TB/month |
| **Enterprise** | 50,000+ | 150,000+ | Visitors: 500 GB<br>Users: 250 GB<br>**Total: 750 GB** | 22 TB | Unlimited |

### Resource Usage Comparison

| Metric | Visitors | Registered Users | Multiplier |
|--------|----------|------------------|------------|
| **Database Reads** | Medium | High | 3× more |
| **Database Writes** | None | High | ∞ (only users write) |
| **Session Storage** | Temporary | Persistent | Redis usage |
| **Notifications** | None | All | CPU/Memory impact |
| **API Calls** | 5-10/session | 50+/session | 5-10× more |
| **Cache Utilization** | High (shared) | Medium (personalized) | Different patterns |
| **Server Load** | 1× | 3-4× | Significant difference |

**Bandwidth Recommendations:**
- **Small:** 1-2 TB/month data transfer
- **Medium:** 5-10 TB/month
- **Large:** Unlimited or 20+ TB/month
- **Enterprise:** CDN + unlimited bandwidth

**Cost Optimization:**
- Use CDN (CloudFlare) for static assets (free tier available)
- Enable Gzip compression in Nginx (reduces by 70%)
- Implement image optimization (WebP format, lazy loading)
- Cache API responses in Redis (reduces backend requests)

---

## 🔧 System Requirements Breakdown

### Operating System

**Recommended:** Ubuntu 22.04 LTS Server

**Why Ubuntu?**
- ✅ Free and open-source
- ✅ Excellent Docker support
- ✅ Large community and documentation
- ✅ 5 years of security updates
- ✅ Low resource overhead

**Alternatives:**
- **CentOS Stream / Rocky Linux**: For enterprise environments
- **Debian 11**: More stable, less frequent updates
- **RHEL**: Enterprise support available

**System Packages Required:**
```bash
# Essential packages
sudo apt update && sudo apt install -y \
  curl \
  wget \
  git \
  htop \
  vim \
  ufw \
  fail2ban

# Docker installation
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Docker Compose
sudo apt install docker-compose-plugin

# Monitoring tools
sudo apt install -y \
  sysstat \
  iotop \
  nethogs
```

---

### CPU Requirements

**Minimum Cores by Scale:**
- **Development:** 2 cores
- **Small Production:** 4 cores
- **Medium Production:** 8 cores
- **Large Production:** 16+ cores

**CPU Architecture:**
- **Preferred:** x86_64 (AMD64)
- **Supported:** ARM64 (for development only)

**CPU Features Required:**
- Virtualization support (VT-x / AMD-V) for Docker
- AES-NI for encryption performance
- Multiple cores (single-core not recommended)

**CPU Intensive Components:**
- Backend API (JSON parsing, database queries)
- MongoDB (indexing, aggregation)
- Celery Workers (notification processing)

---

### RAM Requirements

**Memory Allocation Strategy:**

```
System OS:           1-2 GB
Nginx:               0.5 GB
Frontend:            1-2 GB
Backend:             2-4 GB (scales with Gunicorn workers)
MongoDB:             4-16 GB (uses RAM for indexes and cache)
Redis:               1-4 GB (in-memory database)
Celery Workers:      2-8 GB (scales with worker count)
Monitoring:          2-4 GB (optional)
Reserve:             2 GB (system buffer)
─────────────────────────────────
Total Small:         16 GB
Total Medium:        32 GB
Total Large:         64+ GB
```

**MongoDB Memory Considerations:**
MongoDB uses available RAM for:
- WiredTiger cache (50% of RAM by default)
- Connection pool
- Query execution
- Index storage

**Formula:** `MongoDB RAM = (Database Size × 0.5) + 2 GB`

Example: 20 GB database = 12 GB RAM minimum

---

### Disk I/O Requirements

**IOPS Requirements by Load:**

| Scale | Read IOPS | Write IOPS | Total IOPS |
|-------|-----------|------------|------------|
| **Small** | 500 | 200 | 700 |
| **Medium** | 2,000 | 1,000 | 3,000 |
| **Large** | 10,000 | 5,000 | 15,000 |
| **Enterprise** | 50,000+ | 20,000+ | 70,000+ |

**Storage Type Performance:**
- **HDD (7200 RPM):** ~100 IOPS (not recommended for production)
- **SATA SSD:** ~10,000 IOPS (acceptable for small production)
- **NVMe SSD:** ~100,000+ IOPS (recommended for medium+)
- **Cloud SSD:** Varies (EBS: 3,000-16,000 IOPS)

**Disk-Intensive Operations:**
- MongoDB write operations (job creation, user registration)
- Log file writes (application logs, Nginx logs)
- Backup operations (daily database dumps)
- Search indexing (Elasticsearch if implemented)

---

## 🚀 Cloud Provider Comparison

### Small to Medium Production

| Provider | Plan | Specs | Price | Best For |
|----------|------|-------|-------|----------|
| **Hostinger VPS** | Plan 4 | 4 cores, 16 GB, 100 GB | $40/mo | Budget, Indian users |
| **DigitalOcean** | Premium | 4 cores, 16 GB, 100 GB | $48/mo | Easy setup, good docs |
| **AWS Lightsail** | 2xlarge | 2 cores, 16 GB, 80 GB | $40/mo | AWS ecosystem |
| **Vultr** | High Frequency | 4 cores, 16 GB, 128 GB | $48/mo | Performance |
| **Linode** | Dedicated 16GB | 4 cores, 16 GB, 320 GB | $80/mo | More storage |
| **Hetzner** | CX41 | 4 cores, 16 GB, 160 GB | €15/mo | Best value (EU) |

### Large Production (Dedicated Servers)

| Provider | Specs | Price | Location | Best For |
|----------|-------|-------|----------|----------|
| **Hetzner Dedicated** | 8 cores, 64 GB, 1 TB NVMe | €100/mo | Germany | Best value |
| **OVH Dedicated** | 8 cores, 32 GB, 500 GB SSD | €80/mo | France/Canada | Europe |
| **AWS EC2** | t3.2xlarge (8 cores, 32 GB) | ~$120/mo | Global | Scalability |
| **DigitalOcean** | Premium 32GB (8 cores, 32 GB) | $160/mo | Global | Simplicity |

### Enterprise (Managed Services)

| Service | Provider | Use Case | Pricing Model |
|---------|----------|----------|---------------|
| **MongoDB Atlas** | MongoDB Inc. | Managed database with auto-scaling | Pay-per-use |
| **AWS RDS** | Amazon | Managed database with replication | Hourly |
| **Redis Enterprise** | Redis Labs | Managed cache with HA | Subscription |
| **AWS ElastiCache** | Amazon | Managed Redis/Memcached | Hourly |
| **Kubernetes (EKS/GKE/AKS)** | AWS/GCP/Azure | Container orchestration | Hourly + resources |

---

## 🎯 Recommended Deployment Strategy

### Phase 1: Launch (Month 1-3)
**Target:** 100-1,000 users

**Infrastructure:**
- **Server:** Hostinger VPS Plan 4 or DigitalOcean Droplet
- **Specs:** 4 cores, 16 GB RAM, 100 GB SSD
- **Cost:** $40-50/month
- **Architecture:** Single-server with all 8 containers

**Setup:**
```bash
# Clone repository
git clone https://github.com/SumanKr7/sarkari_path_2.0.git
cd sarkari_path_2.0

# Configure environment
cp .env.example .env
nano .env  # Fill in credentials

# Start all services
docker compose up -d

# Monitor resources
docker stats
```

**Monitoring:**
- CPU usage should stay < 50%
- RAM usage should stay < 12 GB
- Disk I/O should be minimal
- Response times < 200ms

---

### Phase 2: Growth (Month 4-12)
**Target:** 1,000-5,000 users

**Infrastructure:**
- **Server:** Dedicated server or larger VPS
- **Specs:** 8 cores, 32 GB RAM, 250 GB SSD
- **Cost:** $100-120/month
- **Changes:**
  - Scale backend to 2 instances
  - Scale Celery workers to 4 instances
  - Implement Redis caching strategy
  - Setup daily automated backups

**Scaling Commands:**
```bash
# Scale services
docker compose up -d --scale backend=2 --scale celery_worker=4

# Verify scaling
docker compose ps

# Monitor performance
docker stats --no-stream
```

**Optimization:**
- Enable Nginx caching for static content
- Implement Redis cache for job listings
- Setup MongoDB indexes for frequent queries
- Configure CDN for static assets

---

### Phase 3: Maturity (Year 2+)
**Target:** 10,000+ users

**Infrastructure:** Multi-server architecture

**Server 1: Web Layer**
- Nginx Load Balancer
- Frontend (2-3 instances)
- Backend (3-5 instances)

**Server 2: Database**
- MongoDB 3-node replica set
- Redis Cluster

**Server 3: Workers**
- Celery Workers (10-20 instances)
- Celery Beat (1 instance)

**Server 4: Monitoring** (Optional)
- ELK Stack / Prometheus + Grafana
- Application Performance Monitoring

**Total Cost:** $300-500/month

---

## 📊 Performance Benchmarks

### Expected Performance Metrics

**Note:** Metrics vary significantly between visitors and registered users

| Metric | Small | Medium | Large | Visitor vs Registered |
|--------|-------|--------|-------|----------------------|
| **API Response Time** | < 200ms | < 150ms | < 100ms | Visitors: 50% faster (cached) |
| **Page Load Time** | < 2s | < 1.5s | < 1s | Both similar |
| **Concurrent Users** | 100-200 | 500-1,000 | 2,000-5,000 | Mix of both types |
| **Requests per Second** | 50-100 | 200-500 | 1,000-2,000 | 80% from visitors |
| **Database Query Time** | < 50ms | < 30ms | < 20ms | Registered users only |
| **Redis Cache Hit Rate** | 70-80% | 80-90% | 90-95% | Higher for visitors |
| **Uptime** | 99% | 99.5% | 99.9% | Both types affected |

### Load Distribution by User Type

**Typical Traffic Pattern (70% visitors, 30% registered):**

| Load Type | Visitors Contribute | Registered Users Contribute |
|-----------|---------------------|----------------------------|
| **Frontend Requests** | 70% | 30% |
| **Backend API Calls** | 30% | 70% |
| **Database Reads** | 20% | 80% |
| **Database Writes** | 0% | 100% |
| **Cache Usage** | 80% (shared) | 20% (personalized) |
| **Background Jobs** | 0% | 100% |
| **Notifications** | 0% | 100% |

### Load Testing Commands

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test backend API (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost/api/v1/jobs

# Test frontend (500 requests, 50 concurrent)
ab -n 500 -c 50 http://localhost/

# Test with authentication
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN" http://localhost/api/v1/profile

# View detailed results
ab -n 1000 -c 100 -g results.tsv http://localhost/api/v1/jobs
```

---

## ⚠️ Critical Considerations

### 1. MongoDB Performance Optimization

**Your 15 Collections Need:**
- Indexed queries for performance
- TTL indexes for auto-cleanup (saves 75% storage)
- Compound indexes for complex queries
- Query profiling enabled

**Index Examples:**
```javascript
// Job search optimization
db.job_vacancies.createIndex({ 
  "organization": 1, 
  "status": 1, 
  "created_at": -1 
});

// User eligibility matching
db.user_profiles.createIndex({ 
  "education.highest_qualification": 1,
  "personal_info.category": 1 
});

// Notification queries
db.notifications.createIndex({ 
  "user_id": 1, 
  "is_read": 1,
  "created_at": -1 
});
```

**Memory Requirements:**
- Indexes are stored in RAM for fast access
- Formula: Index size ≈ 10-20% of data size
- Example: 20 GB data = 2-4 GB RAM for indexes

---

### 2. Redis Memory Management

**Redis stores everything in RAM:**

| Data Type | Size per Item | Count | Total | User Type |
|-----------|---------------|-------|-------|-----------|
| User Sessions | 10 KB | 1,000 concurrent | 10 MB | ✅ Registered only |
| Visitor Tracking | 500 B | 2,000 concurrent | 1 MB | ✅ Visitors only |
| Job Cache (1h TTL) | 500 KB | 100 jobs | 50 MB | ⚠️ Both (shared) |
| Rate Limit Counters | 100 B | 10,000 users | 1 MB | ⚠️ Both |
| Celery Task Queue | 1 KB | 1,000 tasks | 1 MB | ✅ Registered only |
| API Response Cache | varies | varies | 50-200 MB | ⚠️ Both |

**Key Insight:** Redis usage is mostly **shared** between user types (job listings cache). Session storage only applies to registered users.

**Total Redis RAM by User Mix:**

| Registered Users | Total Visitors | Redis RAM Needed |
|------------------|----------------|------------------|
| 500 | 1,500 | 500 MB |
| 2,000 | 6,000 | 1 GB |
| 10,000 | 30,000 | 2 GB |
| 50,000 | 150,000 | 4-8 GB |

**Total Redis RAM:** 500 MB - 2 GB recommended for small-medium, 4-8 GB for large

**Redis Configuration:**
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict least recently used
save 900 1  # Save to disk every 15 min
appendonly yes  # AOF persistence for durability
```

---

### 3. Celery Worker Scaling

**Your Notification System (Registered Users Only):**

**Important:** Celery only processes tasks for **registered users**. Visitors never trigger background jobs.

| Task Type | Frequency | Priority | Workers Needed | User Type |
|-----------|-----------|----------|----------------|-----------|
| Email Notifications | Immediate | HIGH | 2-4 workers | ✅ Registered only |
| Push Notifications | Immediate | HIGH | 1-2 workers | ✅ Registered only |
| Job Matching (Daily) | Once/day | MEDIUM | 2-3 workers | ✅ Registered only |
| Deadline Reminders | Once/day | MEDIUM | 1-2 workers | ✅ Registered only |
| Analytics Aggregation | Hourly | LOW | 1 worker | ⚠️ Both (page views) |

**Scaling by Registered User Count:**

| Registered Users | Notifications/Day | Celery Workers | Worker RAM |
|------------------|-------------------|----------------|------------|
| 100-500 | 100-500 | 2 workers | 1 GB |
| 500-2,000 | 500-2,000 | 3-4 workers | 2 GB |
| 2,000-10,000 | 2,000-10,000 | 5-8 workers | 4 GB |
| 10,000-50,000 | 10,000-50,000 | 10-15 workers | 8-12 GB |

**Key Point:** Number of visitors doesn't affect Celery scaling - only registered users receive notifications.

**Scaling Strategy:**
```bash
# Small: 2 workers total
docker compose up -d --scale celery_worker=2

# Medium: 4 workers (with priority queues)
docker compose up -d --scale celery_worker=4

# Large: 10+ workers (separate by priority)
docker compose up -d --scale celery_worker=10
```

**Worker Configuration:**
```python
# celery_worker.py
celery = Celery('sarkari_path')

celery.conf.task_routes = {
    'app.tasks.send_email': {'queue': 'high_priority'},
    'app.tasks.send_push': {'queue': 'high_priority'},
    'app.tasks.match_jobs': {'queue': 'medium_priority'},
    'app.tasks.generate_analytics': {'queue': 'low_priority'},
}

celery.conf.worker_prefetch_multiplier = 4
celery.conf.worker_max_tasks_per_child = 1000
```

---

### 4. Backup Strategy

**Daily Automated Backups:**

```bash
#!/bin/bash
# scripts/backup/backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mongodb"

# Backup MongoDB
docker compose exec mongodb mongodump \
  --uri="mongodb://user:pass@localhost:27017/sarkari_path" \
  --out=/backup/$DATE

# Compress backup
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz /backup/$DATE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$DATE.tar.gz s3://your-bucket/backups/
```

**Backup Schedule:**
- **Development:** Weekly manual backups
- **Small Production:** Daily automated backups, 7-day retention
- **Medium Production:** Daily backups + weekly full backups, 30-day retention
- **Large Production:** Hourly incremental + daily full, 90-day retention

**Backup Storage Requirements:**
- Compressed backup ≈ 20-30% of database size
- 30-day retention for 50 GB database = 300-450 GB backup storage

---

## 🔍 Monitoring & Alerting

### Essential Metrics to Monitor

**System Metrics:**
- CPU usage per container
- RAM usage per container
- Disk I/O (read/write IOPS)
- Network bandwidth (in/out)
- Disk space usage

**Application Metrics:**
- API response times (p50, p95, p99)
- Error rates (4xx, 5xx responses)
- Database query times
- Redis cache hit rate
- Celery task queue length
- Celery task processing time

**Business Metrics:**
- Active users (daily, monthly)
- Job postings (created, viewed)
- Notifications sent (email, push)
- User registrations
- Application submissions

### Monitoring Tools

**Free/Open Source:**
- **Docker Stats**: Built-in container monitoring
- **Prometheus + Grafana**: Time-series metrics and dashboards
- **ELK Stack**: Centralized logging (Elasticsearch, Logstash, Kibana)
- **cAdvisor**: Container metrics collector
- **Node Exporter**: System metrics for Prometheus

**Paid Services:**
- **Datadog**: $15-31/host/month (comprehensive APM)
- **New Relic**: $25-99/month (application performance monitoring)
- **AWS CloudWatch**: Pay-per-use (AWS native)
- **Sentry**: $26-80/month (error tracking)

### Alert Thresholds

```yaml
# alerts.yml (Prometheus Alert Rules)
groups:
  - name: sarkari_path_alerts
    rules:
      # CPU Alert
      - alert: HighCPUUsage
        expr: container_cpu_usage_seconds_total > 0.8
        for: 5m
        annotations:
          summary: "High CPU usage detected"

      # RAM Alert
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        annotations:
          summary: "Memory usage above 90%"

      # Disk Space Alert
      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.15
        for: 5m
        annotations:
          summary: "Disk space below 15%"

      # API Response Time Alert
      - alert: SlowAPIResponses
        expr: http_request_duration_seconds{quantile="0.95"} > 0.5
        for: 10m
        annotations:
          summary: "95th percentile response time above 500ms"

      # Error Rate Alert
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "Error rate above 5%"
```

---

## 🛡️ Security Requirements

### Firewall Configuration

```bash
# UFW firewall setup
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change port for security)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### SSL/TLS Requirements

**Minimum:** TLS 1.2
**Recommended:** TLS 1.3

**Free SSL Certificate:**
```bash
# Install Certbot
sudo apt install certbot

# Get certificate (with Nginx)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (runs twice daily)
sudo systemctl enable certbot.timer
```

### Security Hardening

**Required Security Measures:**
- ✅ Firewall enabled (UFW or iptables)
- ✅ Fail2ban installed (prevent brute-force)
- ✅ SSH key authentication (disable password login)
- ✅ Non-root Docker user
- ✅ Regular security updates
- ✅ Strong passwords (minimum 16 characters)
- ✅ Database authentication enabled
- ✅ Redis password protection
- ✅ HTTPS only (redirect HTTP to HTTPS)
- ✅ Security headers in Nginx

---

## 🎯 Summary Recommendations

### For Your Project (Sarkari Path 2.0)

**Understanding Your User Mix:**
- **Target:** Government job seekers in India
- **Expected Mix:** 70% visitors (browse only) + 30% registered users (with accounts)
- **Growth Pattern:** Start with more visitors, conversion rate increases over time

**Start with (Recommended for 300-1,000 Registered Users):**

**Actual User Capacity:**
- **Registered Users:** 300-1,000 (your core users)
- **Total Visitors:** 1,000-4,000 (including registered users)
- **Daily Active:** 100-300 registered users
- **Peak Concurrent:** 50-100 users

**Infrastructure:**
- **Provider:** Hostinger VPS Plan 4 or DigitalOcean Droplet
- **Specs:** 4 cores, 16 GB RAM, 100 GB SSD
- **Cost:** $40-50/month
- **Architecture:** Single-server with 8 Docker containers

**This setup provides:**
- ✅ Handles 1K registered users comfortably
- ✅ Can serve 4K total visitors
- ✅ Room to grow (can handle up to 2K registered before scaling)
- ✅ Affordable startup costs
- ✅ All features working (notifications, caching, background jobs)
- ✅ Excellent performance (< 200ms response times)
- ✅ Simple management (single server)

**When to Scale:**
- **Registered users** > 1,500 (not total visitors)
- **CPU usage** consistently > 70%
- **RAM usage** consistently > 80%
- **Response times** > 300ms
- **Concurrent users** > 500
- **Database size** > 50 GB

**Scaling Path:**
1. **Vertical Scaling (Month 3-6):** When you reach 1,500-2,000 registered users
   - Upgrade to 8 cores, 32 GB RAM (~$100-120/month)
   - No architecture changes needed

2. **Horizontal Scaling (Month 6-12):** When you reach 5,000+ registered users
   - Add second server, load balancer (~$200-250/month)
   - Scale backend to 2 instances
   - Scale Celery workers to 4-6 instances

3. **Multi-Server (Year 2+):** When you reach 20,000+ registered users
   - Separate database server (~$300-500/month)
   - Separate cache server
   - Separate worker server

**Real-World Example:**
```
Month 1: 100 registered, 400 visitors → Current server: ✅ Plenty of capacity
Month 3: 500 registered, 2,000 visitors → Current server: ✅ Running smoothly
Month 6: 1,500 registered, 6,000 visitors → Time to upgrade to 32 GB RAM
Month 12: 5,000 registered, 20,000 visitors → Time for multi-server setup
```

---

## 📞 Support & Resources

### Useful Commands

**Check System Resources:**
```bash
# CPU info
lscpu

# Memory info
free -h

# Disk usage
df -h

# Current resource usage
htop

# Docker resource usage
docker stats

# Check specific container
docker stats backend
```

**Optimize Performance:**
```bash
# Clear system cache
sudo sync && sudo sysctl -w vm.drop_caches=3

# View slow queries (MongoDB)
docker compose exec mongodb mongosh
> db.setProfilingLevel(2)
> db.system.profile.find().sort({millis:-1}).limit(10)

# Redis memory usage
docker compose exec redis redis-cli INFO memory

# Nginx access logs (find slow requests)
docker compose logs nginx | grep "request_time:[2-9]"
```

### Additional Documentation

- **Docker Deployment Guide:** [docs/DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
- **Project Structure:** [docs/PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)
- **Quick Start:** [docs/QUICKSTART.md](./QUICKSTART.md)
- **Complete Documentation:** [docs/INDEX.md](./INDEX.md)

---

**Last Updated:** March 5, 2026
**Version:** 2.0.0
**Maintainer:** Sarkari Path Team

