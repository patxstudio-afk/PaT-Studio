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
    if os.path.exists(path):
        return path
    
    path_lower = path.lower()
    if path_lower != path and os.path.exists(path_lower):
        return path_lower
    
    if not path_lower.endswith('.html'):
        path_with_html = path + '.html'
        if os.path.exists(path_with_html):
            return path_with_html
        
        path_lower_with_html = path_lower + '.html'
        if path_lower_with_html != path_with_html and os.path.exists(path_lower_with_html):
            return path_lower_with_html
    
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
        
        if request_path in ('', 'home'):
            final_path = 'index.html'
        else:
            final_path = find_file_case_insensitive(request_path)
            
            if not final_path:
                final_path = 'index.html'

        if not os.path.exists(final_path):
            final_path = '404.html' if os.path.exists('404.html') else 'index.html'

        if final_path.endswith('.html') and os.path.exists(final_path):
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

        self.send_error(404)

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), AntiCacheHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()
