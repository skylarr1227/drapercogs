# -*- coding: utf-8 -*-
from .customchannels import CustomChannels

from cog_shared.draper_lib import extra_setup


@extra_setup
def setup(bot):
    bot.add_cog(CustomChannels(bot))
