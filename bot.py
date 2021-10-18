import discord
import datetime
import logging
import random
from discord.ext import commands
from time import sleep, time
from pydub import AudioSegment
from threading import Thread
import asyncio
import os

import youtube_dl

token = ""

sounds = {
    '': 'pangorig.mp3',
    'funky': 'arcaneapp.mp3',
    'audi': 'audi.mp3',
    'inget': 'inget.mp3',
    'hermano': 'hermano.mp3',
    'freehermano': 'hermano.mp3',
    'spooky': 'spooky.mp3',
    'sad': 'sad.mp3',
    'komigen': 'komigen.mp3',
    'kom igen': 'komigen.mp3',
    'darth': 'darth.mp3',
    'christmas': 'christmas.mp3',
    'christmasspecial': 'christmasspecial.mp3',

    # special, just add for lazy documentation
    'surprise': '',
}

# piano = {
    # "c" : AudioSegment.from_mp3("sound/piano/C.mp3"),
    # "c#": AudioSegment.from_mp3("sound/piano/C#.mp3"),
    # "d" : AudioSegment.from_mp3("sound/piano/D.mp3"),
    # "d#": AudioSegment.from_mp3("sound/piano/D#.mp3"),
    # "e" : AudioSegment.from_mp3("sound/piano/E.mp3"),
    # "f" : AudioSegment.from_mp3("sound/piano/F.mp3"),
    # "f#": AudioSegment.from_mp3("sound/piano/F#.mp3"),
    # "g" : AudioSegment.from_mp3("sound/piano/G.mp3"),
    # "g#": AudioSegment.from_mp3("sound/piano/G#.mp3"),
    # "a" : AudioSegment.from_mp3("sound/piano/A.mp3"),
    # "a#": AudioSegment.from_mp3("sound/piano/A#.mp3"),
    # "b" : AudioSegment.from_mp3("sound/piano/B.mp3"),
