#! /usr/bin/python3
import http.server
import socketserver
from imports.supermusic import Supermusic
from songbook import SongBook, Song
from urllib.parse import urlparse
from urllib.parse import parse_qs
from time import sleep
from jinja2 import Environment, FileSystemLoader
from jinja2.environment import TemplateStream
import types

PORT = 8000

DB = "./songs.sqlite3"

song_cols = (
    "name", "authors", "text", "rythm", "capo", "bpm", "source", "extid",
    "transpose"
)

def render(template, data):
    env = Environment(loader=FileSystemLoader('./template'))
    tpl = env.get_template(template)
    return tpl.stream(**data)


class PisnickyHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        req = urlparse(self.path)
        if req.path == "/edit":
            query_components = parse_qs(req.query)
            song_id = int(query_components["id"][0])
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            components = parse_qs(post_data.decode("utf8"))
            song = {
                "song_id": song_id
            }
            for k in song_cols:
                if k in components:
                    song[k] = components[k][0]
                # endif
            # endfor
            s = SongBook("./songs.sqlite3")
            s.update_song(**song)
            self.send_response(303)
            self.send_header("Location", f"/edit?id={song_id}")
            self.end_headers()
            return
        elif req.path == "/new":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            components = parse_qs(post_data.decode("utf8"))
            song = {}
            for k in song_cols:
                if k in components:
                    song[k] = components[k][0]
                # endif
            # endfor
            s = SongBook("./songs.sqlite3")
            song_id = s.add_song(**song)
            self.send_response(303)
            self.send_header("Location", f"/edit?id={song_id}")
            self.end_headers()
            return
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes(f"Stránka '{req.path}' nenalezena", 'utf8'))
            return 


    def do_GET(self):
        out = None
        req = urlparse(self.path)
        if req.path == "/print":
            s = SongBook(DB)
            song_id = None
            query_components = parse_qs(req.query)
            if 'id' in query_components:
                song_id = [int(query_components["id"][0])]
            out = s.render(song_id, toc=not bool(song_id))
        elif req.path == "/":
            out = render("list.jinja", {})
        elif req.path == "/list":
            s = SongBook("./songs.sqlite3")
            out = render("list.jinja", {"songs": s.list_songs()})
        elif req.path == "/import/supermusic":
            query_components = parse_qs(req.query)
            song_id = int(query_components["id"][0])
            sm= Supermusic()
            song = sm.import_song(song_id)
            s = SongBook(DB)
            r = s.import_songs([song])
            s_id = r["ids"][(song["source"], song["extid"])]

            self.send_response(303)
            self.send_header("Location", f"/edit?id={s_id}")
            self.end_headers()
            return
        elif req.path == "/delete":
            query_components = parse_qs(req.query)
            song_id = [int(query_components["id"][0])]
            s = SongBook("./songs.sqlite3")
            s.delete(song_id)
            self.send_response(303)
            self.send_header("Location", f"/list")
            self.end_headers()
            return
        elif req.path == "/new":
            song = Song()
            out = render("new.jinja", {"song": song})
        elif req.path == "/edit":
            query_components = parse_qs(req.query)
            song_id = [int(query_components["id"][0])]
            s = SongBook("./songs.sqlite3")
            song = Song(**(list(s.get_song(song_id))[0]))
            out = render("edit.jinja", {"song": song})
        
        if not out:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes(f"Stránka '{req.path}' nenalezena", 'utf8'))
            return 

        # Sending an '200 OK' response
        self.send_response(200)

        # Setting the header
        self.send_header("Content-type", "text/html; charset=UTF-8")

        # Whenever using 'send_header', you also have to call 'end_headers'
        self.end_headers()

        if isinstance(out, (types.GeneratorType, TemplateStream)):
            for buff in out:
                self.wfile.write(
                    buff 
                    if isinstance(buff, bytes)
                    else bytes(buff, "utf8")
                )
        else:
            self.wfile.write(
                out 
                if isinstance(out, bytes)
                else bytes(out, "utf8")
            )

        return

socketserver.TCPServer.allow_reuse_address = True
while True:
    try:
        with socketserver.TCPServer(("", PORT), PisnickyHandler) as httpd:
            print(f"Started server at localhost:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt as e:
        httpd.shutdown()
        break;
    except OSError as e:
        if e.errno == 48:
            print("Port je obsazen - čekám na uvolnění")
            for i in range(9, -1, -1):
                print(i, end="\r")
                sleep(1)
            print("\n")
        else:
            raise
            
