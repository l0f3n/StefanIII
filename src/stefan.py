import discord
from discord.ext import commands

class Stefan(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        commands.Bot.__init__(self, *args, **kwargs)

        self.latest_context = None
        
        self.before_invoke(self._handle_before_invoke)
        self.after_invoke(self._handle_after_invoke)

    async def _handle_before_invoke(self, ctx):
        self.latest_context = ctx
        await ctx.message.add_reaction("👌")

    async def _handle_after_invoke(self, ctx):
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
        if not self.latest_context:
            return

        ctx = self.latest_context
        
        if ctx.author and ctx.author.voice:
            if ctx.guild and ctx.guild.voice_client:
                if ctx.author.voice.channel != ctx.guild.voice_client.channel:
                    await ctx.guild.voice_client.move_to(ctx.author.voice.channel)
            else:
                await ctx.author.voice.channel.connect()

    async def on_ready(self):
        print("Stefan anmäler sig för tjänstgöring.")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ert skitsnack"))
