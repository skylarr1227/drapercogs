# -*- coding: utf-8 -*-
"""
Created on Mar 26, 2019

@author: Guy Reis
"""
from copy import copy
from operator import itemgetter, attrgetter
from typing import List

import discord

from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu


def _(s):
    return s


class MemberStatus(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.config = Config.get_conf(self, identifier=3584065639, force_registration=True)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def playing(self, ctx: commands.Context, *, game: str = None):
        """Shows who's playing what games"""

        global _
        game_name = _("what")
        ending = _(" any games")
        game_list = []
        if game:
            game_name = game
            game_list = [game]
        playing_data = await self.get_players_per_activity(ctx=ctx, game_name=game_list)

        if playing_data:
            embed_list = []
            count = -1
            splitter = 1
            for key, value in sorted(playing_data.items()):
                count += 1
                if count % splitter == 0:
                    embed = discord.Embed(
                        title=_("Who's playing {}?").format(game_name), colour=ctx.embed_color()
                    )

                title = f"{key} ({len(value)} {_('playing')})"
                content = ""
                for _, display_name, _ in sorted(value, key=itemgetter(2, 1)):
                    content += f"{display_name}\n"

                outputs = pagify(content, page_length=1000, priority=True)
                for enum_count, field in enumerate(outputs, 1):
                    if enum_count > 1:
                        title = f"{key} ({_('Part')} {enum_count})"
                    embed.add_field(name=f"{title}", value=field)
                if count % splitter == 0:
                    embed_list.append(copy(embed))

            await menu(
                ctx, pages=embed_list, controls=DEFAULT_CONTROLS, message=None, page=0, timeout=60
            )
        else:
            await ctx.maybe_send_embed(_("No one is playing{ending}").format(ending=ending))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def watching(self, ctx: commands.Context):
        """Shows who's watching what"""

        global _
        watching_data = await self.get_players_per_activity(ctx=ctx, movie=True)

        if watching_data:
            embed_list = []
            count = -1
            splitter = 1
            for key, value in sorted(watching_data.items()):
                count += 1
                if count % splitter == 0:
                    embed = discord.Embed(
                        title=_("Who's watching what?"), colour=ctx.embed_color()
                    )

                title = f"{key} ({len(value)} {_('watching')})"
                content = ""
                for _, display_name, _ in sorted(value, key=itemgetter(2, 1)):
                    content += f"{display_name}\n"

                outputs = pagify(content, page_length=1000, priority=True)
                for enum_count, field in enumerate(outputs, 1):
                    if enum_count > 1:
                        title = f"{key} ({_('Part')} {enum_count})"
                    embed.add_field(name=f"{title}", value=field)
                if count % splitter == 0:
                    embed_list.append(copy(embed))

            await menu(
                ctx, pages=embed_list, controls=DEFAULT_CONTROLS, message=None, page=0, timeout=60
            )
        else:
            await ctx.maybe_send_embed(_("No one is Watching anything"))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def listening(self, ctx: commands.Context):
        """Shows who's listening what"""

        global _
        listening_data = await self.get_players_per_activity(ctx=ctx, music=True)

        if listening_data:
            embed_list = []
            count = -1
            splitter = 1
            for key, value in sorted(listening_data.items()):
                count += 1
                if count % splitter == 0:
                    embed = discord.Embed(
                        title=_("Who's listening to what?"), colour=ctx.embed_color()
                    )

                title = f"{key} ({len(value)} {_('listening')})"
                content = ""
                for _, display_name, _ in sorted(value, key=itemgetter(2, 1)):
                    content += f"{display_name}\n"

                outputs = pagify(content, page_length=1000, priority=True)
                for enum_count, field in enumerate(outputs, 1):
                    if enum_count > 1:
                        title = f"{key} ({_('Part')} {enum_count})"
                    embed.add_field(name=f"{title}", value=field)
                if count % splitter == 0:
                    embed_list.append(copy(embed))

            await menu(
                ctx, pages=embed_list, controls=DEFAULT_CONTROLS, message=None, page=0, timeout=60
            )

        else:
            await ctx.maybe_send_embed(_("No one is listening to anything"))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def streaming(self, ctx: commands.Context, *, game=None):
        """Shows who's streaming what games"""
        global _
        game_name = _("what")
        ending = ""
        game_list = []
        if game:
            game_name = game
            game_list = [game]
            ending = game
        streaming_data = await self.get_players_per_activity(
            ctx=ctx, stream=True, game_name=game_list
        )
        if streaming_data:
            embed_list = []
            count = -1
            splitter = 1
            for key, value in sorted(streaming_data.items()):
                count += 1
                if count % splitter == 0:
                    embed = discord.Embed(
                        title=_("Who's streaming {}?").format(game_name), colour=ctx.embed_color()
                    )

                title = f"{key} ({len(value)} {_('streaming')})"
                content = ""
                for _, display_name, _ in sorted(value, key=itemgetter(2, 1)):
                    content += f"{display_name}\n"

                outputs = pagify(content, page_length=1000, priority=True)
                for enum_count, field in enumerate(outputs, 1):
                    if enum_count > 1:
                        title = f"{key} ({_('Part')} {enum_count})"
                    embed.add_field(name=f"{title}", value=field)
                if count % splitter == 0:
                    embed_list.append(copy(embed))

            await menu(
                ctx, pages=embed_list, controls=DEFAULT_CONTROLS, message=None, page=0, timeout=60
            )
        else:
            await ctx.maybe_send_embed(_("No one is streaming{ending}").format(ending=ending))

    @staticmethod
    async def get_players_per_activity(
        ctx: commands.Context,
        stream: bool = False,
        music: bool = False,
        movie: bool = None,
        game_name: List[str] = None,
    ):
        looking_for = discord.ActivityType.playing
        name_property = "name"
        if stream:
            looking_for = discord.ActivityType.streaming
            name_property = "details"
        elif music:
            looking_for = discord.ActivityType.listening
            name_property = "title"
        elif movie:
            looking_for = discord.ActivityType.watching
            name_property = "name"

        member_data_new = {}
        for member in ctx.guild.members:
            if member.activities:
                interested_in = [
                    activity for activity in member.activities if activity.type == looking_for
                ]
                if interested_in and not member.bot:
                    game = getattr(interested_in[0], name_property, None)
                    if game:
                        if (
                            game_name
                            and game not in game_name
                            and not any(g.lower() in game.lower() for g in game_name)
                        ):
                            continue

                        hoisted_roles = [r for r in member.roles if r and r.hoist]
                        top_role = max(
                            hoisted_roles, key=attrgetter("position"), default=member.top_role
                        )
                        role_value = top_role.position * -1
                        if game in member_data_new:
                            member_data_new[game].append(
                                (member.mention, member.display_name, role_value)
                            )
                        else:
                            member_data_new[game] = [
                                (member.mention, member.display_name, role_value)
                            ]
        return member_data_new
