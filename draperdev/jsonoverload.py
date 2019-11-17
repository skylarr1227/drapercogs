# -*- coding: utf-8 -*-
# Cog Dependencies
from redbot.core import Config, checks, commands
from redbot.core.bot import Red

_config_identifier: int = 208903205982044161


class DraperDevJson(commands.Cog):
    """Drapers JSON overload commands."""

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, _config_identifier, force_registration=True)

    def cog_unload(self) -> None:
        from draperdev import hackyjson

        hackyjson.restore_stdlib()

    @checks.is_owner()
    @commands.group(name="hackydev")
    async def _hackydev(self, ctx: commands.Context):
        """Change hackydev settings."""

    @_hackydev.command(name="overload")
    async def _hackydev_overload(self, ctx: commands.Context):
        """Overload JSON lib."""
        from draperdev import hackyjson

        hackyjson.overload_stdlib()
        await ctx.tick()

    @_hackydev.command(name="revert")
    async def _hackydev_undo_overload(self, ctx: commands.Context):
        """Revert the JSON lib overload."""
        from draperdev import hackyjson

        hackyjson.restore_stdlib()
        await ctx.tick()
