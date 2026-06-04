"""
Production entry point — uses Waitress WSGI server.
Run this instead of app.py on Windows production:

    python serve.py

Waitress is production-grade, pure Python, works on Windows without any
additional C compiler or build tools.
"""
import os
from waitress import serve
from app import create_app

app = create_app()

HOST = os.environ.get('APP_HOST', '127.0.0.1')   # Only listen on localhost — IIS/Nginx proxies to here
PORT = int(os.environ.get('APP_PORT', '5000'))
THREADS = int(os.environ.get('APP_THREADS', '4'))

if __name__ == '__main__':
    print(f'[INFO] ADBN Instant Card System starting...')
    print(f'[INFO] Listening on {HOST}:{PORT} with {THREADS} threads')
    print(f'[INFO] Access via your configured domain (e.g. https://adbn-cards.adbn.gov.np)')
    print(f'[INFO] Press CTRL+C to stop.')
    serve(app, host=HOST, port=PORT, threads=THREADS)
