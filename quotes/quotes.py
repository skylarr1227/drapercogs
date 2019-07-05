# -*- coding: utf-8 -*-
import asyncio
import contextlib
import logging
import random
from collections import OrderedDict
from datetime import datetime
from typing import Optional
from itertools import islice

import discord
from discord.ext.commands.converter import Greedy

from redbot.core.utils.chat_formatting import humanize_list, bold
from redbot.core import Config, commands, checks

try:
    import regex
except Exception as e:
    raise RuntimeError(f"Can't load regex: {e}\nDo 'python -m pip install regex'.")

logger = logging.getLogger("red.cogs.quotes")

_default_guild = dict(
    enabled=False, quotesToKeep=100, crossChannel=False, perma=5, botPrefixes=[], channels={}
)
_default_channel = dict(quotes={}, permaQuotes={})

_ = lambda s: s

urlmatcher_re = regex.compile(
    r"((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]+(:[0-9]+)"
    r"?|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)"
    r"((?:\/[\+~%\/.\w-_]*)?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)",
    regex.IGNORECASE,
)
quote_cleaner_re = regex.compile(
    r"^(<+[\p{P}\p{Sm}\p{Sc}\p{Sk}\p{So}\p{M}\p{Z}\p{N}]*>+)*$|^(:+[\p{P}\p{Sm}\p{"
    r"Sc}\p{Sk}\p{So}\p{M}\p{Z}\p{N}\p{L}]*:+)*$|^([:<]+[\p{L}\p{N}\p{P}]+[:>]+)+$",
    regex.IGNORECASE | regex.MULTILINE,
)


