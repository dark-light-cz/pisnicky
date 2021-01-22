from chord_images import KnownChords
from pychord import Chord as PyChord
import re
import traceback
from copy import deepcopy

# TODO
"""
[A]Byly krásný naše [D]plány [Asus4 A] byla jsi můj celej [F#mi]svět

Zde dojde k chybě v zobrazení akordu [Asus4 A] kdy vypadá takhle
A----------------D-----Asus4 A-------------F#mi--Fmi---Emi--
Byly krásný naše plány  byla jsi můj celej svět ++++++++++++
"""


class Song(list):
    @property
    def width(self):
        return max(i.width for i in self)

    def __init__(
        self, 
        song_id=None,
        name=None,
        authors=None,
        text=None,
        rythm=None,
        capo=None,
        bpm=None,
        source=None,
        extid=None,
        transpose=0
    ):
        self.song_id = song_id
        self.name  = name
        self.authors = authors
        self.rythm  = rythm
        self.capo  = capo
        self.bpm = bpm
        self.source = source
        self.extid = extid
        self.transpose = transpose
        self.used_chords = set()
        # use setter => parse
        self.text = text

    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, val):
        self._text = val or ""
        for one in self[:]:
            self.remove(one)
        # endfor
        self._parse_song()

    def append(self, itm):
        if isinstance(itm, Chorus) and not itm:
            # refrén můžeš přidat prázdný
            pass
        elif not itm:
            # nepřidávej prázdné
            return 
        super().append(itm)

    add = append

    def normalize_text(self):
        out = ""
        for block in self:
            if block.kind == 'chorus':
                out += "Ref:\n"
            elif block.kind == 'verse' and block.pos:
                out += f"{block.pos}:\n"
            # endif
            for line in block:
                for el in line:
                    if el.chord:
                        out += f"[{el.chord}]"
                    if el.text:
                        out += el.text
                    out += " " * el.spaces
                # endfor
                out += "\n"
            # endfor
            out += '\n'
        # endfor
        return out

    def _parse_song(self):
        self.used_chords = set()
        # split song - simple fsm
        chord = False
        songlines = []
        songparts = Line()
        part = ""
        for char in self.text.strip("\n"):
            if chord and char == ']':
                try:
                    songparts.append(Block(
                        chord=" " + part + " ", transpose=self.transpose
                    ))
                except:
                    traceback.print_exc()
                    print(f"Neznámý akord : {part}")
                    songparts.append(Block(text="[" + part + "]"))
                else:
                    self.used_chords.add(songparts[-1].chord)
                part = ""
                chord = False
            elif not chord and char == '[':
                if part:
                    songparts.append(Block(text=part))
                part = ""
                chord = True
            elif char == '\r':
                pass
            elif char == '\n':
                if part:
                    # nepřidávám mezery na konec řádku
                    if not all(i==" " for i in part):
                        songparts.append(Block(
                            chord = part if chord else None,
                            text = part if not chord else None
                        ))
                    # endif
                    part = ""
                    chord = False
                songparts.normalize()
                songlines.append(songparts)
                songparts = Line()
            else:
                part += char
            # endif
        # endfor
        if songparts or part:
            if part:
                songparts.append(Block(text=part))
            # file not ending with \n
            songparts.normalize()
            songlines.append(songparts)

        # teď mám lines a můžu zkusit rozdělit na sloky:
        if not songlines:
            return []

        # TODO pokud začínají všechny sloky mezerami jako 
        # např u https://supermusic.cz/skupina.php?action=piesen&idpiesne=1089
        # nedojde k rozpoznání Refrénové značky :-/

        # ověř začátek
        actBlock = Paragraph()
        for songline in songlines:
            if not songline:
                # prázdná řádka dává nový vždy nový odstavec
                self.add(actBlock)
                actBlock = Paragraph()
            elif songline[0].is_chorus_start:
                # začátek refrénu vždy dá blok refrénu
                self.add(actBlock)
                actBlock = Chorus()
                songline[0].strip_chorus_start()
                if not songline[0].text and not songline[0].chord:
                    if len(songline) != 1:
                        actBlock.append(songline)
                else:
                    actBlock.append(songline)
            elif songline[0].is_verse_start:
                # začátek sloky vždy dá blok sloky
                self.add(actBlock)
                actBlock = Verse()
                actBlock.pos = songline[0].strip_verse_start()
                actBlock.append(songline)
            else:
                actBlock.append(songline)
            # endif
        # endfor
        self.add(actBlock)


ChordImageCache = {}

ChordTranslate = {
    "Gbm": "F#m",
}

for k, v in ChordTranslate.items():
    if k in KnownChords:
        KnownChords[v] = KnownChords[k]
