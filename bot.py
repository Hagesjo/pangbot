import discord
import logging
import random
from discord.ext import commands
from time import sleep

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

    # special, just add for lazy documentation
    'surprise': '',
}

piano = {
    "c" : "C.mp3",
    "c#": "C#.mp3",
    "d" : "D.mp3",
    "d#": "D#.mp3",
    "e" : "E.mp3",
    "f" : "F.mp3",
    "f#": "F#.mp3",
    "g" : "G.mp3",
    "g#": "G#.mp3",
    "a" : "A.mp3",
    "a#": "A#.mp3",
    "b" : "B.mp3",
}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def pang(self, ctx, *, query=""):
        """Plays a file from the local filesystem"""

        if query == "help":
            rows = []
            for k in sounds:
                rows.append(f"!pang {k}")
            await ctx.send('\n'.join(rows))
            return
        elif query == "surprise":
            query = random.choice(list(sounds))


        sound = sounds.get(query.lower())
        if sound:
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'sound/{sound}'))
            ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

            await ctx.send("PANGPANGPANGPANG")

    @commands.command()
    async def sadpang(self, ctx):
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'sound/sad.mp3'))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send("Pang :(")

    @commands.command()
    async def gnap(self, ctx):
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'sound/gnap.mp3'))
        ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send("GNAP GNAP GNAP GNAP")

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
        query = query.split()
        for q in query:
            if q not in piano and q != ";":
                continue
            if q == ";":
                sleep(0.3)
                continue
            sound_file = piano[q]
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(f'sound/piano/{sound_file}'))
            ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)
            sleep(0.3)


    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @sadpang.before_invoke
    @pang.before_invoke
    @pangiano.before_invoke
    @gnap.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            ctx.author.voice.channel.connect()

def main():
    logging.basicConfig(level=logging.INFO)
    bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
                       description='Testlol')
    @bot.event
    async def on_ready():
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')

    bot.add_cog(Music(bot))
    bot.run(token)



if __name__=="__main__":
    main()
