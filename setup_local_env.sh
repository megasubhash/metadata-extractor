#!/bin/bash

# Setup script for local development on macOS
# Source this file: source setup_local_env.sh

echo "🔧 Setting up local development environment for macOS..."

# Fix macOS fork safety issue
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
echo "✅ Set OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES"

# Set Redis URL for local development
export REDIS_URL="redis://localhost:6379/0"
echo "✅ Set REDIS_URL=$REDIS_URL"

# Activate virtual environment if not already active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    if [[ -f "env/bin/activate" ]]; then
        source env/bin/activate
        echo "✅ Activated virtual environment"
    else
        echo "⚠️  Virtual environment not found at env/bin/activate"
    fi
else
    echo "✅ Virtual environment already active: $VIRTUAL_ENV"
fi

echo ""
echo "🚀 Environment ready! You can now run:"
echo "   rq worker extract"
echo "   python app.py"
echo "   python run_worker_local.py  (alternative worker script)"
echo ""
