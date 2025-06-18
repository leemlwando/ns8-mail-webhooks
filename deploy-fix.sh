#!/bin/bash

#
# Complete deployment fix for ns8-mail-webhooks
# This script combines permission fixes, image rebuilding, and verification
#

set -e

SCRIPT_VERSION="1.0"
MODULE_NAME="ns8-mail-webhooks"
BACKEND_IMAGE="localhost/mail-webhooks-backend:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  NS8 Mail Webhooks Deployment  ${NC}"
    echo -e "${BLUE}  Version: ${SCRIPT_VERSION}                 ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_step() {
    echo -e "${YELLOW}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_prerequisites() {
    print_step "Checking prerequisites"
    
    # Check if we're in the right directory
    if [ ! -d "actions" ] || [ ! -d "api" ] || [ ! -f "environment" ]; then
        print_error "Not in the correct module directory"
        print_info "This script should be run from the module root directory"
        print_info "Expected structure: actions/, api/, environment file"
        exit 1
    fi
    
    # Check if we're the module user
    MODULE_USER=$(whoami)
    if [ "${MODULE_USER}" = "root" ]; then
        print_error "Do not run this script as root"
        print_info "Switch to the module user (e.g., su - mail-webhooks1)"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
    print_info "Module user: ${MODULE_USER}"
    print_info "Module directory: $(pwd)"
    echo
}

fix_permissions() {
    print_step "Fixing script permissions"
    
    local fixed_count=0
    
    # Fix action scripts
    while IFS= read -r -d '' script; do
        if [ ! -x "${script}" ]; then
            chmod +x "${script}"
            print_success "Fixed permissions: ${script}"
            fixed_count=$((fixed_count + 1))
        fi
    done < <(find actions -name "[0-9]*" -type f -print0)
    
    # Fix bin scripts
    if [ -d "bin" ]; then
        while IFS= read -r -d '' script; do
            if [ ! -x "${script}" ]; then
                chmod +x "${script}"
                print_success "Fixed permissions: ${script}"
                fixed_count=$((fixed_count + 1))
            fi
        done < <(find bin -type f -print0)
    fi
    
    # Fix shell scripts
    while IFS= read -r -d '' script; do
        if [ ! -x "${script}" ]; then
            chmod +x "${script}"
            print_success "Fixed permissions: ${script}"
            fixed_count=$((fixed_count + 1))
        fi
    done < <(find . -name "*.sh" -type f -print0)
    
    if [ ${fixed_count} -eq 0 ]; then
        print_success "All scripts already have correct permissions"
    else
        print_success "Fixed permissions on ${fixed_count} scripts"
    fi
    echo
}

fix_line_endings() {
    print_step "Fixing line endings"
    
    local fixed_count=0
    
    # Check and fix line endings for critical files
    while IFS= read -r -d '' file; do
        if file "${file}" 2>/dev/null | grep -q "CRLF"; then
            sed -i 's/\r$//' "${file}"
            print_success "Fixed line endings: ${file}"
            fixed_count=$((fixed_count + 1))
        fi
    done < <(find . -type f \( -name "*.service" -o -name "*.sh" -o -name "[0-9]*" \) -print0)
    
    if [ ${fixed_count} -eq 0 ]; then
        print_success "All files have correct line endings"
    else
        print_success "Fixed line endings in ${fixed_count} files"
    fi
    echo
}

stop_services() {
    print_step "Stopping existing services"
    
    if systemctl --user is-active mail-webhooks.service >/dev/null 2>&1; then
        systemctl --user stop mail-webhooks.service
        print_success "Stopped mail-webhooks.service"
    else
        print_info "mail-webhooks.service was not running"
    fi
    
    if systemctl --user is-active mail-monitor.service >/dev/null 2>&1; then
        systemctl --user stop mail-monitor.service
        print_success "Stopped mail-monitor.service"
    else
        print_info "mail-monitor.service was not running"
    fi
    echo
}

rebuild_backend_image() {
    print_step "Rebuilding backend image"
    
    # Remove existing image
    if podman image exists "${BACKEND_IMAGE}"; then
        print_info "Removing existing image: ${BACKEND_IMAGE}"
        podman rmi "${BACKEND_IMAGE}" || true
    fi
    
    # Clean up dangling images
    print_info "Cleaning up dangling images"
    podman image prune -f >/dev/null 2>&1 || true
    
    # Build new image
    if [ ! -d "api" ]; then
        print_error "API directory not found"
        exit 1
    fi
    
    cd api
    print_info "Building image: ${BACKEND_IMAGE}"
    
    if podman build -t "${BACKEND_IMAGE}" . >/dev/null 2>&1; then
        print_success "Successfully built backend image"
        
        # Get image ID for verification
        IMAGE_ID=$(podman image inspect "${BACKEND_IMAGE}" --format "{{.Id}}" | head -c 12)
        print_info "Image ID: ${IMAGE_ID}"
    else
        print_error "Failed to build backend image"
        cd ..
        exit 1
    fi
    
    cd ..
    echo
}

