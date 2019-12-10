# -*- coding: utf-8 -*-
# Cog Relative Imports
from .status import MemberStatus

from cog_shared.draper_lib import extra_setup


@extra_setup
def setup(bot):
    cog = MemberStatus(bot)
    bot.add_cog(cog)
