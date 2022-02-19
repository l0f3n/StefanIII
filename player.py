from discord import Embed, Color, FFmpegOpusAudio
from discord.ext import commands
import yt_dlp

class Player:
    def __init__(self):
        self.current_song = 0
        self.playlist = []

    def test(self):
        print("Det funkade...")

    def queue(self, ctx, url):
        YDL_OPTIONS = {
            'format': 'bestaudio',
            'extract-audio': True,
            'audio-format ': "opus",
            '--id': True,
            'outtmpl': "./downloads/%(title)s.%(ext)s"
        }
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            # The URL to playlists contain the substring 'list'
            if url.find('list') != -1:
                pass
            else:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", None).replace("\"", "\'")
                ydl.download([url])
                self.playlist.append(title)
                print(self.playlist[self.current_song])

    def play(self, ctx):
        if not ctx.voice_client.is_playing():
            song = "./downloads/" + str(self.playlist[self.current_song]) + ".webm"
            source = FFmpegOpusAudio(song)
            ctx.voice_client.play(source)
            self.current_song = self.current_song + 1
        
#
#    def pause(self, ctx):
#
#    def play_next(self, ctx):
#
#    def play_previous(self, ctx):
#
#    def clear_queue(self, ctx):