update_environment() {
    print_step "Updating environment configuration"
    
    # Backup existing environment file
    if [ -f "environment" ]; then
        cp environment environment.backup
        print_info "Backed up existing environment file"
    fi
    
    # Update or add backend image variable
    if grep -q "MAIL_WEBHOOKS_BACKEND_IMAGE" environment 2>/dev/null; then
        sed -i "s|MAIL_WEBHOOKS_BACKEND_IMAGE=.*|MAIL_WEBHOOKS_BACKEND_IMAGE=${BACKEND_IMAGE}|" environment
        print_success "Updated MAIL_WEBHOOKS_BACKEND_IMAGE in environment"
    else
        echo "MAIL_WEBHOOKS_BACKEND_IMAGE=${BACKEND_IMAGE}" >> environment
        print_success "Added MAIL_WEBHOOKS_BACKEND_IMAGE to environment"
    fi
    
    print_info "Environment variable: MAIL_WEBHOOKS_BACKEND_IMAGE=${BACKEND_IMAGE}"
    echo
}

start_services() {
    print_step "Starting services"
    
    # Reload systemd
    systemctl --user daemon-reload
    print_info "Reloaded systemd user daemon"
    
    # Start mail-webhooks service
    if systemctl --user start mail-webhooks.service; then
        print_success "Started mail-webhooks.service"
        
        # Wait a moment for startup
        sleep 3
        
        # Check status
        if systemctl --user is-active mail-webhooks.service >/dev/null 2>&1; then
            print_success "Service is running successfully"
        else
            print_error "Service failed to start properly"
            print_info "Checking service logs:"
            journalctl --user -u mail-webhooks.service -n 10 --no-pager
            return 1
        fi
    else
        print_error "Failed to start mail-webhooks.service"
        return 1
    fi
    echo
}

run_verification() {
    print_step "Running verification tests"
    
    local tests_passed=0
    local tests_total=5
    
    # Test 1: Service status
    if systemctl --user is-active mail-webhooks.service >/dev/null 2>&1; then
        print_success "Service is active"
        tests_passed=$((tests_passed + 1))
    else
        print_error "Service is not active"
    fi
    
    # Test 2: Backend image exists
    if podman image exists "${BACKEND_IMAGE}"; then
        print_success "Backend image exists"
        tests_passed=$((tests_passed + 1))
    else
        print_error "Backend image not found"
    fi
    
    # Test 3: API health check
    if curl -s --connect-timeout 5 http://127.0.0.1:20080/api/health >/dev/null 2>&1; then
        print_success "API health endpoint responding"
        tests_passed=$((tests_passed + 1))
    else
        print_error "API health endpoint not responding"
    fi
    
    # Test 4: Configuration action
    if [ -x "actions/get-configuration/20read" ] && ./actions/get-configuration/20read >/dev/null 2>&1; then
        print_success "Configuration action working"
        tests_passed=$((tests_passed + 1))
    else
        print_error "Configuration action failed"
    fi
    
    # Test 5: No recent errors in logs
    ERROR_COUNT=$(journalctl --user -u mail-webhooks.service -n 20 --no-pager 2>/dev/null | grep -i error | wc -l)
    if [ ${ERROR_COUNT} -eq 0 ]; then
        print_success "No errors in recent logs"
        tests_passed=$((tests_passed + 1))
    else
        print_error "Found ${ERROR_COUNT} errors in recent logs"
    fi
    
    echo
    print_info "Verification Results: ${tests_passed}/${tests_total} tests passed"
    
    if [ ${tests_passed} -eq ${tests_total} ]; then
        print_success "All verification tests passed!"
        return 0
    else
        print_error "Some verification tests failed"
        return 1
    fi
}

print_summary() {
    echo
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Deployment Summary            ${NC}"
    echo -e "${BLUE}================================${NC}"
    
    print_info "Module: ${MODULE_NAME}"
    print_info "User: $(whoami)"
    print_info "Backend Image: ${BACKEND_IMAGE}"
    print_info "Service Status: $(systemctl --user is-active mail-webhooks.service 2>/dev/null || echo 'inactive')"
    
    if systemctl --user is-active mail-webhooks.service >/dev/null 2>&1; then
        echo
        print_success "🎉 Deployment completed successfully!"
        print_info "The ns8-mail-webhooks module is now running correctly."
        echo
        print_info "You can access the API at: http://127.0.0.1:20080/api/health"
        print_info "Check service logs with: journalctl --user -u mail-webhooks.service -f"
    else
        echo
        print_error "❌ Deployment completed with issues"
        print_info "Please check the service logs for details:"
        print_info "journalctl --user -u mail-webhooks.service -n 20"
    fi
    echo
}

# Main execution
main() {
    print_header
    
    check_prerequisites
    fix_permissions
    fix_line_endings
    stop_services
    rebuild_backend_image
    update_environment
    start_services
    
    if run_verification; then
        print_summary
        exit 0
    else
        print_summary
        exit 1
    fi
}

# Run main function
main "$@"
