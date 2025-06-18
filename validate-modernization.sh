#!/bin/bash

#
# Validation script for NS8 Mail Webhooks modernization
# Tests all aspects of the modernized module structure
#

set -e

echo "🔍 Validating NS8 Mail Webhooks Modernization"
echo "============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

validate_file() {
    local file=$1
    local description=$2
    
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✓${NC} $description: $file"
        return 0
    else
        echo -e "${RED}✗${NC} $description: $file (MISSING)"
        return 1
    fi
}

validate_executable() {
    local file=$1
    local description=$2
    
    if [[ -f "$file" && -x "$file" ]]; then
        echo -e "${GREEN}✓${NC} $description: $file (executable)"
        return 0
    elif [[ -f "$file" ]]; then
        echo -e "${YELLOW}⚠${NC} $description: $file (not executable)"
        return 1
    else
        echo -e "${RED}✗${NC} $description: $file (MISSING)"
        return 1
    fi
}

validate_syntax() {
    local file=$1
    local description=$2
    local type=$3
    
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}✗${NC} $description: $file (MISSING)"
        return 1
    fi
    
    case $type in
        "python")
            # Try python3 first, then skip if not available
            if command -v python3 >/dev/null 2>&1; then
                if python3 -m py_compile "$file" 2>/dev/null; then
                    echo -e "${GREEN}✓${NC} $description: $file (valid Python syntax)"
                    return 0
                else
                    echo -e "${RED}✗${NC} $description: $file (Python syntax error)"
                    return 1
                fi
            else
                echo -e "${YELLOW}⚠${NC} $description: $file (Python not available, skipping syntax check)"
                return 0
            fi
            ;;
        "bash")
            if bash -n "$file" 2>/dev/null; then
                echo -e "${GREEN}✓${NC} $description: $file (valid Bash syntax)"
                return 0
            else
                echo -e "${RED}✗${NC} $description: $file (Bash syntax error)"
                return 1
            fi
            ;;
        "json")
            # Try python3 first, then fallback to simple syntax check
            if command -v python3 >/dev/null 2>&1; then
                if python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
                    echo -e "${GREEN}✓${NC} $description: $file (valid JSON)"
                    return 0
                else
                    echo -e "${RED}✗${NC} $description: $file (JSON syntax error)"
                    return 1
                fi
            else
                # Simple JSON validation - check for basic structure
                if grep -q '^{' "$file" && grep -q '}$' "$file"; then
                    echo -e "${YELLOW}⚠${NC} $description: $file (basic JSON structure OK, full validation skipped)"
                    return 0
                else
                    echo -e "${RED}✗${NC} $description: $file (invalid JSON structure)"
                    return 1
                fi
            fi
            ;;
    esac
}

check_ns8_patterns() {
    local file=$1
    local description=$2
    
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}✗${NC} $description: $file (MISSING)"
        return 1
    fi
    
    # Check for NS8 patterns
    local has_agent_import=false
    local has_error_handling=false
    
    if grep -q "import agent" "$file" 2>/dev/null; then
        has_agent_import=true
    fi
    
    if grep -q -E "(try:|except:|sys\.exit)" "$file" 2>/dev/null; then
        has_error_handling=true
    fi
    
    if [[ "$has_agent_import" == true && "$has_error_handling" == true ]]; then
        echo -e "${GREEN}✓${NC} $description: follows NS8 patterns"
        return 0
    elif [[ "$has_agent_import" == true ]]; then
        echo -e "${YELLOW}⚠${NC} $description: has agent import but missing error handling"
        return 1
    else
        echo -e "${YELLOW}⚠${NC} $description: may not follow all NS8 patterns"
        return 1
    fi
}

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0

run_check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if "$@"; then
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    fi
}

echo
echo "📁 Checking core module structure..."
run_check validate_file "build-images.sh" "Build script"
run_check validate_executable "build-images.sh" "Build script executable"
run_check validate_syntax "build-images.sh" "Build script syntax" "bash"

