#!/bin/bash

# Papervisor Web Server Launcher
# This script launches the Papervisor web server with the correct conda environment
# Usage: ./launch_web_server.sh <project_id> [data_dir] [host] [port]

set -e  # Exit on any error

# Default values
DEFAULT_DATA_DIR="data"
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="5000"
CONDA_ENV="env_papervisor"

# Function to print usage
print_usage() {
    echo "Usage: $0 <project_id> [data_dir] [host] [port]"
    echo ""
    echo "Arguments:"
    echo "  project_id    Literature review project ID (required)"
    echo "  data_dir      Data directory path (default: $DEFAULT_DATA_DIR)"
    echo "  host          Server host (default: $DEFAULT_HOST)"
    echo "  port          Server port (default: $DEFAULT_PORT)"
    echo ""
    echo "Examples:"
    echo "  $0 qplanner_literature_review"
    echo "  $0 my_project data 0.0.0.0 8080"
    echo ""
    echo "Requirements:"
    echo "  - Conda environment '$CONDA_ENV' must exist"
    echo "  - Project must exist in the specified data directory"
}

# Check arguments
if [ $# -lt 1 ]; then
    echo "Error: Project ID is required"
    echo ""
    print_usage
    exit 1
fi

# Parse arguments
PROJECT_ID="$1"
DATA_DIR="${2:-$DEFAULT_DATA_DIR}"
HOST="${3:-$DEFAULT_HOST}"
PORT="${4:-$DEFAULT_PORT}"

# Get the directory where this script is located (works with symlinks)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Papervisor Web Server Launcher"
echo "=================================="
echo "Script directory: $SCRIPT_DIR"
echo "Project ID: $PROJECT_ID"
echo "Data directory: $DATA_DIR"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Conda environment: $CONDA_ENV"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda is not available in PATH"
    echo "Please ensure conda is installed and available in your shell"
    exit 1
fi

# Check if the conda environment exists
if ! conda env list | grep -q "^$CONDA_ENV "; then
    echo "❌ Error: Conda environment '$CONDA_ENV' does not exist"
    echo "Please create the environment first:"
    echo "  conda create -n $CONDA_ENV python=3.9"
    echo "  conda activate $CONDA_ENV"
    echo "  cd $SCRIPT_DIR"
    echo "  pip install -e ."
    exit 1
fi

# Check if the data directory exists (relative to script directory)
DATA_PATH="$SCRIPT_DIR/$DATA_DIR"
if [ ! -d "$DATA_PATH" ]; then
    echo "❌ Error: Data directory '$DATA_PATH' does not exist"
    echo "Please ensure the data directory exists and contains your literature review projects"
    exit 1
fi

# Check if the project exists
PROJECT_PATH="$DATA_PATH/literature_reviews/$PROJECT_ID"
if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ Error: Project directory '$PROJECT_PATH' does not exist"
    echo "Available projects:"
    if [ -d "$DATA_PATH/literature_reviews" ]; then
        ls -1 "$DATA_PATH/literature_reviews" 2>/dev/null || echo "  (no projects found)"
    else
        echo "  (literature_reviews directory not found)"
    fi
    exit 1
fi

# Check if consolidated papers file exists
CONSOLIDATED_CSV="$PROJECT_PATH/pdfs/consolidated_papers.csv"
if [ ! -f "$CONSOLIDATED_CSV" ]; then
    echo "⚠️  Warning: Consolidated papers file not found at '$CONSOLIDATED_CSV'"
    echo "You may need to run the consolidation process first:"
    echo "  conda activate $CONDA_ENV"
    echo "  cd $SCRIPT_DIR"
    echo "  python -m papervisor consolidate $PROJECT_ID"
    echo ""
    echo "Continuing anyway..."
fi

echo "✅ All checks passed"
echo ""

# Change to script directory to ensure relative paths work
cd "$SCRIPT_DIR"

echo "📂 Working directory: $(pwd)"
echo "🐍 Activating conda environment '$CONDA_ENV'..."

# Create a temporary script to run the web server
# This ensures the conda environment is properly activated
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << EOF
#!/bin/bash
set -e
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate $CONDA_ENV
echo "🔧 Python executable: \$(which python)"
echo "📦 Python version: \$(python --version)"

# Check and install PyPDF2 if needed for text extraction
echo "📚 Checking PDF text extraction dependencies..."
python -c "
try:
    import PyPDF2
    print('✅ PyPDF2 is available')
except ImportError:
    print('📦 Installing PyPDF2 for PDF text extraction...')
    import subprocess
    subprocess.check_call(['pip', 'install', 'PyPDF2'])
    print('✅ PyPDF2 installed successfully')
"

echo ""
echo "🌐 Starting Papervisor web server..."
echo "   URL: http://$HOST:$PORT"
echo "   Project: $PROJECT_ID"
echo "   Data directory: $DATA_DIR"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
python -c "
import sys
sys.path.insert(0, 'src')
from papervisor.web_server import PapervisorWebServer

try:
    server = PapervisorWebServer('$PROJECT_ID', '$DATA_DIR')
    server.run(host='$HOST', port=$PORT, debug=False)
except KeyboardInterrupt:
    print('\\n\\n🛑 Server stopped by user')
except Exception as e:
    print(f'\\n❌ Error starting server: {e}')
    sys.exit(1)
"
EOF

# Make the temporary script executable and run it
chmod +x "$TEMP_SCRIPT"

# Trap to clean up the temporary script
trap "rm -f $TEMP_SCRIPT" EXIT

# Run the server
bash "$TEMP_SCRIPT"
