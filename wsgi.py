import os
import sys

# Try to capture all errors during startup, including imports
try:
    from app import create_app
    app = create_app(os.getenv('FLASK_CONFIG') or 'default')

    if __name__ == '__main__':
        # PORT is set by the preview manager to the dynamically assigned preview port
        port = int(os.environ.get('PORT', 3000))
        print(f"Starting Flask server on port {port}...", flush=True)
        # Bind specifically to 127.0.0.1 to match preview manager expectation on Windows
        # Disable reloader to prevent forking issues
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', port)), debug=True, use_reloader=False)

except Exception as e:
    import traceback
    print(f"CRITICAL: Failed to start Flask app: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)