# endfor

class Chord(PyChord):

    def __hash__(self):
        return str(self).__hash__()

    def __str__(self):
        ret = super().__str__()
        # extrní libka používá pro některé akordy cizí zápis a my je chceme 
        #   v nám známém českém
        if ret in ChordTranslate:
            return ChordTranslate[ret]
        elif ret[0] == "B" and (len(ret)<2 or ret[1] != 'b'):
            return "H" + ret[1:]
        return ret
    
    @property 
    def has_svg(self):
        if str(self) not in KnownChords:
            print("Chybí definice prstokladu akordu", str(self))
            return False
        return True
        # return str(self) in KnownChords

    def svg(self, width=None, height=None):
        c = KnownChords.get(str(self))
        if not c:
            print("Chybí definice prstokladu akordu", str(self))
            return None
        k = (str(self), width, height)
        img = ChordImageCache.get(k)
        if img:
            return img
        oldstyle = deepcopy(c.style)
        scale = 1
        if width and height:
            scale = min(
                height / c.style["drawing"]["height"],
                width / c.style["drawing"]["width"]
            )
            c.style["drawing"]["height"] = width
            c.style["drawing"]["width"] = height
        elif width:
            scale = width / c.style["drawing"]["width"]
            c.style["drawing"]["height"] *= scale
            c.style["drawing"]["width"] = width
        elif height:
            scale = height / c.style["drawing"]["height"]
            c.style["drawing"]["width"] *= scale
            c.style["drawing"]["height"] = height

        c.style["drawing"]["font_size"] = 15 * scale
        c.style["drawing"]["spacing"] = 30 * scale
        # zvětšit nebo zmenšit kolečko ekvivalentně
        c.style["marker"]["radius"] = (12 * scale)
        # split odstraní hlavičku xml -> protože chci embedovat
        ret = c.render().getvalue().split('\n', 1)[1]
        ChordImageCache[k] = ret
        c.style = oldstyle
        return ret


class Line(list):
    @property
    def len(self):
        return sum(len(i) for i in self)
        
    @property
    def chordline(self):
        return any(i.chord for i in self)
    
    @property
    def textline(self):
        return any(i.text for i in self)
    
    @property
    def mixline(self):
        return self.textline and self.chordline

    def normalize(self):
        if len(self) < 2:
            return
        prev = None
        for this in self[:]:
            if not prev:
                # prev is not set advance
                pass
            elif not prev.chord and not prev.text:
                # prev is only space advance
                pass
            elif prev.chord and not prev.text:
                # prev is pure chord
                if this.chord:
                    # this is chord - can't merge - advance
                    pass
                elif this.text:
                    # prev is pure chord an this is pure text:
                    this_len = len(this.text) + this.spaces
                    prev_len = (
                        len(str(prev.chord)) + prev.chord_spaces + prev.spaces
                    )
                    this.origchord = prev.origchord
                    this.chord = prev.chord
                    this.chord_spaces = prev.chord_spaces
                    if prev_len > this_len:
                        this.spaces += prev_len - this_len
                    self.remove(prev)
                    prev = None
                    continue
                elif this.spaces:
                    # don't merge texts
                    pass
            else:
                # prev is not chord - advance
                pass
            prev = this
        # endfor
    # enddef
# endclass
            

