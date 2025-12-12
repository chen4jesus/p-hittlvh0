
import http.server
import socketserver
import json
import subprocess
import os
import sys

import shutil
import sqlite3
import datetime

PORT = 8000
DB_FILE = os.getenv('DB_FILE', 'contacts.db')

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

class AIServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/contact':
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
                
        elif self.path == '/api/ask-ai':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                prompt = data.get('prompt', '')
                context = data.get('context', '')

                # Check if Claude CLI exists
                if not shutil.which('claude'):
                    self.send_response(200) # Still 200 OK, but with error payload
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "CLAUDE_NOT_FOUND"}).encode('utf-8'))
                    return
                
                # Construct the full prompt for the agent
                full_message = f"Task: {prompt}\n\nContext HTML request:\n{context}\n\nPlease provide the corrected/updated HTML code based on the task."
                
                print(f"[AI Agent] Received Prompt: {prompt}")
                
                # Invoke Claude CLI
                process = subprocess.Popen(
                    ['claude'], 
                    stdin=subprocess.PIPE, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=True 
                )
                
                stdout, stderr = process.communicate(input=full_message)
                
                if process.returncode != 0:
                    response = {"success": False, "error": stderr or "Unknown error"}
                else:
                    response = {"success": True, "output": stdout}

                # Send Response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
        else:
            self.send_error(404, "File not found")

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == "__main__":
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)
    
    init_db()
    
    with socketserver.TCPServer(("", PORT), AIServerHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print("AI Agent Backend Ready. Waiting for requests...")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