echo
echo "🔧 Checking create-module actions..."
run_check validate_executable "imageroot/actions/create-module/10grants" "Grants action"
run_check validate_executable "imageroot/actions/create-module/20env" "Environment setup"
run_check validate_syntax "imageroot/actions/create-module/10grants" "Grants syntax" "python"
run_check validate_syntax "imageroot/actions/create-module/20env" "Environment syntax" "python"
run_check check_ns8_patterns "imageroot/actions/create-module/10grants" "Grants NS8 patterns"
run_check check_ns8_patterns "imageroot/actions/create-module/20env" "Environment NS8 patterns"

echo
echo "⚙️  Checking configure-module actions..."
run_check validate_executable "imageroot/actions/configure-module/01hostname_validation" "Hostname validation"
run_check validate_executable "imageroot/actions/configure-module/02mongodb_validation" "MongoDB validation"
run_check validate_executable "imageroot/actions/configure-module/10env" "Environment setup"
run_check validate_executable "imageroot/actions/configure-module/20configure" "Traefik configuration"
run_check validate_executable "imageroot/actions/configure-module/30ensure_backend_image" "Backend image script"
run_check validate_executable "imageroot/actions/configure-module/80start_services" "Service startup"

run_check validate_syntax "imageroot/actions/configure-module/01hostname_validation" "Hostname validation syntax" "python"
run_check validate_syntax "imageroot/actions/configure-module/02mongodb_validation" "MongoDB validation syntax" "python"
run_check validate_syntax "imageroot/actions/configure-module/10env" "Environment syntax" "python"
run_check validate_syntax "imageroot/actions/configure-module/20configure" "Traefik config syntax" "python"
run_check validate_syntax "imageroot/actions/configure-module/30ensure_backend_image" "Backend image syntax" "python"
run_check validate_syntax "imageroot/actions/configure-module/80start_services" "Service startup syntax" "bash"

run_check validate_file "imageroot/actions/configure-module/validate-input.json" "Configuration schema"
run_check validate_syntax "imageroot/actions/configure-module/validate-input.json" "Schema syntax" "json"

echo
echo "🗑️  Checking destroy-module actions..."
run_check validate_executable "imageroot/actions/destroy-module/20destroy" "Destroy action"
run_check validate_syntax "imageroot/actions/destroy-module/20destroy" "Destroy syntax" "python"
run_check check_ns8_patterns "imageroot/actions/destroy-module/20destroy" "Destroy NS8 patterns"

echo
echo "🔧 Checking SystemD service files..."
run_check validate_file "imageroot/systemd/user/mail-webhooks.service" "Rootless service file"
run_check validate_file "imageroot/systemd/system/mail-webhooks@.service" "Rootfull service file"

echo
echo "📊 Checking for BACKEND_IMAGE references..."
if grep -r "BACKEND_IMAGE" imageroot/systemd/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} SystemD services use BACKEND_IMAGE environment variable"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}✗${NC} SystemD services missing BACKEND_IMAGE references"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo
echo "🔍 Checking for deprecated patterns..."
DEPRECATED_COUNT=0

# Check for old validation patterns
if find imageroot/actions -name "*validate*" -not -name "validate-input.json" | grep -q .; then
    echo -e "${YELLOW}⚠${NC} Found potential deprecated validation files"
    find imageroot/actions -name "*validate*" -not -name "validate-input.json"
    DEPRECATED_COUNT=$((DEPRECATED_COUNT + 1))
fi

# Check for old configure patterns
if find imageroot/actions -name "*configure_new*" | grep -q .; then
    echo -e "${YELLOW}⚠${NC} Found deprecated configure_new files"
    find imageroot/actions -name "*configure_new*"
    DEPRECATED_COUNT=$((DEPRECATED_COUNT + 1))
fi

if [[ $DEPRECATED_COUNT -eq 0 ]]; then
    echo -e "${GREEN}✓${NC} No deprecated patterns found"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo
echo "📋 Validation Summary"
echo "===================="
echo "Passed: $PASSED_CHECKS/$TOTAL_CHECKS checks"

if [[ $PASSED_CHECKS -eq $TOTAL_CHECKS ]]; then
    echo -e "${GREEN}🎉 All validations passed! Module modernization is complete.${NC}"
    exit 0
else
    FAILED=$((TOTAL_CHECKS - PASSED_CHECKS))
    echo -e "${RED}❌ $FAILED validation(s) failed. Please review and fix issues.${NC}"
    exit 1
fi
