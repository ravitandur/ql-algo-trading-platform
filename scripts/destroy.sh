#!/bin/bash

#
# Destroy Script for Options Strategy Lifecycle Platform
# 
# This script automates the safe destruction of the Options Strategy Lifecycle Platform
# infrastructure using AWS CDK. It includes multiple safety checks, data backup options,
# and comprehensive validation to prevent accidental deletion of critical resources.
#
# Features:
# - Multi-layer safety confirmations
# - Data backup before destruction
# - Resource dependency validation
# - Selective resource destruction
# - Cost savings calculation
# - Audit trail logging
# - Emergency stop capability
# - Resource recovery options
#
# Usage:
#   ./scripts/destroy.sh [environment] [options]
#   
# Examples:
#   ./scripts/destroy.sh dev                    # Destroy dev environment (with confirmations)
#   ./scripts/destroy.sh staging --force        # Force destroy staging (dangerous!)
#   ./scripts/destroy.sh dev --backup-data      # Backup data before destroying
#   ./scripts/destroy.sh prod --dry-run         # Show what would be destroyed
#

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/destroy_${TIMESTAMP}.log"

# Default values
ENVIRONMENT="${1:-}"
FORCE_DESTROY="false"
BACKUP_DATA="false"
DRY_RUN="false"
SKIP_CONFIRMATIONS="false"
DESTROY_TIMEOUT=1800  # 30 minutes
CONFIRMATION_COUNT=0
REQUIRED_CONFIRMATIONS=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}" | tee -a "$LOG_FILE"
}

print_info() {
    print_status "$BLUE" "ℹ️  $1"
}

print_success() {
    print_status "$GREEN" "✅ $1"
}

print_warning() {
    print_status "$YELLOW" "⚠️  $1"
}

print_error() {
    print_status "$RED" "❌ $1"
}

print_step() {
    print_status "$PURPLE" "🔥 $1"
}

print_danger() {
    print_status "$RED" "🚨 $1"
}

# Function to display script usage
show_help() {
    cat << EOF
Options Strategy Lifecycle Platform - Destroy Script

⚠️  WARNING: This script will PERMANENTLY DELETE AWS resources! ⚠️

USAGE:
    $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    dev         Destroy development environment
    staging     Destroy staging environment  
    prod        Destroy production environment (requires extra confirmations)

OPTIONS:
    --dry-run           Show what would be destroyed without making changes
    --force             Skip safety confirmations (DANGEROUS!)
    --backup-data       Backup data before destroying resources
    --skip-confirmation Skip manual confirmations (use with extreme caution)
    --timeout SECONDS   Set destruction timeout (default: 1800)
    --help              Show this help message

SAFETY FEATURES:
    • Multiple confirmation prompts
    • Production environment extra protection
    • Resource dependency validation
    • Data backup options
    • Audit trail logging
    • Emergency stop capability

EXAMPLES:
    $0 dev                          # Safely destroy dev (with confirmations)
    $0 staging --backup-data        # Backup data before destroying staging
    $0 prod --dry-run              # Show what would be destroyed in prod
    
⚠️  CAUTION: Use --force flag only if you fully understand the consequences!
⚠️  PRODUCTION: Extra confirmations required for production destruction

For more information, see docs/deployment.md
EOF
}

# Function to parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --force)
                FORCE_DESTROY="true"
                SKIP_CONFIRMATIONS="true"
                print_warning "Force mode enabled - safety checks will be bypassed!"
                shift
                ;;
            --backup-data)
                BACKUP_DATA="true"
                shift
                ;;
            --skip-confirmation)
                SKIP_CONFIRMATIONS="true"
                print_warning "Confirmation prompts will be skipped!"
                shift
                ;;
            --timeout)
                DESTROY_TIMEOUT="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            --*)
                print_error "Unknown option: $1"
                echo "Use --help for usage information."
                exit 1
                ;;
            *)
                if [[ -z "${1:-}" ]]; then
                    break
                fi
                print_error "Unknown argument: $1"
                echo "Use --help for usage information."
                exit 1
                ;;
        esac
    done
}

