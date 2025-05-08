from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json

class S(BaseHTTPRequestHandler):

    def do_GET(self):
        # read title from path
        title = self.path[1:]
        rss_file = os.path.join('rss', f'{title}.jsonl')

        # check if file exists
        if not os.path.exists(rss_file):
            self.send_response(404)
            self.end_headers()
            return
        
        # load rss and send
        with open(rss_file) as f:
            rss = [json.loads(i) for i in f.read().splitlines()]
            rss.reverse()

        # create xml and send response
        xml = make_xml(title, rss)
        self.send_response(200)
        self.send_header("Content-type", 'text/xml')
        self.send_header("Content-Length", len(xml))
        self.end_headers()
        self.wfile.write(xml.encode('utf-8'))

    def do_POST(self):
        # read title from path
        title = self.path[1:]
        rss_file = os.path.join('rss', f'{title}.jsonl')

        # read data from POST body
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length)

        # check if valid json
        try:
            js = json.loads(data)
            if not ('name' in js and 'magnet' in js):
                raise Exception('Bad request')
        except:
            self.send_response(400)
            self.end_headers()
            return
        
        # fix escaping
        js['magnet'] = js['magnet'].replace('&', '&amp;')

        # append to jsonl
        with open(rss_file, 'a') as f:
            json.dump(js, f)
            f.write('\n')

        # send OK
        self.send_response(200)
        self.end_headers()

def make_xml(title, items):
    content = ''
    for item in items:
        content += f'<item><title>{item["name"]}</title><enclosure url=\"{item["magnet"]}\" type="application/x-bittorrent" /><guid>{item["guid"]}</guid></item>'
    return f'<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>{title}</title>{content}</channel></rss>'    

def start(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, S)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()