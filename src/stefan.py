import discord
from difflib import SequenceMatcher
from discord.ext import commands

from log import get_logger

from config import config
from cogs import Music, Misc

logger = get_logger(__name__)

class Stefan(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        commands.Bot.__init__(self, *args, **kwargs)

        self.latest_context = None
        
        self.before_invoke(self._handle_before_invoke)
        self.after_invoke(self._handle_after_invoke)

    async def _handle_before_invoke(self, ctx):
        command = f"Command: _{ctx.command}"
        args = ', '.join(['self', 'ctx'] + [f"'{arg}'" for arg in ctx.args[2:]])
        logger.debug(f"{command}({args}) [source: '{ctx.message.content}']")
        
        self.latest_context = ctx
        await ctx.message.add_reaction("👌")

    async def setup_hook(self):
        await self.add_cog(Music(self, config))
        await self.add_cog(Misc(self, config))
    
    async def _handle_after_invoke(self, ctx):
        await ctx.message.remove_reaction("👌", self.user)
        await ctx.message.add_reaction("👍")

    async def close(self):
        for cog in self.cogs.values():
            await cog.close()

        if self.latest_context:
            await self.latest_context.send("Jag dör! 😱")

            if self.latest_context.guild.voice_client:
                await self.latest_context.guild.voice_client.disconnect()

        return await super().close()

    def get_voice_client(self, ctx):
        """
        Return the bots voice client. May return None.
        """
        return discord.utils.get(self.voice_clients, guild=ctx.guild)

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

    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            await self.handle_user_switched_channel(member, before, after)

    async def handle_user_switched_channel(self, member, before, after):
        """
        Disconnect bot if it is left alone in a channel.
        """
        bot_voice_client = discord.utils.get(self.voice_clients, guild=member.guild)
        if bot_voice_client and len(bot_voice_client.channel.voice_states.keys()) == 1:
            await self.stefan_disconnect(bot_voice_client)

    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.CommandNotFound):
            commands = []
            ratios = []
            invokes = []
            
            for cog in self.cogs.values():
                for command in cog.get_commands():
                    commands.append(command)

                    max_ratio = SequenceMatcher(None, ctx.invoked_with, command.name).ratio()
                    invoke = command.name

                    for alias in command.aliases:
                        ratio = SequenceMatcher(None, ctx.invoked_with, alias).ratio()
                        if ratio > max_ratio:
                            max_ratio = ratio
                            invoke = alias
                    
                    ratios.append(max_ratio)
                    invokes.append(invoke)

            max_index = 0
            current_index = 0
            max_ratio = 0

            for ratio in ratios:
                if ratio > max_ratio:
                    max_ratio = ratio
                    max_index = current_index
                current_index += 1

            if max_ratio > 0.3:
                args = ctx.message.content.split()[1:]

                await ctx.send(f"Jag antar att du ville skriva {invokes[max_index]}? 🤔")
                ctx.args = [commands[max_index], ctx, *args]
                ctx.invoked_with = commands[max_index].name
                ctx.command = commands[max_index].name
                await self._handle_before_invoke(ctx)
                await commands[max_index].__call__(ctx, *args)
                await self._handle_after_invoke(ctx)
            else:
                await ctx.send("Njae, nu har du nog skrivit något tokigt... 🤔")
        else:
            raise error    

    # ============================
    # ===== Stefan functions =====
    # ============================

    async def stefan_disconnect(self, voice_client):
        """
        Disconnect voice_client and notify all cogs that are interested.
        """
        await voice_client.disconnect()

        # Notify every cog that might be interested that the bot has
        # disconnected
        for cog in self.cogs.values():
            if hasattr(cog, 'stefan_on_disconnect') and callable(cog.stefan_on_disconnect):
                cog.stefan_on_disconnect()