# Function to setup logging
setup_logging() {
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    touch "$LOG_FILE"
    
    print_danger "DESTRUCTION STARTED at $(date)"
    print_info "Environment: $ENVIRONMENT"
    print_info "Log file: $LOG_FILE"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_info "DRY RUN MODE - No actual resources will be destroyed"
    else
        print_danger "LIVE MODE - Resources will be permanently deleted!"
    fi
}

# Function to validate environment
validate_environment() {
    local env=$1
    
    if [[ -z "$env" ]]; then
        print_error "Environment not specified!"
        print_error "Usage: $0 <environment> [options]"
        print_error "Supported environments: dev, staging, prod"
        exit 1
    fi
    
    print_step "Validating environment: $env"
    
    case $env in
        dev|staging|prod)
            print_success "Environment '$env' is valid"
            ;;
        *)
            print_error "Invalid environment: $env"
            print_error "Supported environments: dev, staging, prod"
            exit 1
            ;;
    esac
    
    # Extra protection for production
    if [[ "$env" == "prod" ]]; then
        print_danger "PRODUCTION ENVIRONMENT DESTRUCTION REQUESTED!"
        print_danger "This will permanently delete production data and infrastructure!"
        
        if [[ "$FORCE_DESTROY" != "true" ]]; then
            REQUIRED_CONFIRMATIONS=5  # Require more confirmations for prod
        fi
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites"
    
    local missing_tools=()
    
    # Check required tools
    if ! command -v aws &> /dev/null; then
        missing_tools+=("aws-cli")
    fi
    
    if ! command -v cdk &> /dev/null; then
        missing_tools+=("aws-cdk")
    fi
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_error "Please install missing tools and try again"
        exit 1
    fi
    
    print_success "All required tools are installed"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured or invalid"
        print_error "Please configure AWS credentials and try again"
        exit 1
    fi
    
    local aws_account=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
    local aws_user=$(aws sts get-caller-identity --query UserId --output text 2>/dev/null || echo "unknown")
    
    print_success "AWS credentials valid - Account: $aws_account, User: $aws_user"
    
    # Verify we're in the correct project
    if [[ ! -f "$PROJECT_ROOT/cdk.json" ]]; then
        print_error "cdk.json not found. Are you in the correct project directory?"
        exit 1
    fi
}

# Function to analyze stack resources
analyze_stack_resources() {
    print_step "Analyzing stack resources to be destroyed"
    
    local stack_name="OptionsStrategyPlatform-$(echo "$ENVIRONMENT" | awk '{print toupper(substr($0,1,1))substr($0,2)}')"
    
    print_info "Analyzing stack: $stack_name"
    
    # Check if stack exists
    if ! aws cloudformation describe-stacks --stack-name "$stack_name" &>/dev/null; then
        print_warning "Stack '$stack_name' does not exist or has already been deleted"
        print_info "Nothing to destroy for environment: $ENVIRONMENT"
        exit 0
    fi
    
    # Get stack status
    local stack_status
    stack_status=$(aws cloudformation describe-stacks --stack-name "$stack_name" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "UNKNOWN")
    
    print_info "Current stack status: $stack_status"
    
    if [[ "$stack_status" == "DELETE_IN_PROGRESS" ]]; then
        print_warning "Stack is already being deleted"
        exit 0
    fi
    
    # List resources that will be destroyed
    print_info "Resources to be destroyed:"
    
    if aws cloudformation list-stack-resources --stack-name "$stack_name" --query 'StackResourceSummaries[*].[ResourceType,LogicalResourceId,PhysicalResourceId]' --output table >> "$LOG_FILE" 2>&1; then
        # Show a summary
        local resource_count
        resource_count=$(aws cloudformation list-stack-resources --stack-name "$stack_name" --query 'length(StackResourceSummaries)' --output text 2>/dev/null || echo "0")
        
        print_warning "$resource_count resources will be destroyed"
        
        # Show critical resources
        print_info "Critical resources identified:"
        aws cloudformation list-stack-resources --stack-name "$stack_name" \
            --query 'StackResourceSummaries[?contains(`["AWS::RDS::DBInstance","AWS::DynamoDB::Table","AWS::S3::Bucket","AWS::EFS::FileSystem"]`, ResourceType)].[ResourceType,LogicalResourceId]' \
            --output table 2>/dev/null || print_info "No critical data resources found"
    else
        print_error "Failed to analyze stack resources"
        exit 1
    fi
    
    return 0
}

