# Monitoring Stack Service

Comprehensive observability solution providing:
- **Metrics Collection**: Prometheus gathers metrics from all services
- **Visualization**: Grafana dashboards for real-time monitoring
- **Alerting**: AlertManager routes critical alerts to Slack, Email, PagerDuty
- **System Monitoring**: Node Exporter collects OS-level metrics
- **Database Monitoring**: PostgreSQL & Redis exporters track database health
- **Container Monitoring**: cAdvisor monitors Docker container metrics
- **Reverse Proxy Monitoring**: Nginx Exporter tracks traffic patterns

## Services Overview

| Service | Port | Purpose |
|---------|------|---------|
| **Prometheus** | 9090 | Time-series metrics database |
| **Grafana** | 3000 | Visualization & dashboarding |
| **AlertManager** | 9093 | Alert routing & notifications |
| **Node Exporter** | 9100 | System metrics (CPU, Memory, Disk) |
| **Postgres Exporter** | 9187 | PostgreSQL performance metrics |
| **Redis Exporter** | 9121 | Redis cache/queue metrics |
| **Nginx Exporter** | 9113 | Nginx reverse proxy metrics |
| **cAdvisor** | 8080 | Docker container metrics |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│             Monitoring Infrastructure                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Prometheus (9090)                                      │ │
│  │ - Time-series database                                │ │
│  │ - Scrapes metrics every 15s from 8 targets            │ │
│  │ - Stores 30 days of data                              │ │
│  │ - Evaluates alert rules every 15s                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                         │                                    │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │ Grafana (3000)                    AlertManager (9093)  │  │
│  │ - Dashboard creation              │ - Alert routing    │  │
│  │ - Alert visualization             │ - Slack webhook    │  │
│  │ - Pre-provisioned dashboards      │ - Email sending    │  │
│  │                                   │ - PagerDuty        │  │
│  └───────────────────────────────────┴──────────────────┘  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                    Metric Exporters                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Monitored Services                       │  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌──────────┐  ┌──────────┐         │  │
│  │  │Backend API  │  │PostgreSQL│  │  Redis   │         │  │
│  │  │  (5000)     │  │ (5432)   │  │ (6379)   │         │  │
│  │  └─────────────┘  └──────────┘  └──────────┘         │  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌──────────┐  ┌──────────┐         │  │
│  │  │   Nginx     │  │  System  │  │ Docker   │         │  │
│  │  │  (9113)     │  │ (9100)   │  │(8080)    │         │  │
│  │  └─────────────┘  └──────────┘  └──────────┘         │  │
│  │                                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

Ensure backend and Nginx services are running:

```bash
cd src/backend && docker-compose up -d
cd src/nginx && docker-compose up -d  # Optional but recommended
```

### Start Monitoring Stack

```bash
cd src/monitoring
cp .env.example .env       # Review and customize configuration
docker-compose up -d       # Start all 8 monitoring services
```

### Verify Services

```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f

# Test Prometheus
curl http://localhost:9090/-/healthy

# Test Grafana  
curl http://localhost:3000/api/health

# Test AlertManager
curl http://localhost:9093/-/healthy
```

## Access Services

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| **Grafana** | http://localhost:3000 | admin / securepassword123 |
| **Prometheus** | http://localhost:9090 | No auth | 
| **AlertManager** | http://localhost:9093 | No auth |
| **Node Exporter** | http://localhost:9100/metrics | No auth |
| **Postgres Exporter** | http://localhost:9187/metrics | No auth |
| **Redis Exporter** | http://localhost:9121/metrics | No auth |
| **Nginx Exporter** | http://localhost:9113/metrics | No auth |
| **cAdvisor** | http://localhost:8080 | No auth |

## Configuration

### Environment Variables (`.env`)