class Quotes(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8475527184, force_registration=True)
        self.config.register_guild(**_default_guild)
        self.config.register_channel(**_default_channel)
        self.task = self.bot.loop.create_task(self.quote_cleaner())

    def cog_unload(self):
        if self.task:
            self.task.cancel()

    @commands.guild_only()
    @checks.mod_or_permissions(manage_guild=True)
    @commands.group(name="quoteset", autohelp=True)
    async def quoteset(self, ctx: commands.Context):
        """Commands to configure quote settings"""

    @checks.admin_or_permissions(manage_guild=True)
    @quoteset.command(name="toggle")
    async def quoteset_toggle(self, ctx: commands.Context, enabled: bool = None):
        """Toggles Quotes in the server"""
        guild = ctx.guild
        if enabled is None:
            enabled = not await self.config.guild(guild).enabled()
        await self.config.guild(guild).enabled.set(enabled)
        message = _("Quotes has been {}").format(_("enabled") if enabled else _("disabled"))
        await ctx.maybe_send_embed(message)

    @checks.admin_or_permissions(manage_guild=True)
    @quoteset.command(name="channel", autohelp=True)
    async def quoteset_channel(self, ctx: commands.Context, channels: Greedy[discord.TextChannel]):
        """Stop/Start listening to channels"""
        channels = list(set(channels))
        guild = ctx.guild
        channels_to_add = []
        channels_to_remove = []
        message1 = ""
        message2 = ""
        channel_group = self.config.guild(guild).channels
        async with channel_group.channels() as channel_data:
            for channel in channels:
                chan_id = f"{channel.id}"
                if chan_id in channel_data:
                    channels_to_remove.append(channel)
                    channel_data.pop(chan_id, None)
                else:
                    channels_to_add.append(channel)
                    channel_data.update({channel.id: channel.name})
        channels_to_add = [c.mention for c in channels_to_add]
        channels_to_remove = [c.mention for c in channels_to_remove]
        if channels_to_add:
            channels_to_add = humanize_list(channels_to_add)
            message1 = _("I will now monitor the following channels:\n{}").format(channels_to_add)
        if channels_to_remove:
            channels_to_remove = humanize_list(channels_to_remove)
            message2 = _("I will stop monitoring the following channels:\n{}").format(
                channels_to_remove
            )
        for m in [message1, message2]:
            if m:
                await ctx.maybe_send_embed(m)

    @checks.admin_or_permissions(manage_guild=True)
    @quoteset.command(name="limit")
    async def quoteset_limit(self, ctx: commands.Context, limit: int = 100):
        """Set how many quotes to keep
        Note this value is per room
        """
        guild = ctx.message.guild
        await self.config.guild(guild).quotesToKeep.set(limit)
        message = _("Quote limit set to {}").format(limit)
        await ctx.maybe_send_embed(message)

    @checks.admin_or_permissions(manage_guild=True)
    @quoteset.command(name="crosschannel")
    async def quoteset_crosschannel(self, ctx: commands.context, enabled: bool = None):
        """Toggle sticky quotes to show in all rooms"""
        guild = ctx.guild
        if enabled is None:
            enabled = not await self.config.guild(guild).crossChannel()
        await self.config.guild(guild).crossChannel.set(enabled)
        message = _("Sticky Quotes will show {}").format(
            _("in all rooms") if enabled else _("only in the same room as original message")
        )
        await ctx.maybe_send_embed(message)

    @checks.admin_or_permissions(manage_guild=True)
    @quoteset.command(name="ignore")
    async def quoteset_ignores(self, ctx: commands.Context, *to_ignore):
        """Sets a list of words a message starts with
        These will never be added to the quote list"""
        guild = ctx.message.guild
        await self.config.guild(guild).botPrefixes.set(to_ignore)
        to_ignore = humanize_list(to_ignore)
        message = _("All messages starting with the following will be ignored :\n{}").format(
            to_ignore
        )
        await ctx.maybe_send_embed(message)

    @checks.guildowner_or_permissions(administrator=True)
    @quoteset.command(name="wipe")
    async def quote_clean(self, ctx: commands.Context):
        """Wipe quote data for all channels in server
        This does not include Sticky Quotes
        """
        channels = ctx.guild.text_channels
        for channel in channels:
            if channel.name not in list((await self.config.guild(ctx.guild).channels()).values()):
                continue
            await self.config.channel(channel).quotes.clear()
            await ctx.maybe_send_embed(
                _("Quotes for {channel.mention} has been reset").format(channel=channel)
            )

    @quoteset.command(name="perma")
    async def quoteset_permaquote(
        self, ctx: commands.Context, message_id: int, channel: Optional[discord.TextChannel] = None
    ):
        """Pin a Quote to always be in the pool"""
        if not channel:
            channel = ctx.message.channel

        if channel.name not in list((await self.config.guild(ctx.guild).channels()).values()):
            return await ctx.maybe_send_embed(
                _("{channel.mention} isn't a whitelisted channel").format(channel=channel)
            )

        try:
            permaquote = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.maybe_send_embed(
                _("Message: {message} couldn't be found in {channel.mention}").format(
                    channel=channel, message=message_id
                )
            )

        if permaquote:
            content = permaquote.clean_content
            if regex.search(urlmatcher_re, content, concurrent=True):
                return await ctx.maybe_send_embed(
                    _("Messages with URL are not allowed to be quoted").format(
                        channel=channel, message=message_id
                    )
                )
            else:
                data = dict()
                data["avatar_url"] = str(
                    permaquote.author.avatar_url or permaquote.author.default_avatar_url
                )
                data["username"] = permaquote.author.display_name
                data["author"] = permaquote.author.id
                data["message"] = permaquote.content
                data["time_sent"] = permaquote.created_at.timestamp()
                data["jump_url"] = permaquote.jump_url
                new = {permaquote.id: data}

                channel_group = self.config.channel(channel)
                async with channel_group.permaQuotes() as permaQuotes:
                    permaQuotes.update(new)

                return await ctx.maybe_send_embed(
                    _(
                        "I've added [Message]({permaquote.jump_url}) from {"
                        "permaquote.author} to the sticky quotes of {channel.mention}"
                    ).format(permaquote=permaquote, channel=channel)
                )

    @commands.guild_only()
    @commands.command(name="quote", aliases=["q"])
    async def random_quotes(self, ctx: commands.Context):
        """Gets a random quote from this room"""
        member_ids = [m.id for m in ctx.guild.members if m and m.bot is False]
        supported_channels = await self.config.guild(ctx.guild).channels()
        quotes = await self.config.channel(ctx.message.channel).quotes()
        if await self.config.guild(ctx.guild).crossChannel():
            all_channels = await self.config.all_channels()
            all_perma_quotes = [
                v.get("permaQuotes", {})
                for k, v in all_channels.items()
                if f"{k}" in supported_channels
            ]
            permaquotes = {k: v for channel in all_perma_quotes for k, v in channel.items()}
        else:
            permaquotes = await self.config.channel(ctx.message.channel).permaQuotes()

        perma_multiplier = await self.config.guild(ctx.guild).perma()
        quotes = list(quotes.values())
        permaquotes = list(permaquotes.values()) * perma_multiplier
        quotes.extend(permaquotes)
        quotes = [q for q in quotes if q.get("author") in member_ids]
        if quotes:
            quote = random.choice(quotes)
            author = ctx.guild.get_member(quote.get("author", None))
            if author is None:
                author = quote["username"]
                avatar = quote["avatar_url"]
            else:
                avatar = author.avatar_url or author.default_avatar_url
                author = author.display_name
            if await ctx.embed_requested():
                embed = discord.Embed()
                embed.description = quote["message"]
                embed.set_author(name=author, icon_url=avatar)
                embed.set_thumbnail(url=avatar)
                embed.timestamp = datetime.fromtimestamp(quote["time_sent"])
                embed.add_field(
                    name="\u200b", value=f"[{_('Original Message')}]({quote['jump_url']})"
                )
                embed.colour = ctx.author.colour
                return await ctx.send(embed=embed)
            else:
                msg = f"{bold(_('Author'))}: {author}\n\n"
                msg += f"{quote['message'][:1800]}\n\n"
                msg += f"[{_('Original Message')}]({quote['jump_url']})"
                return await ctx.maybe_send_embed(msg)
        else:
            return await ctx.maybe_send_embed(
                _("No quotes available at the moment try again later")
            )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if isinstance(channel, discord.TextChannel):
            await self.config.channel(channel).clear()

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if (
            message.guild
            and not message.author.bot
            and await self.config.guild(message.guild).enabled()
            and f"{message.channel.id}" in (await self.config.guild(message.guild).channels())
        ):
            content = message.clean_content
            if not (
                not content
                or len(content) < 6
                or regex.search(urlmatcher_re, content, concurrent=True)
                or regex.search(quote_cleaner_re, message.content, concurrent=True)
                or any(
                    [
                        message.content.startswith(prefix)
                        for prefix in await self.config.guild(message.guild).botPrefixes()
                    ]
                )
            ):
                data = dict()
                data["avatar_url"] = str(
                    message.author.avatar_url or message.author.default_avatar_url
                )
                data["username"] = message.author.display_name
                data["author"] = message.author.id
                data["message"] = message.content
                data["time_sent"] = message.created_at.timestamp()
                data["jump_url"] = message.jump_url
                new = {message.id: data}
                channel_group = self.config.channel(message.channel)
                async with channel_group.quotes() as quotes:
                    quotes.update(new)

    async def quote_cleaner(self):
        try:
            with contextlib.suppress(asyncio.CancelledError):
                await self.bot.wait_until_ready()
                guilds = self.bot.guilds
                timer = 84600
                while guilds and True:
                    guilds = self.bot.guilds
                    for guild in guilds:
                        channels = guild.text_channels
                        member_ids = [m.id for m in guild.members if m and m.bot is False]
                        whitelisted_channels = list(
                            (await self.config.guild(guild).channels()).values()
                        )
                        difference = await self.config.guild(guild).quotesToKeep()
                        for channel in channels:
                            await asyncio.sleep(0.2)
                            if channel.name not in whitelisted_channels:
                                continue
                            quotes = await self.config.channel(channel).quotes()
                            quotes = {
                                k: v for k, v in quotes.items() if v.get("author") in member_ids
                            }
                            quote_count = len(quotes)
                            if quote_count > difference:
                                sorted_quotes = OrderedDict(
                                    sorted(quotes.items(), key=lambda x: x[1]["time_sent"])
                                )
                                sliced = islice(sorted_quotes.items(), difference)
                                new_quotes = OrderedDict(sliced)
                                await self.config.channel(channel).quotes.set(new_quotes)
                    await asyncio.sleep(timer)
        except Exception as e:
            logger.exception(f"{e}", exc_info=e)