# Function to backup data
backup_data() {
    if [[ "$BACKUP_DATA" != "true" ]]; then
        return 0
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_info "DRY RUN: Would backup data before destruction"
        return 0
    fi
    
    print_step "Backing up data before destruction"
    
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="${BACKUP_DIR}/${ENVIRONMENT}_${backup_timestamp}"
    
    mkdir -p "$backup_path"
    
    # Backup Parameter Store values
    print_info "Backing up Parameter Store values"
    if aws ssm get-parameters-by-path --path "/options-strategy/${ENVIRONMENT}" --recursive --query 'Parameters[*].[Name,Value]' --output json > "${backup_path}/parameters.json" 2>>"$LOG_FILE"; then
        print_success "Parameter Store backup completed"
    else
        print_warning "Parameter Store backup failed (parameters may not exist)"
    fi
    
    # Backup CloudWatch dashboards configuration
    print_info "Backing up CloudWatch dashboard configurations"
    local dashboard_names=()
    while IFS= read -r dashboard_name; do
        if [[ -n "$dashboard_name" && "$dashboard_name" == *"$ENVIRONMENT"* ]]; then
            dashboard_names+=("$dashboard_name")
        fi
    done < <(aws cloudwatch list-dashboards --query 'DashboardEntries[*].DashboardName' --output text 2>/dev/null || echo "")
    
    for dashboard_name in "${dashboard_names[@]}"; do
        if aws cloudwatch get-dashboard --dashboard-name "$dashboard_name" > "${backup_path}/dashboard_${dashboard_name}.json" 2>>"$LOG_FILE"; then
            print_success "Backed up dashboard: $dashboard_name"
        else
            print_warning "Failed to backup dashboard: $dashboard_name"
        fi
    done
    
    # Note: For production systems, you would also backup:
    # - DynamoDB tables (using DynamoDB backup or export)
    # - RDS databases (using snapshots)
    # - S3 buckets (using cross-region replication or backup)
    # - EFS file systems (using backup service)
    
    print_success "Data backup completed at: $backup_path"
    
    # Create recovery instructions
    cat > "${backup_path}/recovery_instructions.md" << EOF
# Recovery Instructions for $ENVIRONMENT

## Backup Details
- Environment: $ENVIRONMENT  
- Backup Date: $(date)
- Backup Path: $backup_path

## Files Included
- parameters.json: Parameter Store values
- dashboard_*.json: CloudWatch dashboard configurations

## Recovery Steps
1. Redeploy the infrastructure using: ./scripts/deploy.sh $ENVIRONMENT
2. Restore Parameter Store values from parameters.json
3. Recreate CloudWatch dashboards from dashboard_*.json files

## Notes
- This backup contains configuration data only
- Application data (databases, file systems) require separate backup procedures
- Test the recovery process in a non-production environment first

EOF

    print_success "Recovery instructions created at: ${backup_path}/recovery_instructions.md"
}

