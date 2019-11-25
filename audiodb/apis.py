# -*- coding: utf-8 -*-
# Standard Library
import asyncio
import contextlib
import datetime
import logging
import time

from typing import Callable, List, Mapping, Optional, Tuple

# Cog Dependencies
import aiohttp
import discord
import lavalink

from aiohttp import ClientTimeout
from lavalink.enums import LoadType
from lavalink.rest_api import LoadResult
from redbot.cogs.audio import audio_dataclasses
from redbot.cogs.audio.apis import HAS_SQL, MusicCache, SQLError
from redbot.cogs.audio.utils import CacheLevel, Notifier, is_allowed, queue_duration, track_limit
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n
from requests.utils import requote_uri

# Cog Imports
from audiodb import json

log = logging.getLogger("red.audio.cache")
_ = Translator("Audio", __file__)

_config: Config = None
_WRITE_GLOBAL_API_ACCESS = None
_QUERY_LAVALINK_TABLE = "SELECT * FROM lavalink;"
_API_URL = "http://api.redbot.app/"


def _pass_config_to_api(config: Config):
    global _config
    if _config is None:
        _config = config


class AudioDBAPI:
    def __init__(self, bot: Red, session: aiohttp.ClientSession):
        self.bot = bot
        self.session = session
        self.api_key = None

    async def _get_api_key(self,) -> Optional[str]:
        global _WRITE_GLOBAL_API_ACCESS
        if self.api_key is None:
            tokens = await self.bot.get_shared_api_tokens("audiodb")
            self.api_key = tokens.get("api_key", None)
        _WRITE_GLOBAL_API_ACCESS = self.api_key is not None
        return self.api_key

    async def get_call(self, query: Optional[audio_dataclasses.Query] = None) -> Optional[dict]:
        with contextlib.suppress(Exception):
            query = audio_dataclasses.Query.process_input(query)
            if any([not query or not query.valid or query.is_spotify or query.is_local]):
                return {}
            await self._get_api_key()
            search_response = "error"
            query = query.lavalink_query
            api_url = f"{_API_URL}api/v1/queries"
            with contextlib.suppress(aiohttp.ContentTypeError, asyncio.TimeoutError):
                async with self.session.request(
                    "GET",
                    api_url,
                    timeout=ClientTimeout(total=await _config.get_timeout()),
                    params={"query": requote_uri(query)},
                ) as r:
                    search_response = await r.json()
                    if "x-process-time" in r.headers:
                        log.debug(
                            f"GET || Ping {r.headers['x-process-time']} || Status code {r.status} || {query}"
                        )
            if "tracks" not in search_response:
                return {}
            return search_response
        return {}

    async def get_spotify(self, title: str, author: Optional[str]) -> Optional[dict]:
        with contextlib.suppress(Exception):
            search_response = "error"
            api_url = f"{_API_URL}api/v1/queries/spotify"
            params = {"title": requote_uri(title), "author": requote_uri(author)}
            await self._get_api_key()
            with contextlib.suppress(aiohttp.ContentTypeError, asyncio.TimeoutError):
                async with self.session.request(
                    "GET",
                    api_url,
                    timeout=ClientTimeout(total=await _config.get_timeout()),
                    params=params,
                ) as r:
                    search_response = await r.json()
                    if "x-process-time" in r.headers:
                        log.debug(
                            f"GET/spotify || Ping {r.headers['x-process-time']} || Status code {r.status} || {title} - {author}"
                        )
            if "tracks" not in search_response:
                return None
            return search_response
        return {}

    async def post_call(
        self, llresponse: LoadResult, query: Optional[audio_dataclasses.Query]
    ) -> None:
        with contextlib.suppress(Exception):
            query = audio_dataclasses.Query.process_input(query)
            if llresponse.has_error or llresponse.load_type.value in ["NO_MATCHES", "LOAD_FAILED"]:
                return

            if query and query.valid and not query.is_local and not query.is_spotify:
                query = query.lavalink_query
            else:
                return None
            token = await self._get_api_key()
            if token is None:
                return None
            api_url = requote_uri(f"{_API_URL}api/v1/queries")
            async with self.session.request(
                "POST",
                api_url,
                json=llresponse._raw,
                headers={"Authorization": token},
                params={"query": requote_uri(query)},
            ) as r:
                await r.read()
                if "x-process-time" in r.headers:
                    log.debug(
                        f"POST || Ping {r.headers['x-process-time']} ||"
                        f" Status code {r.status} || {query}"
                    )


