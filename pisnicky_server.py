#! /usr/bin/python3
import http.server
import socketserver
from imports.supermusic import Supermusic
from songbook import SongBook, Song
from urllib.parse import urlparse
from urllib.parse import parse_qs
from time import sleep

PORT = 8000

DB = "./songs.sqlite3"

song_cols = (
    "name", "authors", "text", "rythm", "capo", "bpm", "source", "extid",
    "transpose"
)

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
            out = open("index.html", "rb").read()
        elif req.path == "/list":
            s = SongBook("./songs.sqlite3")
            out="""
            <html>
                <head>
                </head>
                <body>
                    <h1>Seznam písní</h1>
                    <ul>"""
            for song in s.list_songs():
                out += f'''<li>
                    {song["name"]}
                    <a href="/print?id={song["song_id"]}">Tisk</a>
                    <a href="/edit?id={song["song_id"]}">Upravit</a>
                    <a href="/delete?id={song["song_id"]}" onclick='javascript:confirm("Opravdu smazat?")'>Smazat</a>
                </li>'''
            out += """
                    </ul>
                </body>
            </html> """
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
        elif req.path == "/edit" or req.path == "/new":
            if req.path == '/new':
                song = Song()
            else:
                query_components = parse_qs(req.query)
                song_id = [int(query_components["id"][0])]
                s = SongBook("./songs.sqlite3")
                song = Song(**(list(s.get_song(song_id))[0]))
            # endif
            out=f"""
            <html>
                <head>
                    <style>
                        body {{
                            font-size: 18px;
                        }}
                        textarea,
                        input {{ 
                            font-size: 18px; font-family: monospace; 
                        }}
                    </style>
                </head>
                <body>
                    <h1>Edit písně</h1>
                    <a href="/">Domů</a><br/>
                    <form method="POST">
                        <label for="id">ID:</label> <input id="id" name="id" value="{song.song_id}" readonly><br>
                        <label for="name">Jméno:</label> <input id="name" name="name" value="{song.name}"><br>
                        <label for="authors">Autoři:</label> <input id="authors" name="authors" value="{song.authors}"><br>
                        <label for="capo">Capo:</label> <input id="capo" name="capo" value="{song.capo}" type="number" min='0' max='10'><br>
                        <label for="bpm">tempo:</label> <input id="bpm" name="bpm" value="{song.bpm}" type="number"><br>
                        <label for="transpose">Zobrazit transponované o:</label> <input id="transpose" name="transpose" value="{song.transpose}" type="number" min='-10' max='10'><br>
                        <label for="source">Zdroj:</label> <input id="source" name="source" value="{song.source}" readonly><br>
                        <label for="extid">Externí id:</label> <input id="extid" name="extid" value="{song.extid}" readonly><br>
                        <textarea name="text" style="width:100%;height:500px">{song.text}</textarea><br>
                        <input type="submit" value="Uložit" name="submit"><br>
                    </form>
                    <pre>{song.normalize_text()}</pre><br>
                    <iframe src="/print?id={song.song_id}" style="width:100%;height:750px"></iframe>
                </body>
            </html> """

        if not out:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes(f"Stránka '{req.path}' nenalezena", 'utf8'))
            return 

        # Sending an '200 OK' response
        self.send_response(200)

        # Setting the header
        self.send_header("Content-type", "text/html")

        # Whenever using 'send_header', you also have to call 'end_headers'
        self.end_headers()

        self.wfile.write(
            out 
            if isinstance(out, bytes)
            else bytes(out, "utf8")
        )

        return

while True:
    try:
        with socketserver.TCPServer(("", PORT), PisnickyHandler) as httpd:
            print(f"Started server at localhost:{PORT}")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 48:
            print("Port je obsazen - čekám na uvolnění")
            for i in range(9, -1, -1):
                print(i, end="\r")
                sleep(1)
            print("\n")
        else:
            raise
            
