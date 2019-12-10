# -*- coding: utf-8 -*-
from .dynamicchannels import DynamicChannels
from cog_shared.draper_lib import extra_setup


@extra_setup
def setup(bot):
    bot.add_cog(DynamicChannels(bot))
