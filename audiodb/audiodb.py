# -*- coding: utf-8 -*-
# Standard Library
import contextlib
from typing import Union

# Cog Dependencies
from redbot import VersionInfo
from redbot.cogs.audio import Audio
from redbot.cogs.audio.audio import __version__ as audio_version

if VersionInfo.from_str(audio_version) < VersionInfo.from_str("1.0.0"):
    raise RuntimeError("Your Audio cog version does not support this plugin!")

from redbot.cogs.audio.apis import MusicCache as DefaultMusicCache  # isort:skip
from redbot.core import Config, checks, commands  # isort:skip
from redbot.core.bot import Red  # isort:skip
from redbot.core.data_manager import cog_data_path  # isort:skip
from redbot.core.utils.menus import start_adding_reactions  # isort:skip
from redbot.core.utils.predicates import ReactionPredicate  # isort:skip

from .apis import MusicCache, _pass_config_to_api  # isort:skip

old_audio_cache: DefaultMusicCache = None

_config_identifier: int = 208903205982044161


class AudioDB(commands.Cog):
    """Drapers AudioDB commands."""
    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, _config_identifier, force_registration=True)
        self.config.register_global(enabled=True, get_timeout=1)

    async def initialize(self, audio: Audio, enabled=True) -> None:
        _pass_config_to_api(self.config)
        global old_audio_cache
        if old_audio_cache is None:
            old_audio_cache = audio.music_cache

        if enabled is True:
            audio.music_cache = MusicCache(
                audio.bot, audio.session, path=str(cog_data_path(raw_name="Audio"))
            )
            await audio.music_cache.initialize(audio.config)
        elif enabled is False:
            audio.music_cache = old_audio_cache

    def cog_unload(self) -> None:
        audio = self.bot.get_cog("Audio")
        if audio is not None and old_audio_cache is not None:
            audio.music_cache = old_audio_cache

    @commands.Cog.listener()
    async def on_red_audio_initialized(self, audio: Audio):
        state = await self.config.enabled()
        await self.initialize(audio, enabled=state)

    @commands.Cog.listener()
    async def on_red_audio_unload(self, audio: Audio):
        with contextlib.suppress(Exception):
            await self.initialize(audio, enabled=False)

    @checks.is_owner()
    @commands.group(name="audiodb")
    async def _audiodb(self, ctx: commands.Context):
        """Change audiodb settings."""

    @_audiodb.command(name="toggle")
    async def _audiodb_toggle(self, ctx: commands.Context):
        """Toggle the server settings.

        Default is ON
        """
        audio = self.bot.get_cog("Audio")
        state = await self.config.enabled()
        await self.config.enabled.set(not state)
        await self.initialize(audio, enabled=not state)

        await ctx.send(f"Global DB is {'enabled' if not state else 'disabled'}")

    @_audiodb.command(name="timeout")
    async def _audiodb_timeout(self, ctx: commands.Context, timeout: Union[float, int]):
        """Set GET request timeout.

        Example: 0.1 = 100ms 1 = 1 second
        """

        await self.config.get_timeout.set(timeout)

        await ctx.send(f"Request timeout set to {timeout} second(s)")

    @_audiodb.command(name="contribute")
    async def contribute(self, ctx: commands.Context):
        """Send your local DB upstream."""
        tokens = await self.bot.get_shared_api_tokens("audiodb")
        api_key = tokens.get("api_key", None)
        if api_key is None:
            return await ctx.send(
                f"Hey! Thanks for showing interest into contributing, "
                f"currently you dont have access to this, "
                f"if you wish to contribute please DM Draper#6666"
            )
        audio = self.bot.get_cog("Audio")
        db_entries = await audio.music_cache.fetch_all_contribute()
        info = await ctx.send(
            f"Sending {len(db_entries)} entries to the global DB. "
            f"are you sure about this (It may take a very long time...)?"
        )
        start_adding_reactions(info, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(info, ctx.author)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if not pred.result:
            return await ctx.send(f"Cancelled!")

        await audio.music_cache._api_nuker(ctx, db_entries)