class Block:
    _chorus_starts = re.compile(r'^(R(ef)?((\.?:)|(\.)))|(®:?)')
    _verse_starts = re.compile(r'^(\d+)[.:]?\)?')

    def __len__(self):
        return max(
            len(self.text or "") + self.spaces,
            len(str(self.chord or "")) + self.chord_spaces
        )

    def __init__(self, text=None, chord=None, transpose=0):
        self.chord = None
        self.chord_spaces = 0
        self.origchord = None
        if chord:
            origchord = chord
            initial_chord_len = len(chord) 
            chord = chord.strip()
            if "," in chord:
                chord = chord.split(',')
            if ' ' in chord:
                chord = chord.split(' ')
            if "(" in chord:
                chord = [
                        j.strip()
                        for i in chord.split("(")
                        for j in i.split(")")
                        if j.strip()
                    ]
            # TODO tady je potřeba udělat multiakord podle toho co to je 
            #   začít to zpracovávat
            #   1) "C(D)" - při opakování refrénu se hraje jiná tónina ...
            #   2) "Dmi, Ami,.." na samostaném řádku je to vlastně předehra
            #   3) "Dmi, Ami, ..." na konco sloky je to vlastně mezihra nebo 
            #       vyhrávka na konci
            if isinstance(chord, list):
                print("!"*20, "Chyba zpracování multi-akordu ", origchord)
                chord=chord[0]
                self.origchord = origchord
            chord_split = chord.split("/")
            for idx, chordpart in enumerate(chord_split):
                chordpart = chordpart[0].upper() + chordpart[1:]
                # pychordpart neumí pracovat s H ale anglicky B
                if chordpart.startswith("H"):
                    chordpart = "B" + chordpart[1:]
                # pychordpart neumí pracovat s Ami ale jen s Am
                if chordpart.endswith("mi"):
                    chordpart = chordpart[:-1]
                elif chordpart.endswith("mi7"):
                    chordpart = chordpart[:-2] + "7"
                elif chordpart.endswith("7maj"):
                    chordpart = chordpart[:-4] + "maj7"
                elif chordpart.endswith("4sus"):
                    chordpart = chordpart[:-4] + "sus4"
                chord_split[idx] = chordpart
            chord = "/".join(chord_split)
            self.chord = Chord(chord)
            if transpose:
                self.chord.transpose(transpose)
            self.chord_spaces = initial_chord_len - len(str(self.chord))
        # endif
        if text and all(i == " " for i in text):
            self.spaces = len(text)
            self.text = None
        else:
            self.text = text
            self.spaces = 0
        # endif
    # endef
    
    @property
    def is_chorus_start(self):
        # TODO nerozpoznává se vícenásobný refrén
        #   např "2 x R:" (supermusic 1089)
        
        return self.text and self._chorus_starts.match(self.text)

    def strip_chorus_start(self):
        if not self.is_chorus_start:
            raise RuntimeError(
                "Nemůžeš odstraňovat refrénovou zančku z něčeho kde není"
            )
        match = self.text and self._chorus_starts.match(self.text)
        if not match:
            raise RuntimeError(
                "Nemůžeš odstraňovat číslo sloky kde není"
            )
        grp = match.group(0)
        self.text = self.text[len(grp):]
        if self.text and self.text[0] == " ":
            self.text = self.text[1:]
    # endef strip_chorus_start
    
    @property
    def is_verse_start(self):
        return self.text and self._verse_starts.match(self.text)

    def strip_verse_start(self):
        match = self.text and self._verse_starts.match(self.text)
        if not match:
            raise RuntimeError(
                "Nemůžeš odstraňovat číslo sloky kde není"
            )
        grp = match.group(0)
        self.text = self.text[len(grp):]
        if self.text and self.text[0] == " ":
            self.text = self.text[1:]
        return match.group(1)

    # endef strip_chorus_start

    def __repr__(self):
        return f'Block(text:"{self.text}",chord:"{self.chord}", space:{self.spaces}, chordSpace:{self.chord_spaces})'  # noqa
    
    @property
    def after_origchord_space(self):
        if not self.origchord:
            raise RuntimeError(
                "Cant' use origchord space without origchord set")
        if not self.text:
            return 0
        else:
            ocl = len(self.origchord)
            text_len = len(self.text) + self.spaces
            max(text_len - ocl, 0)

    @property
    def after_chord_space(self):
        if self.chord:
            if self.text:
                # expected text length 
                text_len = len(self.text) + self.spaces
                # expected chord length 
                chord_len = len(str(self.chord)) + self.chord_spaces
                return max(text_len, chord_len) - len(str(self.chord))
                # chord and text mixed
            else:
                # only chord
                return self.chord_spaces
        elif self.text:
            # only text
            return len(self.text) + self.spaces
        else:
            return self.spaces
        """
        if not self.text and not self.chord:
            return self.spaces
        if not self.text:
            return max(max(self.spaces, self.chord_spaces) - len(self.chord), 0)
        if not self.chord:
            return len(self.text)
        return max(len(self.text) - len(self.chord), 0)
        """
    
    @property
    def after_text_space(self):
        if self.text:
            if self.chord:
                # expected text length 
                text_len = len(self.text)
                # expected chord length 
                chord_len = len(str(self.chord)) + self.chord_spaces
                return max(text_len, chord_len) - len(self.text)
            else:
                return self.spaces
        elif self.chord:
            # only chord 
            return len(str(self.chord)) + self.chord_spaces
        else:
            return self.spaces
        """
        if not self.text and not self.chord:
            return self.spaces
        if not self.chord:
            return max(self.spaces - len(self.text), 0)
        if not self.text:
            return len(self.chord)
        return max(len(self.chord) - len(self.text), 0)
    """


class SongBlock(list):
    kind = ""
    @property
    def width(self):
        if not self:
            return 0
        return max(i.len for i in self)


class Paragraph(SongBlock):
    kind = "paragraph"


class Verse(SongBlock):
    kind = "verse"
    pos = None


class Chorus(SongBlock):
    kind = "chorus"


class Recital(SongBlock):
    kind = "recital"
