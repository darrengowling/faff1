#!/bin/bash

# UCL Auction One-Command Deployment Script
# Usage: ./deploy.sh [environment] [action]
# Example: ./deploy.sh production deploy
# Example: ./deploy.sh staging update

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default values
ENVIRONMENT=${1:-production}
ACTION=${2:-deploy}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if environment file exists
    if [[ ! -f ".env.${ENVIRONMENT}" ]]; then
        error "Environment file .env.${ENVIRONMENT} not found."
        error "Please create it from the template and configure your settings."
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Load environment variables
load_environment() {
    log "Loading environment configuration for: ${ENVIRONMENT}"
    
    # Copy environment file
    cp ".env.${ENVIRONMENT}" .env
    
    # Load environment variables
    set -a  # Automatically export all variables
    source .env
    set +a
    
    success "Environment loaded: ${ENVIRONMENT}"
}

# Backup database
backup_database() {
    if [[ "${ENVIRONMENT}" == "production" ]]; then
        log "Creating database backup..."
        
        # Create backup directory
        BACKUP_DIR="./backups/$(date +'%Y%m%d_%H%M%S')"
        mkdir -p "$BACKUP_DIR"
        
        # Backup MongoDB
        docker-compose exec -T mongodb mongodump --out /tmp/backup
        docker cp ucl-auction-mongodb:/tmp/backup "$BACKUP_DIR/"
        
        success "Database backup created: $BACKUP_DIR"
    fi
}

# Build and deploy
deploy_application() {
    log "Deploying UCL Auction application..."
    
    # Pull latest images
    docker-compose pull
    
    # Build application
    log "Building application..."
    docker-compose build --no-cache
    
    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose down
    
    # Start services
    log "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 30
    
    # Check health
    check_health
    
    success "Application deployed successfully!"
}

# Update existing deployment
update_application() {
    log "Updating UCL Auction application..."
    
    # Create backup first
    backup_database
    
    # Pull updates
    docker-compose pull
    
    # Build with latest changes
    docker-compose build
    
    # Rolling update
    log "Performing rolling update..."
    docker-compose up -d --no-deps app
    
    # Check health
    check_health
    
    success "Application updated successfully!"
}

# Check application health
check_health() {
    log "Checking application health..."
    
    # Wait for application to start
    sleep 10
    
    # Check MongoDB
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ismaster')" > /dev/null 2>&1; then
        success "MongoDB is healthy"
    else
        error "MongoDB health check failed"
        return 1
    fi
    
    # Check application
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        success "Application is healthy"
    else
        error "Application health check failed"
        return 1
    fi
    
    success "All health checks passed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create monitoring directory
    mkdir -p ./monitoring
    
    # Setup log rotation
    cat > ./monitoring/logrotate.conf << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose restart app
    endscript
}
EOF
    
    success "Monitoring setup completed"
}

# Initialize database with seed data
init_database() {
    log "Initializing database with seed data..."
    
    # Run seed script
    docker-compose exec -T app python seed_script.py
    
    success "Database initialized with seed data"
}

# Show deployment status
show_status() {
    log "Deployment Status:"
    echo
    
    # Show container status
    docker-compose ps
    echo
    
    # Show logs
    log "Recent logs:"
    docker-compose logs --tail=20
    echo
    
    # Show URLs
    log "Application URLs:"
    echo "Frontend: http://localhost:8000"
    echo "API: http://localhost:8000/api"
    echo "Health: http://localhost:8000/health"
    echo
}

# Rollback to previous version
rollback() {
    log "Rolling back to previous version..."
    
    # Stop current containers
    docker-compose down
    
    # Restore from backup
    if [[ -d "./backups" ]]; then
        LATEST_BACKUP=$(ls -t ./backups | head -n1)
        if [[ -n "$LATEST_BACKUP" ]]; then
            log "Restoring from backup: $LATEST_BACKUP"
            
            # Restore database
            docker-compose up -d mongodb
            sleep 10
            docker cp "./backups/$LATEST_BACKUP/backup" ucl-auction-mongodb:/tmp/
            docker-compose exec -T mongodb mongorestore /tmp/backup
            
            success "Database restored from backup"
        fi
    fi
    
    # Start application
    docker-compose up -d
    
    success "Rollback completed"
}

# Cleanup old resources
cleanup() {
    log "Cleaning up old resources..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove old backups (keep last 10)
    if [[ -d "./backups" ]]; then
        cd ./backups
        ls -t | tail -n +11 | xargs -r rm -rf
        cd ..
    fi
    
    success "Cleanup completed"
}

# Main execution
main() {
    log "🚀 UCL Auction Deployment Script"
    log "Environment: ${ENVIRONMENT}"
    log "Action: ${ACTION}"
    echo
    
    case $ACTION in
        "deploy")
            check_prerequisites
            load_environment
            setup_monitoring
            deploy_application
            init_database
            show_status
            ;;
        "update")
            check_prerequisites
            load_environment
            update_application
            show_status
            ;;
        "status")
            show_status
            ;;
        "rollback")
            rollback
            ;;
        "cleanup")
            cleanup
            ;;
        "backup")
            load_environment
            backup_database
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "stop")
            docker-compose down
            success "Application stopped"
            ;;
        "restart")
            docker-compose restart
            success "Application restarted"
            ;;
        *)
            echo "Usage: $0 [environment] [action]"
            echo "Environments: production, staging"
            echo "Actions: deploy, update, status, rollback, cleanup, backup, logs, stop, restart"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"