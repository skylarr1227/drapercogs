# -*- coding: utf-8 -*-
# Cog Relative Imports
from .status import MemberStatus


def setup(bot):
    cog = MemberStatus(bot)
    bot.add_cog(cog)
