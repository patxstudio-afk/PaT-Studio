import http.server, socketserver, os, glob

PORT = 8000
JS_BYPASS = b"""<script>
if(['navigate','back_forward'].includes(performance.getEntriesByType('navigation')[0]?.type))location.reload();
window.addEventListener('languagechange',()=>location.reload());
window.addEventListener('DOMContentLoaded',()=>{
sessionStorage.setItem('_l',document.documentElement.lang||'');
new MutationObserver(()=>{
const l=document.documentElement.lang||'';
if(l!==sessionStorage.getItem('_l')){sessionStorage.setItem('_l',l);location.reload();}
}).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});
});
const _f=window.fetch;window.fetch=(u,o)=>{if(typeof u==='string')u+=(u.includes('?')?'&':'?')+'t='+Date.now();return _f(u,o)};
</script>"""

def find_file_case_insensitive(path):
    """Find file with case-insensitive fallback and .html extension"""
    candidates = [
        path,
        path.lower(),
        f"{path}.html",
        f"{path.lower()}.html"
    ]
    
    seen = set()
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            if os.path.isfile(candidate):
                return candidate
    
    return None

class AntiCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Clear-Site-Data', '"cache"')
        super().end_headers()

    def do_GET(self):
        request_path = self.path.split('?')[0].strip('/')
        
        # Handle root and home - serve index.html
        if request_path in ('', 'home'):
            final_path = 'index.html'
        else:
            # Try to find the requested file
            final_path = find_file_case_insensitive(request_path)
            
            # If file not found, serve 404
            if not final_path or not os.path.isfile(final_path):
                if os.path.isfile('404.html'):
                    try:
                        with open('404.html', 'rb') as f:
                            content = f.read()
                        
                        pos = content.find(b'</head>')
                        if pos != -1:
                            body = content[:pos] + JS_BYPASS + content[pos:]
                        else:
                            body = JS_BYPASS + content
                        
                        self.send_response(404)
                        self.send_header('Content-Type', 'text/html; charset=utf-8')
                        self.send_header('Content-Length', len(body))
                        self.end_headers()
                        self.wfile.write(body)
                        return
                    except Exception as e:
                        self.send_error(404)
                        return
                else:
                    self.send_error(404)
                    return

        # Verify file exists
        if not os.path.isfile(final_path):
            self.send_error(404)
            return

        # Serve HTML files with cache-busting script
        if final_path.endswith('.html'):
            try:
                with open(final_path, 'rb') as f:
                    content = f.read()
                
                pos = content.find(b'</head>')
                if pos != -1:
                    body = content[:pos] + JS_BYPASS + content[pos:]
                else:
                    body = JS_BYPASS + content
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', len(body))
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                self.send_error(500)
                return
        
        # Non-HTML files return 404
        self.send_error(404)

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), AntiCacheHandler) as httpd:
        try:
            print(f"Server running on port {PORT}")
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()
