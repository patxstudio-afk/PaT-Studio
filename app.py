import http.server
import socketserver
import os

PORT = 8000

class GitHubSimHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith('/'):
            self.path += 'index.html'

        local_path = self.path.lstrip('/').split('?')[0]

        if not os.path.exists(local_path):
            if os.path.exists('404.html'):
                self.path = '/404.html'
            else:
                self.send_error(404, "File not found")
                return

        return super().do_GET()

Handler = GitHubSimHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server start : http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()