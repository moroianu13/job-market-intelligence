#!/bin/bash

# Project Health Check Script
# Verifies the project is ready for deployment

echo "🔍 Job Market Intelligence - Health Check"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

# Check function
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $1${NC}"
        ((FAILED++))
    fi
}

# 1. Python version
echo "Checking Python version..."
python3 --version | grep -q "3.10\|3.11\|3.12"
check "Python 3.10+ installed"

# 2. Dependencies
echo "Checking dependencies..."
pip list | grep -q "pandas"
check "Python dependencies installed"

# 3. Environment file
echo "Checking configuration..."
[ -f ".env" ]
check ".env file exists"

if [ -f ".env" ]; then
    grep -q "ADZUNA_APP_ID" .env
    check "ADZUNA_APP_ID configured"
    
    grep -q "ADZUNA_APP_KEY" .env
    check "ADZUNA_APP_KEY configured"
fi

# 4. Directory structure
echo "Checking directory structure..."
[ -d "data" ] && [ -d "models" ] && [ -d "reports" ]
check "Required directories exist"

# 5. Tests
echo "Running tests..."
pytest --tb=short -q > /dev/null 2>&1
check "All tests passing (53/53)"

# 6. Docker
echo "Checking Docker..."
command -v docker > /dev/null 2>&1
check "Docker installed"

command -v docker-compose > /dev/null 2>&1
check "Docker Compose installed"

# 7. Git
echo "Checking Git..."
git status > /dev/null 2>&1
check "Git repository initialized"

git remote -v | grep -q "github.com"
check "GitHub remote configured"

# 8. Key files
echo "Checking key files..."
FILES=("config.py" "orchestration/run_pipeline.py" "app/streamlit_app.py" "processing/fingerprints.py" "analysis/repost_detector.py")
for file in "${FILES[@]}"; do
    [ -f "$file" ]
    check "File exists: $file"
done

# 9. Deployment files
echo "Checking deployment configuration..."
DEPLOY_FILES=(".github/workflows/ci-cd.yml" "deployment/kubernetes.yml" "deployment/terraform/main.tf" "docker-compose.prod.yml" "Dockerfile.prod" "DEPLOYMENT.md")
for file in "${DEPLOY_FILES[@]}"; do
    [ -f "$file" ]
    check "Deployment file: $file"
done

# 10. Documentation
echo "Checking documentation..."
DOCS=("README.md" "QUICKSTART.md" "DEPLOYMENT.md" "GHOST_JOBS_FEATURE.md")
for doc in "${DOCS[@]}"; do
    [ -f "$doc" ]
    check "Documentation: $doc"
done

# Summary
echo ""
echo "=========================================="
echo "Summary:"
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Project is ready for deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review DEPLOYMENT.md for deployment options"
    echo "2. Run: ./deployment/deploy.sh production"
    echo "3. Or: kubectl apply -f deployment/kubernetes.yml"
    echo "4. Or: docker-compose -f docker-compose.prod.yml up -d"
    exit 0
else
    echo -e "${YELLOW}⚠️  Please fix the failed checks before deploying${NC}"
    exit 1
fi