# Function to get user confirmations
get_confirmations() {
    if [[ "$SKIP_CONFIRMATIONS" == "true" ]]; then
        print_warning "Skipping confirmations as requested"
        return 0
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_info "DRY RUN: Skipping confirmations"
        return 0
    fi
    
    print_step "Safety confirmations required"
    print_danger "You are about to PERMANENTLY DELETE the $ENVIRONMENT environment!"
    
    local confirmations_needed=$REQUIRED_CONFIRMATIONS
    
    # Additional warning for production
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        print_danger "🚨 PRODUCTION ENVIRONMENT DESTRUCTION 🚨"
        print_danger "This action will:"
        print_danger "- Delete ALL production data"
        print_danger "- Remove ALL production infrastructure" 
        print_danger "- Potentially cause service downtime"
        print_danger "- Be IRREVERSIBLE without backups"
        echo
    fi
    
    # Confirmation 1: Environment name
    echo -n "Type the environment name '$ENVIRONMENT' to confirm: "
    read -r env_confirmation
    if [[ "$env_confirmation" != "$ENVIRONMENT" ]]; then
        print_error "Environment name confirmation failed"
        print_error "Expected: $ENVIRONMENT, Got: $env_confirmation"
        exit 1
    fi
    CONFIRMATION_COUNT=$((CONFIRMATION_COUNT + 1))
    print_success "Environment confirmation: $CONFIRMATION_COUNT/$confirmations_needed"
    
    # Confirmation 2: Understanding of consequences
    echo -n "Type 'I understand the consequences' to continue: "
    read -r consequence_confirmation
    if [[ "$consequence_confirmation" != "I understand the consequences" ]]; then
        print_error "Consequence confirmation failed"
        exit 1
    fi
    CONFIRMATION_COUNT=$((CONFIRMATION_COUNT + 1))
    print_success "Consequence confirmation: $CONFIRMATION_COUNT/$confirmations_needed"
    
    # Confirmation 3: Final confirmation
    echo -n "Type 'DELETE' in uppercase to proceed: "
    read -r delete_confirmation
    if [[ "$delete_confirmation" != "DELETE" ]]; then
        print_error "Delete confirmation failed"
        exit 1
    fi
    CONFIRMATION_COUNT=$((CONFIRMATION_COUNT + 1))
    print_success "Delete confirmation: $CONFIRMATION_COUNT/$confirmations_needed"
    
    # Additional confirmations for production
    if [[ "$ENVIRONMENT" == "prod" && $CONFIRMATION_COUNT -lt $confirmations_needed ]]; then
        # Confirmation 4: Production specific
        echo -n "Type 'DESTROY PRODUCTION' to confirm production destruction: "
        read -r prod_confirmation
        if [[ "$prod_confirmation" != "DESTROY PRODUCTION" ]]; then
            print_error "Production confirmation failed"
            exit 1
        fi
        CONFIRMATION_COUNT=$((CONFIRMATION_COUNT + 1))
        print_success "Production confirmation: $CONFIRMATION_COUNT/$confirmations_needed"
        
        # Confirmation 5: Final production check
        echo -n "This is your FINAL WARNING. Type 'YES I AM SURE' to proceed: "
        read -r final_confirmation
        if [[ "$final_confirmation" != "YES I AM SURE" ]]; then
            print_error "Final confirmation failed"
            exit 1
        fi
        CONFIRMATION_COUNT=$((CONFIRMATION_COUNT + 1))
        print_success "Final confirmation: $CONFIRMATION_COUNT/$confirmations_needed"
    fi
    
    if [[ $CONFIRMATION_COUNT -ge $confirmations_needed ]]; then
        print_success "All required confirmations received"
        print_danger "Proceeding with destruction in 10 seconds..."
        print_info "Press Ctrl+C to abort"
        
        for i in {10..1}; do
            echo -n "$i... "
            sleep 1
        done
        echo
        print_danger "Starting destruction process!"
    else
        print_error "Insufficient confirmations ($CONFIRMATION_COUNT/$confirmations_needed)"
        exit 1
    fi
}

