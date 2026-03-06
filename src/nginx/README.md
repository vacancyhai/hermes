# Nginx Reverse Proxy Service

Nginx acts as the single entry point for the entire Hermes platform, providing:
- **Reverse Proxy**: Routes requests to backend API and frontend applications
- **Load Balancing**: Distributes traffic across upstream servers
- **SSL/TLS Termination**: Handles HTTPS encryption/decryption
- **Security Headers**: Adds security headers to responses
- **Request Correlation**: Tracks requests with unique IDs
- **Response Compression**: Gzip compression for bandwidth optimization
- **Rate Limiting**: Protects against DDoS attacks

## Service Details

- **Container Name**: `hermes_nginx`
- **Image**: `nginx:alpine` (lightweight, ~42MB)
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Configuration**: Local file `nginx.conf` (in this folder)
- **SSL Certificates**: `ssl/` folder (in this folder)
- **Logs**: Persisted in Docker volume `nginx_logs`

## Upstream Services

Nginx proxies to two main services:

1. **Backend API** (`http://backend:5000`)
   - Routes: `/api/*`, `/ws/*` (WebSocket)
   - Handles job management, user auth, RBAC

2. **Frontend** (`http://frontend:8080`)
   - Routes: `/`, `/login`, `/dashboard`, etc.
   - Serves Jinja2 templates and static assets

## Quick Start

### Prerequisites

Before starting Nginx, ensure backend and frontend services are running:

```bash
cd src/backend && docker-compose up -d
cd src/frontend && docker-compose up -d
```

### Start Nginx Service

```bash
cd src/nginx
cp .env.example .env  # Configure if needed
docker-compose up -d
```

### Verify Nginx is Running

```bash
# Check container status
docker ps | grep hermes_nginx

# Test health endpoint
curl http://localhost:80/health

# View logs
docker-compose logs -f nginx
```

### Access Services

- **Frontend**: http://localhost/
- **API Documentation**: http://localhost/api/v1/docs
- **Health Check**: http://localhost/health

## Configuration

### Environment Variables (`.env`)

```bash
NGINX_HTTP_PORT=80           # HTTP port (forwarded from host)
NGINX_HTTPS_PORT=443         # HTTPS port (forwarded from host)
BACKEND_URL=http://backend:5000    # Backend service URL
FRONTEND_URL=http://frontend:8080  # Frontend service URL
RATE_LIMIT=10               # Requests per second (limiting)
LOG_LEVEL=info              # Nginx log level
```

### SSL/HTTPS Configuration

For production HTTPS setup:

1. **Generate SSL Certificate**:
```bash
# Self-signed (testing only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx_certs/key.pem -out nginx_certs/cert.pem

# Or use Let's Encrypt (recommended for production)
certbot certonly --standalone -d yourdomain.com
```

2. **Copy Certificates**:
```bash
cp /path/to/cert.pem ./nginx_certs/
cp /path/to/key.pem ./nginx_certs/
```

3. **Update nginx.conf**:
   - Uncomment HTTPS server block
   - Update certificate paths if needed
   - Rebuild Nginx: `docker-compose up -d --build`

4. **Enable HTTPS Redirect**:
   - Edit nginx.conf to redirect HTTP → HTTPS (already included, just uncomment)

### Security Headers

Nginx automatically adds these security headers:

```nginx
X-Frame-Options: DENY                           # Prevent clickjacking
X-Content-Type-Options: nosniff                 # Prevent MIME sniffing
X-XSS-Protection: 1; mode=block                 # XSS protection
Strict-Transport-Security: max-age=31536000     # HSTS (when HTTPS enabled)
Referrer-Policy: strict-origin-when-cross-origin  # Referrer policy
```

### Request Correlation

Every request gets a unique X-Request-ID header:

```nginx
proxy_set_header X-Request-ID $request_id;
```

This enables request tracking across backend logs without needing to parse logs.

## Performance Optimization

### Gzip Compression

Nginx compresses responses by content type:
- `text/*` - HTML, CSS, JavaScript
- `application/json` - API responses
- `image/svg+xml` - SVG graphics

Compression reduces bandwidth by 60-80% for text content.

### Connection Handling

- **Keepalive**: Reuses TCP connections to upstream servers
- **Buffering**: Buffers responses to allow backend to disconnect early
- **Timeouts**: 
  - Connect timeout: 60s
  - Read timeout: 60s
  - Send timeout: 60s

## Troubleshooting

### Port Already in Use

If port 80 or 443 is already in use:

1. Find what's using the port:
```bash
# macOS/Linux
lsof -i :80
lsof -i :443

# Find and kill process
kill -9 <PID>
```

2. Or change port in docker-compose.yml:
```yaml
ports:
  - "8000:80"  # Forward 8000 to container 80
  - "8443:443"
```

### Upstream Services Unavailable

If you see "504 Bad Gateway":

1. Check backend/frontend are running:
```bash
docker ps | grep hermes_
```

2. Restart dependent services:
```bash
cd src/nginx && docker-compose restart nginx
```

3. Check service connectivity:
```bash
# From within Nginx container
docker-compose exec nginx ping -c 1 backend
docker-compose exec nginx curl http://backend:5000/health
```

### SSL Certificate Issues

If HTTPS not working:

1. Verify certificate files exist:
```bash
ls -la ./nginx_certs/
```

2. Check file permissions:
```bash
chmod 644 ./nginx_certs/*.pem
```

3. Validate certificate:
```bash
openssl x509 -in ./nginx_certs/cert.pem -text -noout
```

## Networking

### Docker Networks

Nginx connects to two Docker networks:

1. **src_backend_network**: Communicates with backend service
2. **src_frontend_network**: Communicates with frontend service

This enables Nginx to route between the two independent services.

### External Network References

```yaml
networks:
  - src_backend_network    # External - created by backend service
  - src_frontend_network   # External - created by frontend service
```

Both networks must be created and running before Nginx starts.

## Common Operations

### Restart Nginx
```bash
docker-compose restart nginx
```

### Reload Configuration (without restart)
```bash
docker-compose exec nginx nginx -s reload
```

### Rebuild from nginx.conf changes
```bash
docker-compose up -d --build nginx
```

### Remove All Data
```bash
docker-compose down -v
```

## Integration with Full Stack

To run complete platform:

```bash
# Terminal 1: Start Backend
cd src/backend && docker-compose up -d

# Terminal 2: Start Frontend
cd src/frontend && docker-compose up -d

# Terminal 3: Start Nginx (load balancer)
cd src/nginx && docker-compose up -d

# Or use Makefile
make all-up
```

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│         External Users                   │
│       (Port 80/443)                     │
└────────────────┬────────────────────────┘
                 │
    ┌────────────▼────────────┐
    │   Nginx Reverse Proxy    │
    │   (Port 80/443)          │
    │ - SSL Termination        │
    │ - Request Routing        │
    │ - Load Balancing         │
    │ - Security Headers       │
    └────┬────────────────┬────┘
         │                │
    src_backend_network   src_frontend_network
         │                │
         │                │
    ┌────▼────┐      ┌────▼──────┐
    │ Backend  │      │ Frontend   │
    │ API      │      │ Service    │
    │ (5000)   │      │ (8080)     │
    └──────────┘      └────────────┘
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs nginx`
2. Verify configuration: `docker-compose exec nginx nginx -t`
3. Review [Project README](../../README.md) for full setup
4. Check Nginx documentation: https://nginx.org/en/docs/

## Related Services

- [Backend API](../backend/README.md) - Main application server
- [Frontend](../frontend/README.md) - Web UI application
