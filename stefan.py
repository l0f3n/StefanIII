import discord
from discord.ext import commands

class Stefan(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        commands.Bot.__init__(self, *args, **kwargs)

        self.current_context = None
        self.latest_context = None
        
        self.before_invoke(self._handle_before_invoke)
        self.after_invoke(self._handle_after_invoke)

    async def _handle_before_invoke(self, ctx):
        self.current_context = ctx
        self.latest_context = ctx
        await ctx.message.add_reaction("👌")

    async def _handle_after_invoke(self, ctx):
        self.current_context = None
        await ctx.message.remove_reaction("👌", self.user)
        await ctx.message.add_reaction("👍")

    async def close(self):
        for cog in self.cogs.values():
            await cog.close()

        if self.latest_context:
            await self.latest_context.send("Jag dör! 😱")

        return await super().close()

    async def join_channel(self):
        """
        Joins the users channel given the current context.
        """
        if not self.current_context:
            return
        
        if self.current_context.author and self.current_context.author.voice:
            if self.current_context.guild and self.current_context.guild.voice_client:
                if self.current_context.author.voice.channel != self.current_context.guild.voice_client.channel:
                    await self.current_context.guild.voice_client.move_to(self.current_context.author.voice.channel)
            else:
                await self.current_context.author.voice.channel.connect()

    async def on_ready(self):
        print("Stefan anmäler sig för tjänstgöring.")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ert skitsnack"))
