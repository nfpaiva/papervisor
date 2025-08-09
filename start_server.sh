#!/bin/bash
cd /home/nuno_paiva_nos_pt/papervisor
conda activate env_papervisor
python -c "
import sys
sys.path.insert(0, 'src')
from papervisor.web_server import PapervisorWebServer
server = PapervisorWebServer('qplanner_literature_review', 'data')
print('🌐 Starting Papervisor Web Server...')
print('📁 Project: qplanner_literature_review')
print('🔗 URL: http://127.0.0.1:5000')
print('Press Ctrl+C to stop')
server.run(host='0.0.0.0', port=5000, debug=False)
"
