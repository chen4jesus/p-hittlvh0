
import http.server
import http.cookies
import socketserver
import json
import os
import secrets
import sqlite3
import time
import aissistant
import urllib.parse
import shutil
import datetime

PORT = int(os.getenv('PORT', 8000))
DB_FILE = os.getenv('DB_FILE', 'churchdata.db')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
UPLOAD_DIR = os.path.join(os.getcwd(), 'upload')
BACKUP_DIR = os.path.join(os.getcwd(), 'backups')

# Simple in-memory session store: token -> timestamp
SESSIONS = {}
SESSION_TIMEOUT = 3600  # 1 hour

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

class ServerHandler(http.server.SimpleHTTPRequestHandler):
    def is_authenticated(self):
        cookie_header = self.headers.get('Cookie')
        if not cookie_header:
            return False
        cookies = http.cookies.SimpleCookie(cookie_header)
        if 'session_token' not in cookies:
            return False
        token = cookies['session_token'].value
        if token in SESSIONS:
            # Check expiry
            if time.time() - SESSIONS[token] < SESSION_TIMEOUT:
                SESSIONS[token] = time.time()  # Refresh session
                return True
            else:
                del SESSIONS[token]
        return False

    def do_GET(self):
        # API Handling
        if self.path.startswith('/api/'):
            if self.path == '/api/admin/verify':
                self.send_response(200 if self.is_authenticated() else 401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"authenticated": self.is_authenticated()}).encode('utf-8'))
                return
            
            # Protected Admin APIs
            if self.path.startswith('/api/admin/'):
                if not self.is_authenticated():
                    self.send_error(401, "Unauthorized")
                    return

                if self.path.startswith('/api/admin/messages'):
                    try:
                        # Parse query params manually to avoid extra dependencies if possible, 
                        # or just use simple string manipulation for page/limit
                        # url: /api/admin/messages?page=1&limit=10
                        
                        query_string = self.path.split('?')[1] if '?' in self.path else ''
                        params = {}
                        if query_string:
                            for pair in query_string.split('&'):
                                if '=' in pair:
                                    k, v = pair.split('=')
                                    params[k] = v
                        
                        page = int(params.get('page', 1))
                        limit = int(params.get('limit', 10))
                        offset = (page - 1) * limit

                        conn = sqlite3.connect(DB_FILE)
                        conn.row_factory = sqlite3.Row
                        c = conn.cursor()
                        
                        # Get Total Count
                        c.execute("SELECT COUNT(*) FROM messages")
                        total = c.fetchone()[0]

                        # Get Paginated Messages
                        c.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT ? OFFSET ?", (limit, offset))
                        rows = c.fetchall()
                        messages = [dict(row) for row in rows]
                        conn.close()
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "success": True, 
                            "messages": messages,
                            "total": total,
                            "page": page,
                            "limit": limit
                        }).encode('utf-8'))
                    except Exception as e:
                        self.send_error(500, str(e))
                    return

                if self.path == '/api/admin/files':
                    try:
                        files = []
                        if os.path.exists(UPLOAD_DIR):
                            for f in os.listdir(UPLOAD_DIR):
                                full_path = os.path.join(UPLOAD_DIR, f)
                                if os.path.isfile(full_path):
                                    stats = os.stat(full_path)
                                    files.append({
                                        "name": f,
                                        "size": stats.st_size,
                                        "modified": stats.st_mtime
                                    })
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": True, "files": files}).encode('utf-8'))
                    except Exception as e:
                        self.send_error(500, str(e))
                    return

                # AI History APIs
                if self.path.startswith('/api/ai/history'):
                    try:
                         # Parse query params
                        query_string = self.path.split('?')[1] if '?' in self.path else ''
                        params = {}
                        if query_string:
                            for pair in query_string.split('&'):
                                if '=' in pair:
                                    k, v = pair.split('=')
                                    params[k] = v
                        
                        page = int(params.get('page', 1))
                        limit = int(params.get('limit', 20))
                        offset = (page - 1) * limit

                        result = aissistant.get_history(DB_FILE, limit, offset)
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": True, **result}).encode('utf-8'))
                    except Exception as e:
                        self.send_error(500, str(e))
                    return
            
            # Fallthrough for unknown API
            self.send_error(404, "API endpoint not found")
            return

        # Secure Admin Frontend Access
        if self.path.startswith('/admin'):
             # Allow login page
            if self.path == '/admin/login.html' or self.path == '/admin/login':
                 super().do_GET()
                 return
            
            # Protect other admin pages
            if not self.is_authenticated():
                # Redirect to login
                self.send_response(302)
                self.send_header('Location', '/admin/login.html')
                self.end_headers()
                return
        
        # Default Static File Serving
        if self.path.startswith('/api/'):
             # Handle Preflight
            if self.command == 'OPTIONS':
                self.send_response(200)
                self.end_headers()
                return

        # Default Static File Serving
        super().do_GET()

    def do_PUT(self):
        if not self.is_authenticated():
            self.send_error(401, "Unauthorized")
            return

        if self.path.startswith('/api/admin/messages/'):
             # ... (Existing PUT logic) ...
             pass

        elif self.path.startswith('/api/ai/history/'):
            # Allow updating commit hash for a history entry
            if not self.is_authenticated():
                self.send_error(401, "Unauthorized")
                return

            hist_id = self.path.split('/')[-1]
            content_length = int(self.headers['Content-Length'])
            put_data = self.rfile.read(content_length)

            try:
                data = json.loads(put_data)
                commit_hash = data.get('commit_hash')
                
                if aissistant.update_history_commit(DB_FILE, hist_id, commit_hash):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                else:
                    self.send_error(500, "Failed to update")
            except Exception as e:
                self.send_error(500, str(e))
        else:
             self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        # Robust path matching
        path = self.path.split('?')[0].rstrip('/')
        
        print(f"[DEBUG] POST Request to: {self.path} -> Normalized: {path}")

        if path == '/api/contact':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                name = data.get('name', '')
                email = data.get('email', '')
                phone = data.get('phone', '')
                message = data.get('message', '')

                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO messages (name, email, phone, message) VALUES (?, ?, ?, ?)",
                          (name, email, phone, message))
                conn.commit()
                conn.close()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Message received"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
                
        elif path == '/api/ask-ai':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                
                # Delegate to AI Assistant Module
                response = aissistant.handle_ai_request(data, DB_FILE)
                
                # Send Response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                print(f"[ERROR] AI Processing Exception: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
        
        elif path == '/api/admin/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                password = data.get('password', '')
                
                if password == ADMIN_PASSWORD:
                    token = secrets.token_hex(16)
                    SESSIONS[token] = time.time()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Set-Cookie', f'session_token={token}; Path=/; HttpOnly')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                else:
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Invalid password"}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))

        elif path == '/api/admin/save-page':
            # Check Authentication
            if not self.is_authenticated():
                self.send_error(401, "Unauthorized")
                return

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                page_name = data.get('page')
                content = data.get('content')
                
                if not page_name or not content:
                    self.send_error(400, "Missing page or content")
                    return

                # Security: Enforce basename and extension
                clean_name = os.path.basename(page_name)
                if not clean_name.endswith('.html'):
                     self.send_error(403, "Only HTML files can be saved")
                     return
                
                # Prevent editing system files if any (optional, but good practice)
                if clean_name.startswith('admin') or clean_name == 'login.html':
                     # Just a basic check, though 'admin' is a folder so basename handles it differently.
                     # But let's be safe about overwriting critical things if they were in root.
                     pass 

                 
                file_path = os.path.join(web_dir, clean_name)
                
                # BACKUP: Create timestamped backup if file exists
                if os.path.exists(file_path):
                    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    backup_name = f"{clean_name}.{timestamp}.bak"
                    backup_path = os.path.join(BACKUP_DIR, backup_name)
                    try:
                        shutil.copy2(file_path, backup_path)
                        print(f"[BACKUP] Created backup: {backup_name}")
                    except Exception as e:
                        print(f"[WARNING] Backup failed: {e}")

                # Write changes
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"[ADMIN] Updated file: {clean_name}")

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))

            except Exception as e:
                print(f"[ERROR] Save Page Exception: {e}")
                self.send_error(500, str(e))

        elif path == '/api/admin/upload':
            # Check Authentication
            if not self.is_authenticated():
                self.send_error(401, "Unauthorized")
                return

            try:
                content_type = self.headers['Content-Type']
                if not content_type.startswith('multipart/form-data'):
                    self.send_error(400, "Content-Type must be multipart/form-data")
                    return

                boundary = content_type.split('boundary=')[1].encode()
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)

                # Split by boundary
                parts = body.split(b'--' + boundary)
                
                saved_filename = None
                
                for part in parts:
                    if b'filename="' in part:
                        # Extract headers and content
                        headers_raw, content = part.split(b'\r\n\r\n', 1)
                        content = content.rstrip(b'\r\n--') # Remove trailing boundary markers
                        
                        # Extract filename
                        headers_str = headers_raw.decode()
                        for line in headers_str.split('\r\n'):
                            if 'Content-Disposition' in line:
                                import re
                                match = re.search(r'filename="(.+?)"', line)
                                if match:
                                    original_filename = match.group(1)
                                    # Sanitize filename
                                    safe_name = os.path.basename(original_filename).replace(' ', '_')
                                    # Ensure unique or timestamped? Let's just keep original but safe
                                    saved_filename = safe_name
                                    
                                    file_path = os.path.join(UPLOAD_DIR, saved_filename)
                                    with open(file_path, 'wb') as f:
                                        f.write(content)
                                    break
                
                if saved_filename:
                    print(f"[ADMIN] Uploaded file: {saved_filename}")
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    # Return path relative to web root
                    self.wfile.write(json.dumps({"success": True, "url": f"upload/{saved_filename}"}).encode('utf-8'))
                else:
                    self.send_error(400, "No file found in request")

            except Exception as e:
                print(f"[ERROR] Upload Exception: {e}")
                self.send_error(500, str(e))

        else:
            print(f"[WARNING] 404 For POST Path: {self.path} (Normalized: {path})")
            self.send_error(404, "File not found")

    def do_DELETE(self):
        if not self.is_authenticated():
            self.send_error(401, "Unauthorized")
            return

        if self.path.startswith('/api/admin/messages/'):
            msg_id = self.path.split('/')[-1]
            try:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            except Exception as e:
                self.send_error(500, str(e))

        elif self.path.startswith('/api/admin/files/'):
            filename = self.path.split('/')[-1]
            # Decode URL-encoded filename (e.g. %20 -> space, %E7... -> Chinese chars)
            filename = urllib.parse.unquote(filename)
            
            # Security: Prevent directory traversal
            clean_name = os.path.basename(filename)
            file_path = os.path.join(UPLOAD_DIR, clean_name)
            
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                else:
                    self.send_error(404, "File not found")
            except Exception as e:
                self.send_error(500, str(e))
            return

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)
    
    init_db()
    aissistant.init_db(DB_FILE)
    
    print(f"Admin Password: {ADMIN_PASSWORD}") # Print for user awareness
    
    # Use ThreadingHTTPServer for concurrent request handling
    with ThreadingHTTPServer(("", PORT), ServerHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print("AI Agent Backend Ready (Multi-threaded). Waiting for requests...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
