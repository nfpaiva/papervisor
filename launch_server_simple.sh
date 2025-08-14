#!/bin/bash

# Simple server launch script (assumes conda environment is already activated)
# Usage: conda activate env_papervisor && ./launch_server_simple.sh

echo "🚀 Launching Papervisor Web Server..."

# Change to project directory
cd /home/nuno_paiva_nos_pt/papervisor

# Check if we're in the right conda environment
if [[ "$CONDA_DEFAULT_ENV" != "env_papervisor" ]]; then
    echo "❌ Please activate the conda environment first:"
    echo "   conda activate env_papervisor"
    echo "   Then run this script again"
    exit 1
fi

echo "📦 Environment: $CONDA_DEFAULT_ENV"
echo "🐍 Python: $(python --version)"

echo "🌐 Starting server..."
echo "� Multi-project mode: Browse all literature review projects"
echo "🔗 Local URL: http://127.0.0.1:5000"
echo "🔗 Network URL: http://0.0.0.0:5000"
echo "⚠️  Press Ctrl+C to stop the server"
echo "=================================================="

python -c "
import sys
sys.path.insert(0, 'src')

try:
    from papervisor.web_server import PapervisorWebServer

    # Launch in multi-project mode (no specific project_id)
    server = PapervisorWebServer(project_id=None, data_dir='data')

    print('🌟 Multi-project mode enabled - browse all literature review projects')
    server.run(host='0.0.0.0', port=5000, debug=False)
except KeyboardInterrupt:
    print()
    print('👋 Server stopped by user')
except Exception as e:
    print(f'❌ Server error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
