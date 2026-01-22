# Production Deployment Guide

## 🚀 Quick Deploy

### Docker Compose (Recommended for Single Server)

```bash
# 1. Clone repository
git clone https://github.com/moroianu13/job-market-intelligence.git
cd job-market-intelligence

# 2. Create production environment file
cp .env.example .env.production
# Edit .env.production with your credentials

# 3. Run deployment script
./deployment/deploy.sh production
```

### Kubernetes (Recommended for Scale)

```bash
# 1. Update secrets in deployment/kubernetes.yml
kubectl create secret generic app-secrets \
  --from-literal=ADZUNA_APP_ID=your_id \
  --from-literal=ADZUNA_APP_KEY=your_key \
  -n job-intelligence

# 2. Apply configuration
kubectl apply -f deployment/kubernetes.yml

# 3. Get service URL
kubectl get svc streamlit-service -n job-intelligence
```

### AWS (Terraform + ECS)

```bash
# 1. Initialize Terraform
cd deployment/terraform
terraform init

# 2. Plan deployment
terraform plan -out=tfplan

# 3. Apply
terraform apply tfplan

# 4. Push Docker image to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag job-market-intelligence:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/job-market-intelligence:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/job-market-intelligence:latest
```

---

## 🏗️ Architecture

### Production Stack

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (SSL/Reverse Proxy)                │
│                    - Rate limiting                           │
│                    - Load balancing                          │
│                    - SSL termination                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────┐
│                   Streamlit UI (2 replicas)               │
│                   - Interactive dashboard                  │
│                   - Job exploration                        │
│                   - Ghost job visualization                │
└───────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────┐
│                     Data Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ PostgreSQL  │  │    Redis    │  │   S3/EFS    │      │
│  │  (Metadata) │  │   (Cache)   │  │   (Files)   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└───────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────┐
│                Pipeline Scheduler (CronJob)               │
│  - Weekly data collection                                 │
│  - ML model training                                      │
│  - Ghost job detection                                    │
│  - Report generation                                      │
└───────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────┐
│                  Monitoring & Logging                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ Prometheus  │  │   Grafana   │  │  CloudWatch │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└───────────────────────────────────────────────────────────┘
```

---

## 🔐 Security

### 1. Secrets Management

**Never commit secrets!** Use environment variables or secret managers:

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name job-intelligence/adzuna \
  --secret-string '{"app_id":"xxx","app_key":"yyy"}'

# Kubernetes Secrets
kubectl create secret generic app-secrets \
  --from-literal=ADZUNA_APP_ID=xxx \
  --from-literal=ADZUNA_APP_KEY=yyy
```

### 2. Network Security

- ✅ Use HTTPS (SSL/TLS)
- ✅ Enable firewall rules
- ✅ Whitelist IP addresses
- ✅ Use VPC/private subnets
- ✅ Enable rate limiting

### 3. Container Security

```bash
# Scan for vulnerabilities
docker scan job-market-intelligence:latest

# Run as non-root user (already configured)
docker run --user 1000:1000 job-market-intelligence:latest
```

---

## 📊 Monitoring

### Grafana Dashboards

Access at `http://your-server:3000`

**Pre-configured Dashboards:**
1. **Pipeline Health**: Success rate, execution time, errors
2. **Data Metrics**: Jobs collected, ghost jobs detected, countries covered
3. **System Resources**: CPU, memory, disk usage
4. **API Usage**: Adzuna API calls, rate limits

### Prometheus Metrics

Access at `http://your-server:9090`

**Key Metrics:**
- `pipeline_execution_duration_seconds`: Pipeline run time
- `jobs_collected_total`: Total jobs fetched
- `ghost_jobs_detected_total`: Ghost jobs found
- `api_requests_total`: API call count

### Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f streamlit

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 pipeline
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

**Automated on every push to `main`:**

1. **Test Suite** (`ci-cd.yml`)
   - Run all 53 tests
   - Code coverage report
   - Linting (flake8, black)
   - Security scanning (Trivy)

2. **Build & Deploy** (`ci-cd.yml`)
   - Build Docker image
   - Push to Docker Hub/ECR
   - Deploy to staging
   - Health checks

3. **Scheduled Pipeline** (`scheduled-pipeline.yml`)
   - Every Monday 2 AM UTC
   - Fetch new data
   - Train ML models
   - Detect ghost jobs
   - Upload reports as artifacts

### Manual Deployment

```bash
# Trigger pipeline manually
gh workflow run scheduled-pipeline.yml

# Deploy to production
gh workflow run ci-cd.yml --ref main
```

---

## 🗄️ Database

### PostgreSQL Schema (Optional)

```sql
-- Pipeline execution tracking
CREATE TABLE pipeline_runs (
    id SERIAL PRIMARY KEY,
    run_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    jobs_fetched INT,
    ghost_jobs_detected INT,
    execution_time_seconds INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Job metadata index
CREATE TABLE job_metadata (
    job_fingerprint VARCHAR(40) PRIMARY KEY,
    first_seen DATE NOT NULL,
    last_seen DATE NOT NULL,
    is_ghost_job BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Backups

**Automated daily backups:**

```bash
# Backup script (runs daily via cron)
docker-compose exec postgres pg_dump -U admin job_intelligence | gzip > backups/$(date +%Y%m%d).sql.gz

# Restore
gunzip < backups/20260122.sql.gz | docker-compose exec -T postgres psql -U admin job_intelligence
```

---

## 📈 Scaling

### Horizontal Scaling

**Kubernetes HPA:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: streamlit-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: streamlit-ui
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Vertical Scaling

Adjust resources in `docker-compose.prod.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'        # Increase for heavy workloads
      memory: 8G
```

---

## 🔧 Configuration

### Environment Variables

```bash
# API Credentials
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0

# Application
LOG_LEVEL=INFO
ENVIRONMENT=production

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_PASSWORD=secure_password

# Storage
S3_BUCKET=job-intelligence-data
AWS_REGION=us-east-1
```

---

## 🆘 Troubleshooting

### Common Issues

**1. Pipeline fails to start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs pipeline

# Verify credentials
docker-compose -f docker-compose.prod.yml exec pipeline python -c "from config import validate_api_credentials; print(validate_api_credentials())"
```

**2. Streamlit won't connect**
```bash
# Check if service is running
docker-compose -f docker-compose.prod.yml ps streamlit

# Test health endpoint
curl http://localhost:8501/_stcore/health
```

**3. Out of disk space**
```bash
# Clean old Docker images
docker system prune -a

# Remove old snapshots (keep last 3 months)
find data/curated/snapshots/ -type d -mtime +90 -exec rm -rf {} \;
```

**4. Database connection issues**
```bash
# Check PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U admin -d job_intelligence -c "SELECT version();"

# Reset database
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d postgres
```

---

## 📞 Support

- **Issues**: https://github.com/moroianu13/job-market-intelligence/issues
- **Discussions**: https://github.com/moroianu13/job-market-intelligence/discussions
- **Email**: See repository for contact info

---

## ✅ Pre-Deployment Checklist

- [ ] Environment variables configured
- [ ] API credentials validated
- [ ] SSL certificates obtained
- [ ] Database initialized
- [ ] Backups configured
- [ ] Monitoring dashboards set up
- [ ] Health checks passing
- [ ] All tests passing (53/53)
- [ ] Security scan completed
- [ ] Documentation reviewed

---

**Ready for production!** 🚀