# }

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.loop_running = False
        self.song_start = time()
        self.current_song_info = {}


    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    def get_queue(self, ctx):
        g = ctx.message.guild.name
        if not g in self.queues:
            return []
        return self.queues[g]

    def add_to_queue(self, ctx, song_info):
        g = ctx.message.guild.name
        if not g in self.queues:
            self.queues[g] = [song_info]
        else:
            self.queues[g].append(song_info)

    def pop_from_queue(self, ctx):
        g = ctx.message.guild.name
        if not g in self.queues:
            return ""
        return self.queues[g].pop(0)

    async def embed_queue(self, ctx):
        queue = self.get_queue(ctx)
        if not queue and not self.current_song_info:
            await ctx.send("Nothing is currently playing")
            return

        total_duration = int(self.current_song_info['duration'] - (time() - self.song_start))
        embed = discord.Embed(title="Queue", description="", color=0x00ff00)
        if self.current_song_info:
            embed.add_field(name="Currently playing", value="[{}]({})".format(self.current_song_info['title'], self.current_song_info['webpage_url']), inline=True)
            embed.add_field(name="Length", value="{}".format(datetime.timedelta(seconds=self.current_song_info['duration'])), inline=True)

        if queue:
            embed.add_field(name="\u200b",  value="\u200b", inline=False)

        for i, song_info in enumerate(queue, start=1):
            embed.add_field(name="Position", value=str(i), inline=True)
            embed.add_field(name="Name", value="[{}]({})".format(song_info['title'], song_info['webpage_url']), inline=True)
            embed.add_field(name="Length / Time until played", value="{} / {}".format(
                    datetime.timedelta(seconds=song_info['duration']),
                    datetime.timedelta(seconds=total_duration)),
                inline=True)
            total_duration += song_info['duration']

        await ctx.send(embed=embed)

    @commands.command()
    async def play(self, ctx, *, query="", from_queue=False):
        """Plays a youtube link"""

        if not query.startswith("https://"):
            query = "ytsearch:" + query



        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
        }
    
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            song_info = ydl.extract_info(query, download=False)
            if '_type' in song_info and song_info['_type'] == "playlist":
                song_info = song_info['entries'][0]

        if not from_queue:
            if (ctx.voice_client and ctx.voice_client.is_playing()) or self.get_queue(ctx):
                self.add_to_queue(ctx, song_info)
                await self.embed_queue(ctx)
                return

        ctx.voice_client.play(discord.FFmpegPCMAudio(song_info["formats"][0]["url"]))
        ctx.voice_client.source = discord.PCMVolumeTransformer(ctx.voice_client.source)
        ctx.voice_client.source.volume = 1
        self.song_start = time()
        self.current_song_info = song_info


        await self.embed_queue(ctx)
        if not self.loop_running:
            await self.check_disconnect_loop(ctx)

    async def check_disconnect_loop(self, ctx):
        while True:
            if not ctx.voice_client:
                return
            elif not ctx.voice_client.is_playing():
                if not self.get_queue(ctx):
                    await ctx.voice_client.disconnect()
                    return
                await self.play(ctx, query=self.pop_from_queue(ctx)['webpage_url'], from_queue=True)
            await asyncio.sleep(5)

    @commands.command()
    async def queue(self, ctx, *, query=""):
        """Prints the queue"""
        await self.embed_queue(ctx)

    @commands.command(aliases=["fs"])
    async def skip(self, ctx, *, query=""):
        """Skips the current song. If a number is provided, it will skip to that song in the list"""
        if not ctx.voice_client:
            return

        if not query:
            query = "1"

        if not query.isnumeric():
            await send("Invalid skip number")
            return

        q = int(query)
        num_skips = max(0, q - 1)
        num_skips = min(len(self.get_queue(ctx)), num_skips)
        for i in range(num_skips):
            self.pop_from_queue(ctx)
        ctx.voice_client.stop()
        if q == 1:
            await ctx.send("Ok, skipping")
        else:
            await ctx.send("Ok, skipping to song {}.".format(q))

    @commands.command()
    async def pang(self, ctx, *, query=""):
        """Plays a file from the local filesystem"""
        if query == "help":
            rows = []
            for k in sounds:
                rows.append(f"!pang {k}")
            rows.append("")
            rows.append("!pangstorm")
            rows.append("!sadpang")
            rows.append("!gnap")
            await ctx.send('\n'.join(rows))
            return
        elif query == "surprise":
            query = random.choice(list(sounds))


        sound = sounds.get(query.lower())
        if sound:
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'sound/{sound}'))
            ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

            await ctx.send("PANGPANGPANGPANG")
        await self.check_disconnect_loop(ctx)

    @commands.command()
    async def sadpang(self, ctx):
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'sound/sad.mp3'))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send("Pang :(")
        await self.check_disconnect_loop(ctx)

    @commands.command()
    async def status(self, ctx):
        if ctx.voice_client:
            print(ctx.voice_client.is_playing())

    @commands.command()
    async def pangstorm(self, ctx):
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'sound/pangstorm.wav'))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send("PANG PANG PANG PANG")
        await self.check_disconnect_loop(ctx)

    @commands.command()
    async def gnap(self, ctx):
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'sound/gnap.mp3'))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send("GNAP GNAP GNAP GNAP")
        await self.check_disconnect_loop(ctx)

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def pangiano(self, ctx, *, query):
        """Play the piano"""
        if len(query) == 0:
            return
        query = query.split()

        bpm = query[0]
        if not bpm.isnumeric():
            return
        bpm = int(bpm)
        streams = []

        await ctx.send("Combining files")
        for q in query[1:]:
            if q not in piano and not q.isnumeric():
                continue
            if q.isnumeric():
                bps = 60 / bpm
                streams.append(AudioSegment.silent(duration=1000 * float(q) * bps))
                continue

            sound_file = piano[q]
            streams.append(piano[q])

        combined = AudioSegment.empty()
        for stream in streams:
            combined += stream
        combined.export("tmp.wav", format="wav")
        await ctx.send("Files combined")


        await ctx.send("Processing...")
        source = discord.FFmpegOpusAudio("tmp.wav")
        await ctx.send("Processing done. Playing")
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)
        await check_disconnect_loop(ctx)


    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        self.queues[ctx.message.guild.name] = []
        self.current_song_info = {}
        await ctx.voice_client.disconnect()

    @sadpang.before_invoke
    @pang.before_invoke
    @pangstorm.before_invoke
    @pangiano.before_invoke
    @gnap.before_invoke
    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        # elif ctx.voice_client.is_playing():
            # ctx.voice_client.stop()
            # ctx.author.voice.channel.connect()


def main():
    logging.basicConfig(level=logging.INFO)
    bot = commands.Bot(command_prefix=commands.when_mentioned_or("."),
                       description='Testlol')
    @bot.event
    async def on_ready():
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')

    bot.add_cog(Music(bot))
    bot.run(token)



if __name__=="__main__":
    main()
