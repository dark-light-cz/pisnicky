import sqlite3
from jinja2 import Environment, BaseLoader
from song import Song
from czech_sort import key as czkey


def czech_sort(arr, attr):
    return sorted(arr, key=lambda s: czkey(s[attr]))


class SongBook:
    def __init__(self, dbname):
        self.conn = sqlite3.connect(dbname)
        self.conn.row_factory = sqlite3.Row 
        self.prepare_db()
    # enddef

    def prepare_db(self):
        # check if new database is needded
        cur = self.conn.cursor()

        cur.execute("""
            SELECT name FROM sqlite_master WHERE type='table' 
            AND name='songs';""")
        val = cur.fetchone()
        if not val:
            cur.execute("""
                CREATE TABLE songs (
                    song_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name text,
                    authors text,
                    text text,
                    rythm char(8),
                    capo int not null default 0,
                    bpm int,
                    source text,
                    extid text,
                    transpose int not null default 0,
                    cols int,
                    fontsize int,
                    chordsplace varchar(20) not null default "default"
                );
            """)
        self.conn.commit()
    # enddef - prepare_db

    def get_song(self, songs, cur=None):
        commit = False
        if cur is None:
            commit = True
            cur = self.conn.cursor()
        cur.execute(
            "select * from songs where song_id in (" + 
            ", ".join(["?"]*len(songs)) + 
            ")",
            tuple(songs)
        )
        for one in cur:
            yield one
        if commit:
            self.conn.commit()

    def list_songs(self, cur=None):
        commit = False
        if cur is None:
            commit = True
            cur = self.conn.cursor()
        cur.execute("select song_id, name, authors from songs")
        songs = cur.fetchall()
        songs.sort(key=lambda s: czkey(s["name"]))
        for i in songs:
            yield i
        if commit:
            self.conn.commit()
    # enddef list

    def import_songs(
        self, songs, cur=None
    ):
        commit = False
        if cur is None:
            commit = True
            cur = self.conn.cursor()
        inserted = 0
        updated = 0
        ids = {}
        for song in songs:
            if song.get("source") and song.get("extid"):
                cur.execute(
                    "select song_id from songs where source=? and extid=?",
                    (song["source"], song["extid"])
                )
                s = cur.fetchone()
                if s:
                    self.update_song(cur=cur, song_id=s[0], **song)
                    ids[(song["source"], song["extid"])] = s[0]
                    updated += 1
                else:
                    if "authors"  not in song:
                        song["authors"] = ""
                    s_id = self.add_song(cur=cur, **song)
                    ids[(song["source"], song["extid"])] = s_id
                    inserted += 1
            else:
                self.add_song(cur=cur, **song)
                inserted += 1
        if commit:
            self.conn.commit()
        return {
            "inserted": inserted,
            "updated": updated,
            "ids": ids

        }
    
    def update_song(
        self, song_id,
        cur=None,
        **kwargs
    ):
        commit = False
        if cur is None:
            commit = True
            cur = self.conn.cursor()
        cols = {}
        for k in (
            "name", "authors", "text", "rythm", "capo", "bpm", "source", 
            "extid", "transpose", "cols", "fontsize", "chordsplace"
        ):
            if k in kwargs:
                if kwargs[k] == 'None':
                    kwargs[k] = None
                cols[k] = kwargs[k]
        
        qry = "update songs set " + ", ".join(
            col + "=?"
            for col in cols
        ) + " where song_id = ?"
        
        cur.execute(qry, tuple(cols.values()) + (song_id,))
        lastrowid = cur.lastrowid
        
        if commit:
            self.conn.commit()
        return lastrowid

    def add_song(
        self, name, authors, text, 
        rythm=None, capo=0, bpm=None, source=None, extid=None, transpose=0,
        cur=None, cols=None, fontsize=None, chordsplace="default"
    ):
        commit = False
        if cur is None:
            commit = True 
            cur = self.conn.cursor()

        cur.execute("""insert into songs 
    (
        name,authors,text,rythm,capo,bpm,source,extid,transpose,
        cols,fontsize,chordsplace
    )
    values
    (
        ?   ,?      ,?   ,?    ,?   ,?  ,?     ,?    ,?        ,
        ?   ,?       ,?
    )
                """, (
            name, authors, text, rythm, capo, bpm, source, extid, transpose,
            cols, fontsize, chordsplace
        ))
        lastrowid = cur.lastrowid
        
        if commit:
            self.conn.commit()
        return lastrowid

    def transpose_song(self, song_id, trans, cur=None):
        commit = False
        if cur is None:
            commit = True
            cur = self.conn.cursor()
        cur.execute(
            "update songs set transpose = transpose + ? where song_id in (" + 
            ", ".join(["?"]*len(song_id)) + 
            ")",
            (trans,) + tuple(song_id)
        )
        if cur.rowcount != len(song_id):
            raise RuntimeError("Nenalezeno")
        if commit:
            self.conn.commit()

    def delete(self, song_id, cur=None):
        commit = False
        if cur is None:
            commit = True
            cur = self.conn.cursor()
        cur.execute(
            "delete from songs where song_id in (" + 
            ", ".join(["?"]*len(song_id)) + 
            ")",
            tuple(song_id)
        )
        if cur.rowcount != len(song_id):
            raise RuntimeError("Nenalezeno")
        if commit:
            self.conn.commit()

    def render(self, songs, template="./template.jinja", cur=None, toc=True):
        tpl = Environment(loader=BaseLoader()).from_string(
            open(template).read()
        )
        qry = "select * from songs"
        q_args = []

        if songs:
            qry += " where song_id in ("
            qry += ", ".join(["?"] * len(songs))
            qry += ")"
            q_args.extend(songs)
        # endif

        qry += " order by name asc"
        commit = False
        if cur is None:
            commit = True
            cur = self.conn.cursor()
        cur.execute(qry, q_args)
        try: 
            return tpl.render(
                songs=sorted(
                    (Song(**i) for i in cur),
                    key=lambda s: czkey(s.name)
                ),
                print_toc=toc,
                czech_sort=czech_sort,
            )
        finally:
            if commit:
                self.conn.commit()
# eof    