@cog_i18n(_)
class MusicCache(MusicCache):
    """Handles music queries to the Spotify and Youtube Data API.

    Always tries the Cache first.
    """

    def __init__(self, bot: Red, session: aiohttp.ClientSession, path: str):
        super().__init__(bot, session, path)
        self.bot = bot
        self.audio_api: AudioDBAPI = AudioDBAPI(bot, session)

    async def fetch_all_contribute(self) -> List[Mapping]:
        return await self.database.fetch_all(query=_QUERY_LAVALINK_TABLE)

    async def update_global(
        self, llresponse: LoadResult, query: Optional[audio_dataclasses.Query] = None
    ):
        await self.audio_api.post_call(llresponse=llresponse, query=query)

    async def lavalink_query(
        self,
        ctx: commands.Context,
        player: lavalink.Player,
        query: audio_dataclasses.Query,
        forced: bool = False,
        lazy: bool = False,
        should_query_global: bool = True,
    ) -> Tuple[LoadResult, bool]:
        """A replacement for :code:`lavalink.Player.load_tracks`. This will try to get a valid
        cached entry first if not found or if in valid it will then call the lavalink API.

        Parameters
        ----------
        ctx: commands.Context
            The context this method is being called under.
        player : lavalink.Player
            The player who's requesting the query.
        query: audio_dataclasses.Query
            The Query object for the query in question.
        forced:bool
            Whether or not to skip cache and call API first..
        lazy:bool
            If set to True, it will not call the api if a track is not found.
        Returns
        -------
        Tuple[lavalink.LoadResult, bool]
            Tuple with the Load result and whether or not the API was called.
        """
        await self.audio_api._get_api_key()
        current_cache_level = (
            CacheLevel(await self.config.cache_level()) if HAS_SQL else CacheLevel.none()
        )
        cache_enabled = CacheLevel.set_lavalink().is_subset(current_cache_level)
        val = None
        _raw_query = audio_dataclasses.Query.process_input(query)
        query = str(_raw_query)
        valid_global_entry = True
        results = None
        time.time()
        globaldb_toggle = await _config.enabled()

        if cache_enabled and not forced and not _raw_query.is_local:
            update = True
            with contextlib.suppress(SQLError):
                val, update = await self.fetch_one("lavalink", "data", {"query": query})
            if update:
                val = None
            if val:
                local_task = ("update", ("lavalink", {"query": query}))
                self.append_task(ctx, *local_task)
                valid_global_entry = False
        if (
            globaldb_toggle
            and not val
            and should_query_global
            and not forced
            and not _raw_query.is_local
            and not _raw_query.is_spotify
        ):
            valid_global_entry = False
            with contextlib.suppress(Exception):
                global_entry = await self.audio_api.get_call(query=_raw_query)
                results = LoadResult(global_entry)
                if results.load_type in [
                    LoadType.PLAYLIST_LOADED,
                    LoadType.TRACK_LOADED,
                    LoadType.SEARCH_RESULT,
                    LoadType.V2_COMPAT,
                ]:
                    valid_global_entry = True
                if valid_global_entry:
                    return results, False

        if lazy is True:
            called_api = False
        elif val and not forced:
            data = json.loads(val)
            data["query"] = query
            results = LoadResult(data)
            called_api = False
            if results.has_error:
                # If cached value has an invalid entry make a new call so that it gets updated
                results, called_api = await self.lavalink_query(
                    ctx, player, _raw_query, forced=True
                )
            valid_global_entry = False
        else:
            called_api = True
            results = None
            try:
                results = await player.load_tracks(query)
            except KeyError:
                results = None
            if results is None:
                results = LoadResult({"loadType": "LOAD_FAILED", "playlistInfo": {}, "tracks": []})
            valid_global_entry = False
        update_global = globaldb_toggle and not valid_global_entry and _WRITE_GLOBAL_API_ACCESS
        with contextlib.suppress(Exception):
            if (
                update_global
                and not _raw_query.is_local
                and not results.has_error
                and len(results.tracks) >= 1
            ):
                global_task = ("global", dict(llresponse=results, query=_raw_query))
                self.append_task(ctx, *global_task)
        if (
            cache_enabled
            and results.load_type
            and not results.has_error
            and not _raw_query.is_local
            and results.tracks
        ):
            with contextlib.suppress(SQLError):
                time_now = str(datetime.datetime.now(datetime.timezone.utc))
                local_task = (
                    "insert",
                    (
                        "lavalink",
                        [
                            {
                                "query": query,
                                "data": json.dumps(results._raw),
                                "last_updated": time_now,
                                "last_fetched": time_now,
                            }
                        ],
                    ),
                )
                self.append_task(ctx, *local_task)
        return results, called_api

    async def run_tasks(self, ctx: Optional[commands.Context] = None, _id=None):
        lock_id = _id or ctx.message.id
        lock_author = ctx.author if ctx else None
        async with self._lock:
            if lock_id in self._tasks:
                log.debug(f"Running database writes for {lock_id} ({lock_author})")
                with contextlib.suppress(Exception):
                    tasks = self._tasks[ctx.message.id]
                    del self._tasks[ctx.message.id]
                    await asyncio.gather(
                        *[asyncio.ensure_future(self.insert(*a)) for a in tasks["insert"]],
                        loop=self.bot.loop,
                        return_exceptions=True,
                    )
                    await asyncio.gather(
                        *[asyncio.ensure_future(self.update(*a)) for a in tasks["update"]],
                        loop=self.bot.loop,
                        return_exceptions=True,
                    )
                    await asyncio.gather(
                        *[asyncio.ensure_future(self.update_global(**a)) for a in tasks["global"]],
                        loop=self.bot.loop,
                        return_exceptions=True,
                    )
            log.debug(f"Completed database writes for {lock_id} " f"({lock_author})")

    async def run_all_pending_tasks(self):
        async with self._lock:
            log.debug("Running pending writes to database")
            with contextlib.suppress(Exception):
                tasks = {"update": [], "insert": [], "global": []}
                for k, task in self._tasks.items():
                    for t, args in task.items():
                        tasks[t].append(args)
                self._tasks = {}

                await asyncio.gather(
                    *[asyncio.ensure_future(self.insert(*a)) for a in tasks["insert"]],
                    loop=self.bot.loop,
                    return_exceptions=True,
                )
                await asyncio.gather(
                    *[asyncio.ensure_future(self.update(*a)) for a in tasks["update"]],
                    loop=self.bot.loop,
                    return_exceptions=True,
                )
                await asyncio.gather(
                    *[asyncio.ensure_future(self.update_global(**a)) for a in tasks["global"]],
                    loop=self.bot.loop,
                    return_exceptions=True,
                )
        log.debug("Completed pending writes to database have finished")

    def append_task(self, ctx: commands.Context, event: str, task: tuple, _id=None):
        lock_id = _id or ctx.message.id
        if lock_id not in self._tasks:
            self._tasks[lock_id] = {"update": [], "insert": [], "global": []}
        self._tasks[lock_id][event].append(task)

    async def spotify_enqueue(
        self,
        ctx: commands.Context,
        query_type: str,
        uri: str,
        enqueue: bool,
        player: lavalink.Player,
        lock: Callable,
        notifier: Optional[Notifier] = None,
        query_global=True,
    ) -> List[lavalink.Track]:
        track_list = []
        has_not_allowed = False
        await self.audio_api._get_api_key()
        try:
            current_cache_level = (
                CacheLevel(await self.config.cache_level()) if HAS_SQL else CacheLevel.none()
            )
            guild_data = await self.config.guild(ctx.guild).all()

            # now = int(time.time())
            enqueued_tracks = 0
            consecutive_fails = 0
            queue_dur = await queue_duration(ctx)
            queue_total_duration = lavalink.utils.format_time(queue_dur)
            before_queue_length = len(player.queue)
            tracks_from_spotify = await self._spotify_fetch_tracks(
                query_type, uri, params=None, notifier=notifier
            )
            globaldb_toggle = await _config.enabled()
            total_tracks = len(tracks_from_spotify)
            if total_tracks < 1:
                lock(ctx, False)
                embed3 = discord.Embed(
                    colour=await ctx.embed_colour(),
                    title=_("This doesn't seem to be a supported Spotify URL or code."),
                )
                await notifier.update_embed(embed3)

                return track_list
            database_entries = []
            time_now = str(datetime.datetime.now(datetime.timezone.utc))

            youtube_cache = CacheLevel.set_youtube().is_subset(current_cache_level)
            spotify_cache = CacheLevel.set_spotify().is_subset(current_cache_level)
            for track_count, track in enumerate(tracks_from_spotify):
                (
                    song_url,
                    track_info,
                    uri,
                    artist_name,
                    track_name,
                    _id,
                    _type,
                ) = self._get_spotify_track_info(track)

                database_entries.append(
                    {
                        "id": _id,
                        "type": _type,
                        "uri": uri,
                        "track_name": track_name,
                        "artist_name": artist_name,
                        "song_url": song_url,
                        "track_info": track_info,
                        "last_updated": time_now,
                        "last_fetched": time_now,
                    }
                )

                val = None
                llresponse = None
                if youtube_cache:
                    update = True
                    with contextlib.suppress(SQLError):
                        val, update = await self.fetch_one(
                            "youtube", "youtube_url", {"track": track_info}
                        )
                    if update:
                        val = None
                should_query_global = (
                    globaldb_toggle and not update and query_global and val is None
                )
                if should_query_global:
                    llresponse = await self.audio_api.get_spotify(track_name, artist_name)
                    if llresponse:
                        llresponse = LoadResult(llresponse)
                    val = llresponse or None

                if val is None:
                    val = await self._youtube_first_time_query(
                        ctx, track_info, current_cache_level=current_cache_level
                    )
                if youtube_cache and val and llresponse is None:
                    task = ("update", ("youtube", {"track": track_info}))
                    self.append_task(ctx, *task)

                if llresponse:
                    track_object = llresponse.tracks
                elif val:
                    try:
                        result, called_api = await self.lavalink_query(
                            ctx,
                            player,
                            audio_dataclasses.Query.process_input(val),
                            should_query_global=not should_query_global,
                        )
                    except (RuntimeError, aiohttp.ServerDisconnectedError):
                        lock(ctx, False)
                        error_embed = discord.Embed(
                            colour=await ctx.embed_colour(),
                            title=_("The connection was reset while loading the playlist."),
                        )
                        await notifier.update_embed(error_embed)
                        break
                    except asyncio.TimeoutError:
                        lock(ctx, False)
                        error_embed = discord.Embed(
                            colour=await ctx.embed_colour(),
                            title=_("Player timeout, skipping remaining tracks."),
                        )
                        await notifier.update_embed(error_embed)
                        break
                    track_object = result.tracks
                else:
                    track_object = []
                if (track_count % 2 == 0) or (track_count == total_tracks):
                    key = "lavalink"
                    seconds = "???"
                    second_key = None
                    await notifier.notify_user(
                        current=track_count,
                        total=total_tracks,
                        key=key,
                        seconds_key=second_key,
                        seconds=seconds,
                    )

                if consecutive_fails >= 10:
                    error_embed = discord.Embed(
                        colour=await ctx.embed_colour(),
                        title=_("Failing to get tracks, skipping remaining."),
                    )
                    await notifier.update_embed(error_embed)
                    break
                if not track_object:
                    consecutive_fails += 1
                    continue
                consecutive_fails = 0
                single_track = track_object[0]
                if not await is_allowed(
                    ctx.guild,
                    (
                        f"{single_track.title} {single_track.author} {single_track.uri} "
                        f"{str(audio_dataclasses.Query.process_input(single_track))}"
                    ),
                ):
                    has_not_allowed = True
                    log.debug(f"Query is not allowed in {ctx.guild} ({ctx.guild.id})")
                    continue
                track_list.append(single_track)
                if enqueue:
                    if guild_data["maxlength"] > 0:
                        if track_limit(single_track, guild_data["maxlength"]):
                            enqueued_tracks += 1
                            player.add(ctx.author, single_track)
                            self.bot.dispatch(
                                "red_audio_track_enqueue",
                                player.channel.guild,
                                single_track,
                                ctx.author,
                            )
                    else:
                        enqueued_tracks += 1
                        player.add(ctx.author, single_track)
                        self.bot.dispatch(
                            "red_audio_track_enqueue",
                            player.channel.guild,
                            single_track,
                            ctx.author,
                        )

                    if not player.current:
                        await player.play()
            if len(track_list) == 0:
                if not has_not_allowed:
                    embed3 = discord.Embed(
                        colour=await ctx.embed_colour(),
                        title=_(
                            "Nothing found.\nThe YouTube API key may be invalid "
                            "or you may be rate limited on YouTube's search service.\n"
                            "Check the YouTube API key again and follow the instructions "
                            "at `{prefix}audioset youtubeapi`."
                        ).format(prefix=ctx.prefix),
                    )
                    await ctx.send(embed=embed3)
            player.maybe_shuffle()
            if enqueue and tracks_from_spotify:
                if total_tracks > enqueued_tracks:
                    maxlength_msg = " {bad_tracks} tracks cannot be queued.".format(
                        bad_tracks=(total_tracks - enqueued_tracks)
                    )
                else:
                    maxlength_msg = ""

                embed = discord.Embed(
                    colour=await ctx.embed_colour(),
                    title=_("Playlist Enqueued"),
                    description=_("Added {num} tracks to the queue.{maxlength_msg}").format(
                        num=enqueued_tracks, maxlength_msg=maxlength_msg
                    ),
                )
                if not guild_data["shuffle"] and queue_dur > 0:
                    embed.set_footer(
                        text=_(
                            "{time} until start of playlist"
                            " playback: starts at #{position} in queue"
                        ).format(time=queue_total_duration, position=before_queue_length + 1)
                    )

                await notifier.update_embed(embed)
            lock(ctx, False)

            if spotify_cache:
                task = ("insert", ("spotify", database_entries))
                self.append_task(ctx, *task)
        except Exception as e:
            lock(ctx, False)
            raise e
        finally:
            lock(ctx, False)
        return track_list

    async def _api_nuker(self, ctx: commands.Context, db_entries) -> None:
        tasks = []
        for i, entry in enumerate(db_entries, start=1):
            query = entry.query
            data = entry.data
            _raw_query = audio_dataclasses.Query.process_input(query)
            results = LoadResult(json.loads(data))
            with contextlib.suppress(Exception):
                if not _raw_query.is_local and not results.has_error and len(results.tracks) >= 1:
                    global_task = dict(llresponse=results, query=_raw_query)
                    tasks.append(global_task)
                if i % 20000 == 0:
                    log.debug("Running pending writes to database")
                    await asyncio.gather(
                        *[asyncio.ensure_future(self.update_global(**a)) for a in tasks],
                        loop=self.bot.loop,
                        return_exceptions=True,
                    )
                    tasks = []
                    log.debug("Pending writes to database have finished")
            if i % 20000 == 0:
                await ctx.send(f"20k-sleeping")
                await asyncio.sleep(5)

        await ctx.send(f"20k-Local Audio cache sent upstream, thanks for contributing")