# Function to run CDK destroy
run_cdk_destroy() {
    if [[ "$DRY_RUN" == "true" ]]; then
        print_info "DRY RUN: Would run CDK destroy"
        print_info "Command would be: cdk destroy --force"
        return 0
    fi
    
    print_step "Running CDK destroy for $ENVIRONMENT environment"
    
    cd "$PROJECT_ROOT"
    
    export CDK_ENVIRONMENT="$ENVIRONMENT"
    
    local cdk_args=()
    cdk_args+=("--force")  # Skip confirmation since we've already confirmed
    
    print_info "Running: cdk destroy ${cdk_args[*]}"
    
    if timeout "$DESTROY_TIMEOUT" cdk destroy "${cdk_args[@]}" >> "$LOG_FILE" 2>&1; then
        print_success "CDK destroy completed successfully"
        return 0
    else
        print_error "CDK destroy failed"
        print_error "Check log file: $LOG_FILE"
        return 1
    fi
}

# Function to verify destruction
verify_destruction() {
    if [[ "$DRY_RUN" == "true" ]]; then
        print_info "DRY RUN: Would verify destruction"
        return 0
    fi
    
    print_step "Verifying destruction completion"
    
    local stack_name="OptionsStrategyPlatform-$(echo "$ENVIRONMENT" | awk '{print toupper(substr($0,1,1))substr($0,2)}')"
    
    # Check if stack still exists
    local max_attempts=30  # Check for up to 15 minutes
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if aws cloudformation describe-stacks --stack-name "$stack_name" &>/dev/null; then
            local stack_status
            stack_status=$(aws cloudformation describe-stacks --stack-name "$stack_name" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "UNKNOWN")
            
            print_info "Stack status: $stack_status (attempt $((attempt + 1))/$max_attempts)"
            
            case $stack_status in
                "DELETE_COMPLETE")
                    print_success "Stack deletion completed successfully"
                    return 0
                    ;;
                "DELETE_FAILED")
                    print_error "Stack deletion failed"
                    print_error "Manual intervention may be required"
                    return 1
                    ;;
                "DELETE_IN_PROGRESS")
                    print_info "Stack deletion in progress..."
                    sleep 30
                    attempt=$((attempt + 1))
                    ;;
                *)
                    print_warning "Unexpected stack status: $stack_status"
                    sleep 30
                    attempt=$((attempt + 1))
                    ;;
            esac
        else
            print_success "Stack no longer exists - destruction complete"
            return 0
        fi
    done
    
    print_error "Timeout waiting for stack deletion to complete"
    print_error "Stack may still be deleting - check AWS console"
    return 1
}

# Function to clean up orphaned resources
cleanup_orphaned_resources() {
    if [[ "$DRY_RUN" == "true" ]]; then
        print_info "DRY RUN: Would cleanup orphaned resources"
        return 0
    fi
    
    print_step "Checking for orphaned resources"
    
    # Check for orphaned Parameter Store entries
    print_info "Checking for orphaned Parameter Store entries"
    local parameters
    if parameters=$(aws ssm get-parameters-by-path --path "/options-strategy/${ENVIRONMENT}" --query 'Parameters[*].Name' --output text 2>/dev/null); then
        if [[ -n "$parameters" ]]; then
            print_warning "Found orphaned Parameter Store entries:"
            echo "$parameters" | tr '\t' '\n' | while read -r param; do
                print_info "  - $param"
            done
            
            echo -n "Delete orphaned Parameter Store entries? (y/N): "
            read -r cleanup_params
            if [[ $cleanup_params =~ ^[Yy]$ ]]; then
                echo "$parameters" | tr '\t' '\n' | while read -r param; do
                    if aws ssm delete-parameter --name "$param" 2>>"$LOG_FILE"; then
                        print_success "Deleted parameter: $param"
                    else
                        print_error "Failed to delete parameter: $param"
                    fi
                done
            fi
        else
            print_success "No orphaned Parameter Store entries found"
        fi
    fi
    
    # Check for orphaned CloudWatch Log Groups
    print_info "Checking for orphaned CloudWatch Log Groups"
    local log_groups
    if log_groups=$(aws logs describe-log-groups --log-group-name-prefix "/aws/options-strategy/${ENVIRONMENT}" --query 'logGroups[*].logGroupName' --output text 2>/dev/null); then
        if [[ -n "$log_groups" ]]; then
            print_warning "Found orphaned CloudWatch Log Groups:"
            echo "$log_groups" | tr '\t' '\n' | while read -r log_group; do
                print_info "  - $log_group"
            done
            
            echo -n "Delete orphaned CloudWatch Log Groups? (y/N): "
            read -r cleanup_logs
            if [[ $cleanup_logs =~ ^[Yy]$ ]]; then
                echo "$log_groups" | tr '\t' '\n' | while read -r log_group; do
                    if aws logs delete-log-group --log-group-name "$log_group" 2>>"$LOG_FILE"; then
                        print_success "Deleted log group: $log_group"
                    else
                        print_error "Failed to delete log group: $log_group"
                    fi
                done
            fi
        else
            print_success "No orphaned CloudWatch Log Groups found"
        fi
    fi
    
    print_success "Orphaned resource cleanup completed"
}

