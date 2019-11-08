# -*- coding: utf-8 -*-
# Standard Library
import asyncio
import contextlib
import logging

from typing import Optional

# Cog Dependencies
import aiohttp
import lavalink

from lavalink.enums import LoadType
from lavalink.rest_api import LoadResult, Track
from redbot import VersionInfo
from redbot.cogs.audio.audio import __version__ as audio_version
from redbot.core import Config, commands
from redbot.core.bot import Red
from requests.utils import requote_uri

if VersionInfo.from_str(audio_version) >= VersionInfo.from_str("1.0.0"):
    raise RuntimeError(
        "You should use the `audiodb` cog with this audio version but you have `audiodb31`!"
    )

_config_identifier: int = 208903205982044161
log = logging.getLogger("red.audio.cache")


class AudioDBAPI:
    def __init__(self, bot: Red, session: aiohttp.ClientSession):
        self.bot = bot
        self.session = session
        self.api_key = None

    async def _get_api_key(self,) -> Optional[str]:
        global _WRITE_GLOBAL_API_ACCESS
        tokens = await self.bot.db.api_tokens.get_raw("audiodb", default={"api_key": None})
        self.api_key = tokens.get("api_key", None)
        _WRITE_GLOBAL_API_ACCESS = self.api_key is not None
        return self.api_key

    async def post_call(self, track: Track) -> None:
        with contextlib.suppress(Exception):
            token = await self._get_api_key()
            if token is None:
                return None
            if "loadtrack" in track.uri:
                return None
            api_url = requote_uri(f"https://redaudio-db.appspot.com/api/v1/queries")
            llresponse = self.get_load_track(track)
            async with self.session.request(
                "POST",
                api_url,
                json=llresponse._raw,
                headers={"Authorization": token},
                params={"query": requote_uri(track.uri)},
            ) as r:
                await r.read()
                if "x-process-time" in r.headers:
                    log.debug(
                        f"POST || Ping {r.headers['x-process-time']} ||"
                        f" Status code {r.status} || {track.uri}"
                    )

    @staticmethod
    def track_creator(track: Track):
        track_keys = track._info.keys()
        track_values = track._info.values()
        track_id = track.track_identifier
        track_info = {}
        for k, v in zip(track_keys, track_values):
            track_info[k] = v
        keys = ["track", "info"]
        values = [track_id, track_info]
        track_obj = {}
        for key, value in zip(keys, values):
            track_obj[key] = value
        return track_obj

    def get_load_track(self, track: Track):
        load_track = {
            "loadType": LoadType.TRACK_LOADED,
            "playlistInfo": {},
            "tracks": [self.track_creator(track)],
        }

        return LoadResult(load_track)


class AudioDB31(commands.Cog):
    """Drapers AudioDB commands."""

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, _config_identifier, force_registration=True)
        self.session = aiohttp.ClientSession()
        self.AudioDBAPI = AudioDBAPI(self.bot, self.session)
        self._task = self.bot.loop.create_task(self.sync_up())

    def cog_unload(self):
        if self._task:
            self._task.cancel()
        if self.session:
            self.session.close()

    @staticmethod
    async def async_iterate(sequence, sleep=0.001):
        for i in sequence:
            yield i
            await asyncio.sleep(sleep)

    async def sync_up(self):
        await self.bot.wait_until_ready()

        while True:
            for p in lavalink.all_players():
                queue = p.queue or []
                current = p.current
                if current:
                    queue.append(current)
                if not queue:
                    continue
                async for t in self.async_iterate(queue):
                    await self.AudioDBAPI.post_call(t)
            await asyncio.sleep(600)