```bash
# Prometheus
PROMETHEUS_PORT=9090           # Access port
PROMETHEUS_RETENTION=30d       # Data retention (30 days)
PROMETHEUS_EVALUATION_INTERVAL=15s  # Alert evaluation frequency
PROMETHEUS_SCRAPE_INTERVAL=15s      # Metrics scrape frequency

# Grafana
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin       # Change this!
GRAFANA_ADMIN_PASSWORD=<password>  # Required - use strong password!

# AlertManager
ALERTMANAGER_PORT=9093

# Slack Alerts (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#alerts

# Email Alerts (Optional)
EMAIL_CRITICAL_ALERTS=critical@example.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# PagerDuty Alerts (Optional)
PAGERDUTY_SERVICE_KEY=<your-key>
```

### Create .env from Template

```bash
cd src/monitoring
cp .env.example .env
nano .env  # Edit with your settings
docker-compose restart  # Apply changes
```

## Metrics Collection

### Prometheus Scrape Targets

Prometheus collects metrics from:

1. **Backend API** (http://backend:5000/metrics)
   - API request latency, error rates
   - Database query performance
   - Celery task metrics
   - Application-specific metrics

2. **PostgreSQL Exporter** (http://postgres_exporter:9187)
   - Connection counts
   - Slow queries
   - Table/index statistics
   - Cache hit ratio
   - Disk usage

3. **Redis Exporter** (http://redis_exporter:9121)
   - Memory usage
   - Key counts
   - Eviction stats
   - Connection info
   - Command latency

4. **Nginx Exporter** (http://nginx_exporter:9113)
   - Active connections
   - Request throughput
   - Response status codes
   - Upstream health

5. **Node Exporter** (http://node_exporter:9100)
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network traffic
   - Load average

6. **cAdvisor** (http://cadvisor:8080)
   - Container CPU usage
   - Container memory usage
   - Container network stats
   - Volume usage

7. **Frontend** (http://localhost:8080/metrics) - Optional
   - Response times
   - Error rates
   - Page load metrics

8. **Celery** (via backend metrics)
   - Task queue depth
   - Task success/failure rates
   - Worker availability

### View Metrics in Prometheus

```
Query examples in Prometheus (http://localhost:9090):

# API Request Rate
rate(http_request_duration_seconds_count[5m])

# 95th Percentile Response Time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Database Connections
pg_stat_activity_count

# Redis Memory Usage
redis_memory_used_bytes

# Nginx Active Connections
nginx_active_connections

# System CPU Usage
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

## Grafana Dashboards

### Pre-Provisioned Dashboards

Default dashboards automatically available:

1. **System Overview**
   - CPU, Memory, Disk usage across all hosts
   - Network traffic
   - Load averages

2. **Docker Containers**
   - Container count by status
   - Memory and CPU by container
   - Network I/O per container

3. **PostgreSQL**
   - Connections by state
   - Active queries
   - Cache hit ratio
   - Slow queries

4. **Redis**
   - Memory usage
   - Key count trends
   - Command latency
   - Eviction rate

5. **Nginx**
   - Request rate
   - Response codes distribution
   - Upstream health
   - Connection states

### Creating Custom Dashboards

1. **Login to Grafana**: http://localhost:3000
2. **Click "Create"** → New Dashboard
3. **Add Panel** → Prometheus data source
4. **Enter PromQL query** (examples below)
5. **Customize** visualization (graph, gauge, table)
6. **Save** dashboard

Example custom dashboard:

```yaml
Title: API Performance
Panels:
  1. Request Rate (requests/sec)
     - Query: rate(http_request_duration_seconds_count[5m])
  2. Error Rate (%)
     - Query: rate(http_requests_total{status=~"5.."}[5m]) * 100
  3. P95 Latency (ms)
     - Query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
  4. Top Endpoints by Traffic
     - Query: topk(10, rate(http_request_duration_seconds_count{le="+Inf"}[5m]))
```

## Alert Rules

### Pre-configured Alert Rules

40+ alert rules covering:

**API Alerts:**
- `HighErrorRate` - API error rate > 1% for 5min
- `HighResponseTime` - P95 latency > 500ms
- `APIDowntime` - API unreachable for 2 minutes

**Database Alerts:**
- `PostgreSQLDown` - PostgreSQL service unavailable
- `SlowQueries` - Queries taking > 50s
- `TooManyConnections` - > 90% of max connections
- `DiskAlmostFull` - < 10% free space

**Cache Alerts:**
- `RedisDown` - Redis service unavailable
- `RedisMemoryHigh` - > 85% memory usage
- `RedisEvictions` - Keys being evicted
- `RedisPIAHigh` - > 100k pipeline items

**System Alerts:**
- `HighCpuUsage` - > 85% for 10 minutes
- `HighMemoryUsage` - > 90% used
- `DiskFull` - > 85% usage
- `IOWaitHigh` - I/O wait > 30%
- `LoadHigh` - Load average > 4

**Container Alerts:**
- `ContainerCrashed` - Container restarted recently
- `ContainerMemoryLimitApproaching` - > 90% of limit

**Celery Alerts:**
- `CeleryWorkerDown` - Celery worker offline
- `CeleryTasksQueued` - > 1000 tasks waiting
- `CeleryHighFailureRate` - Task failure ratio too high

### Alert Severity Levels

- **Critical** (Immediate action required)
  - Service down
  - Data loss risk
  - Security breach
  - Business impact

- **Warning** (Investigate soon)
  - Performance degradation
  - Resource constraints
  - Configuration issues

### Custom Alert Rules

To add custom alerts:

1. **Edit alert rules**:
   ```bash
   nano alert_rules.yml
   ```

2. **Add new rule**:
   ```yaml
   - alert: MyCustomAlert
     expr: some_metric > threshold
     for: 5m
     annotations:
       summary: "Description"
       description: "{{ $labels.instance }}: {{ $value }}"
   ```

3. **Reload Prometheus**:
   ```bash
   docker-compose exec prometheus kill -HUP 1
   ```

## Alert Routing

### Configure Notifications

Alerts are routed based on severity and service:

**Critical Alerts** → PagerDuty + Slack + Email (immediate)
**Warnings** → Slack + Email (within 5 minutes)
**Info** → Slack only (summary at end of hour)

### Setup Slack Integration

1. **Create Slack Webhook**:
   - Go to: https://api.slack.com/messaging/webhooks
   - Create new webhook
   - Copy webhook URL

2. **Add to `.env`**:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   SLACK_CHANNEL=#alerts
   ```

3. **Restart AlertManager**:
   ```bash
   docker-compose restart alertmanager
   ```

### Setup Email Alerts

1. **Configure SMTP**:
   ```bash
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

2. **For Gmail**, use [App Passwords](https://myaccount.google.com/apppasswords)

3. **Test email**:
   ```bash
   docker-compose logs alertmanager | grep "sending email"
   ```

### Setup PagerDuty Integration

1. **Create PagerDuty Service**
2. **Get Service Key** from integration settings
3. **Add to `.env`**:
   ```bash
   PAGERDUTY_SERVICE_KEY=your-service-key
   ```

4. **Restart AlertManager**:
   ```bash
   docker-compose restart alertmanager
   ```

## Common Operations

### View Alert Status

```bash
# In Prometheus UI (http://localhost:9090/alerts)
# Shows firing and pending alerts

# Via API
curl http://localhost:9090/api/v1/alerts
```

### Test Alert Rule

```bash
# Execute a query in Prometheus
# If it returns data for > "for" duration, alert fires

# Example: Test high CPU alert
curl 'http://localhost:9090/api/v1/query?query=node_cpu_seconds_total{mode="system"}'
```

### Silence an Alert

In Grafana/AlertManager:
1. Go to Alerts
2. Find the alert
3. Click "Silence" 
4. Set duration
5. Acknowledge

### View AlertManager Status

```bash
# Check configuration
curl http://localhost:9093/api/v1/status

# View silences
curl http://localhost:9093/api/v1/silences

# View alerts
curl http://localhost:9093/api/v1/alerts
```

## Data Retention

### Prometheus Retention

Default: 30 days of metrics

To adjust:
```bash
PROMETHEUS_RETENTION=60d  # Store 60 days
docker-compose down
docker volume rm monitoring_prometheus_data  # Delete old data
docker-compose up -d
```

### Disk Usage Estimation

- 15s scrape interval
- 8 scrape targets with ~100 metrics each
- Approximately 1.5GB per week
- 30-day retention ≈ 6GB

Monitor disk space:
```bash
docker exec prometheus df -h /prometheus
```

## Troubleshooting

### Prometheus Not Scraping

```bash
# Check targets
curl http://localhost:9090/api/v1/targets

# Look for unreachable targets
# Verify services are running: docker ps | grep hermes_
```

### Grafana Can't Connect to Prometheus

```bash
# Test from Grafana container
docker-compose exec grafana curl http://prometheus:9090/-/healthy

# Verify network connectivity
docker network inspect src_backend_network
```

### Alert Not Firing

```bash
# Validate alert expression syntax
curl 'http://localhost:9090/api/v1/query?query=your_metric'

# Check alert group evaluation
curl http://localhost:9090/api/v1/rules

# View alert logs
docker-compose logs prometheus | grep -i alert
```

### AlertManager Not Sending

```bash
# Check configuration
curl http://localhost:9093/api/v1/status

# Verify webhook URL (for Slack)
docker-compose logs alertmanager | grep webhook

# Test SMTP (for email)
docker-compose logs alertmanager | grep "email"
```

### High Memory Usage

If Prometheus memory is high:

```bash
# Check retention size
docker-compose logs prometheus | grep retention

# Reduce retention
PROMETHEUS_RETENTION=14d
docker-compose restart prometheus
```

## Performance Tuning

### Scrape Intervals

For faster metrics (more data):
```bash
PROMETHEUS_SCRAPE_INTERVAL=5s  # Every 5 seconds (default: 15s)
```

For better performance (less data):
```bash
PROMETHEUS_SCRAPE_INTERVAL=60s  # Every 60 seconds
```

### Alert Evaluation

```bash
PROMETHEUS_EVALUATION_INTERVAL=30s  # Evaluate every 30s (default: 15s)
```

## Integration with Full Stack

To run complete platform with monitoring:

```bash
# Terminal 1: Start Backend
cd src/backend && docker-compose up -d

# Terminal 2: Start Frontend  
cd src/frontend && docker-compose up -d

# Terminal 3: Start Nginx
cd src/nginx && docker-compose up -d

# Terminal 4: Start Monitoring
cd src/monitoring && docker-compose up -d

# Or use Makefile
make all-up
```

## Backup & Restore

### Backup Monitoring Data

```bash
# Backup volumes
docker run --rm -v monitoring_prometheus_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz -C /data .

docker run --rm -v monitoring_grafana_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/grafana-backup.tar.gz -C /data .
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore volumes
docker volume rm monitoring_prometheus_data monitoring_grafana_data
docker volume create monitoring_prometheus_data
docker volume create monitoring_grafana_data

docker run --rm -v monitoring_prometheus_data:/data \
  -v $(pwd):/backup alpine tar xzf /backup/prometheus-backup.tar.gz -C /data

docker run --rm -v monitoring_grafana_data:/data \
  -v $(pwd):/backup alpine tar xzf /backup/grafana-backup.tar.gz -C /data

# Restart
docker-compose up -d
```

## Resources

- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [AlertManager Docs](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Node Exporter Metrics](https://github.com/prometheus/node_exporter)
- [PostgreSQL Exporter](https://github.com/prometheuscommun/postgres_exporter)

## Support

For issues:
1. Check service logs: `docker-compose logs <service>`
2. Verify connectivity: Test metric endpoints directly
3. Review configuration files in this folder (*.yml files)
4. Check [Project README](../../README.md)
