#!/bin/bash

# Setup script for automated query scheduler cron jobs
# This script will configure cron to run the scheduler twice daily

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH="$PROJECT_ROOT/venv/bin/python"
SCHEDULER_SCRIPT="$SCRIPT_DIR/automated_scheduler.py"

echo "🚀 Setting up automated query scheduler cron jobs..."
echo "Project root: $PROJECT_ROOT"
echo "Python path: $PYTHON_PATH"
echo "Scheduler script: $SCHEDULER_SCRIPT"

# Check if virtual environment exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Virtual environment not found at $PYTHON_PATH"
    echo "Please run 'python -m venv venv' and 'source venv/bin/activate' first"
    exit 1
fi

# Check if scheduler script exists
if [ ! -f "$SCHEDULER_SCRIPT" ]; then
    echo "❌ Scheduler script not found at $SCHEDULER_SCRIPT"
    exit 1
fi

# Make the script executable
chmod +x "$SCHEDULER_SCRIPT"

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Create the cron job entries
# Run every 15 minutes to check if it's time to execute queries
CRON_JOB="*/15 * * * * cd $PROJECT_ROOT && $PYTHON_PATH $SCHEDULER_SCRIPT >> $PROJECT_ROOT/logs/cron.log 2>&1"

echo ""
echo "📅 Cron job configuration:"
echo "$CRON_JOB"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCHEDULER_SCRIPT"; then
    echo "⚠️  Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "$SCHEDULER_SCRIPT" | crontab -
fi

# Add the new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job added successfully!"
    echo ""
    echo "📋 Current cron jobs:"
    crontab -l
    echo ""
    echo "🔍 To monitor the scheduler:"
    echo "  - Check logs: tail -f $PROJECT_ROOT/logs/cron.log"
    echo "  - Check scheduler logs: tail -f $PROJECT_ROOT/logs/scheduler_*.log"
    echo "  - View cron jobs: crontab -l"
    echo "  - Remove cron jobs: crontab -r"
    echo ""
    echo "⏰ The scheduler will run every 15 minutes and check if it's time to execute queries"
    echo "   based on your schedule (every 3 days at 9:00 AM with 15-minute window)"
    echo "   Post-processing will automatically run after queries complete"
else
    echo "❌ Failed to add cron job"
    exit 1
fi
