import http.server, socketserver, os

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

class AntiCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Clear-Site-Data', '"cache"')
        super().end_headers()

    def do_GET(self):
        clean_path = self.path.split('?')[0].strip('/')
        
        if clean_path in ('', 'home'):
            self.path = '/index.html'
        else:
            alt_html = clean_path + '.html'
            
            if os.path.exists(clean_path):
                pass
            elif os.path.exists(alt_html):
                self.path = '/' + alt_html
            else:
                if not clean_path.endswith('.html'):
                    if os.path.exists('index.html'):
                        self.path = '/index.html'
                    else:
                        self.path = '/404.html'
                else:
                    self.path = '/404.html'

        local_path = self.path.lstrip('/')
        if not os.path.exists(local_path):
            self.path = '/404.html' if os.path.exists('404.html') else '/index.html'
            local_path = self.path.lstrip('/')

        if local_path.endswith('.html') and os.path.exists(local_path):
            try:
                with open(local_path, 'rb') as f:
                    content = f.read()
                pos = content.find(b'</head>')
                body = content[:pos] + JS_BYPASS + content[pos:] if pos != -1 else JS_BYPASS + content
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(body)
                return
            except:
                pass
        
        return super().do_GET()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), AntiCacheHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()
