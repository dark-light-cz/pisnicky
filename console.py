import sys
from imports.hovorka import Hovorka
from imports.supermusic import Supermusic

class Console():
    def __init__(self, songbook):
        self.songbook = songbook

    def list_songs(self):
        found = False
        for row in self.songbook.list_songs():
            if not found:
                print("ID - JMENO PISNE - AUTORI")
                found = True
            print(row["id"], " - ", row["name"], " - ", row["authors"])
        if not found:
            print("V databázi nejsou žádné písně")
        # endfor
    # enddef - list_songs

    def add_song(self):
        print("Název:")
        name = input()
        print("Author:")
        author = input()
        print("adejte víceřádkový text, Vkládání ukončíte Ctrl-D:")
        text = ""
        while True:
            try:
                line = input()
            except EOFError:
                break
            text += "\n" + line
        song_id = self.songbook.add_song(
            name=name,
            authors=author,
            text=text, 
        )
        print('\n\nÚspěšně přidáno - id písně:', song_id)
    # enddef - add_song
    
    def transpose_song(self, song_id, trans):
        try:
            self.songbook.transpose(song_id, trans)
        except RuntimeError as e:
            print(str(e))
            sys.exit(-1)
        else:
            print("Transponováno")
    # enddef - transpose_song
    
    def delete_song(self, song_id):
        try:
            self.songbook.delete(song_id)
        except RuntimeError as e:
            print(str(e))
            sys.exit(-1)
        else:
            print("Smazáno")
    # enddef - delete_song

    def print_song(self, songs, template="./template.jinja"):
         
        with open("out.html", "w") as fds:
            fds.write(self.songbook.render(songs, template))
    # enddef - print song


    def import_hovorka(self, fds):
        # create an XMLReader
        h = Hovorka()
        res = self.songbook.import_songs(h.import_file(fds))
        print(
            "Importoval jsem", res["inserted"], "nových písní"
            " a aktualizoval" , res["updated"], "písní"
            "."
        )
    
    def import_supermusic(self, song_id):
        s = Supermusic()
        s.import_song(song_id)
        res = self.songbook.import_songs([s])
        if res["inserted"]:
            print("Importoval jsem novou píseň")
        else:
            print("Akualizoval jsem píseň")

    # endef import_hovorka

    def show_song(self, songs):
        separator = "=====\n"
        for song in self.songbook.get_song(songs):
            song = dict(zip(song.keys(), song))
            for k, v in song.items():
                print("".join((k, ": ", str(v), "\n")))
            # endfor
            print(separator)

    # enddef - show_song




# endclass - Console

