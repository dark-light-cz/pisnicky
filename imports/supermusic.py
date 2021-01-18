import requests

class Supermusic():
    def __init__(self):
        pass
    
    def import_song(self, song_id):
        url = (
            f"https://supermusic.cz/export.php"
            f"?idpiesne={song_id}&stiahni=1&typ=TXT"
        )
        resp = requests.get(url)
        resp.raise_for_status()
        text = resp.text.rstrip()
        if not text:
            raise RuntimeError(
                f"Tato píseň nebyla nalezena nebo je prázdná! ({url})"
            )
        # endif
        name, text = text.split("\n", 1)
        name = name.strip()

        return {
            "name": name,
            "text": text, 
            "extid": str(song_id),
            "source": 'supermusic'
        }
    # endef import_song
