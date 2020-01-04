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
        if old_audio_cache is None and enabled is True:
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
