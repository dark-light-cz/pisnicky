import xml.sax

class HovorkaSongHandler(xml.sax.ContentHandler):
    def __init__(self, ):
        self.songs = []
        self.depth = 0
        self.reset_vals()

    def reset_vals(self):
        self.song_id = ""
        self.name = ""
        self.authors = ""
        self.text = ""
        self.rythm = ""
        self.capo = ""
        self.bpm = ""

    def startElement(self, tag, attributes):
        print(">" * self.depth, "Enter", tag)
        self.depth += 1
        self.CurrentData = tag

    # Call when an elements ends
    def endElement(self, tag):
        self.depth -= 1
        print(">" * self.depth, "Leave", tag)
        self.CurrentData = None
        if tag == "song":
            self._insert_song()
            self.reset_vals()
        # endif
    # enddef - endElement

    def _insert_song(self):
        self.songs.append({
            "name": self.name.strip(),
            "authors": self.authors.strip() or None,
            "text": self.text.rstrip(),
            "rythm": self.rythm.strip() or None,
            "capo": self.capo or 0,
            "bpm": int(self.bpm.strip() or 0) or None,
            "extid": self.song_id.strip(),
            "source": 'hovorka',
        })

    # Call when a character is read
    def characters(self, content):
        print(">" * (self.depth + 1), "Contents:", repr(content))
        if self.CurrentData == "ID":
            self.song_id += content
            # endif
        elif self.CurrentData == "title":
           self.name += content
        elif self.CurrentData == "author":
           self.authors += content
        elif self.CurrentData == "songtext":
           self.text += content
        """
        elif self.CurrentData == "":
           self.rythm = content
        elif self.CurrentData == "":
           self.capo = content
        elif self.CurrentData == "":
           self.bpm = content
        """

class Hovorka():
    def __init__(self):
        pass
    
    def import_file(self, fds):
        # create an XMLReader
        parser = xml.sax.make_parser()
        # turn off namepsaces
        parser.setFeature(xml.sax.handler.feature_namespaces, 0)

        # override the default ContextHandler
        hsh = HovorkaSongHandler()
        parser.setContentHandler(hsh)
        parser.parse(fds)
        return hsh.songs