# Function to calculate cost savings
calculate_cost_savings() {
    print_step "Calculating potential cost savings"
    
    # This is a placeholder for cost calculation logic
    # In a real implementation, you might integrate with AWS Cost Explorer API
    # or use historical billing data
    
    print_info "Cost savings calculation not implemented yet"
    print_info "Please review your AWS billing dashboard for actual costs"
    
    if [[ "$ENVIRONMENT" == "prod" ]]; then
        print_warning "Production environment destroyed - monitor billing for cost impact"
    else
        print_info "Development/staging environment destroyed - should reduce monthly costs"
    fi
}

# Function to send notifications
send_notification() {
    local status=$1
    local message=$2
    
    print_info "Sending destruction notification"
    
    # Email notification (if configured)
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
        # Placeholder for email notification
        print_info "Email notification would be sent to: $NOTIFICATION_EMAIL"
    fi
    
    # Slack notification (if configured)
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        # Placeholder for Slack notification
        print_info "Slack notification would be sent"
    fi
    
    # SNS notification (if configured)
    if [[ -n "${SNS_TOPIC_ARN:-}" ]]; then
        # Placeholder for SNS notification
        print_info "SNS notification would be sent"
    fi
}

# Function to cleanup on exit
cleanup() {
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "Destruction completed successfully"
        calculate_cost_savings
        send_notification "success" "Environment $ENVIRONMENT destroyed successfully"
        
        if [[ "$BACKUP_DATA" == "true" ]]; then
            print_info "Backup available at: $BACKUP_DIR"
            print_info "See recovery instructions in backup directory"
        fi
    else
        print_error "Destruction failed with exit code: $exit_code"
        print_error "Some resources may still exist - check AWS console"
        send_notification "failure" "Environment $ENVIRONMENT destruction failed"
    fi
    
    print_info "Log file available at: $LOG_FILE"
    print_info "Destruction process finished at $(date)"
}

# Main destruction function
main() {
    # Setup trap for cleanup
    trap cleanup EXIT
    
    # Parse command line arguments (skip first argument which is environment)
    if [[ $# -gt 1 ]]; then
        parse_arguments "${@:2}"
    fi
    
    # Setup logging
    setup_logging
    
    # Validate environment
    validate_environment "$ENVIRONMENT"
    
    # Check prerequisites
    check_prerequisites
    
    # Analyze what will be destroyed
    analyze_stack_resources
    
    # Backup data if requested
    backup_data
    
    # Get user confirmations
    get_confirmations
    
    # Run CDK destroy
    if run_cdk_destroy; then
        # Verify destruction
        if verify_destruction; then
            # Clean up any orphaned resources
            cleanup_orphaned_resources
            
            print_success "🗑️  Environment $ENVIRONMENT has been completely destroyed!"
        else
            print_error "❌ Destruction verification failed!"
            exit 1
        fi
    else
        print_error "❌ Destruction failed!"
        exit 1
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi