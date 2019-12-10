# -*- coding: utf-8 -*-
from .publishermanager import PublisherManager

from cog_shared.draper_lib import extra_setup


@extra_setup
def setup(bot):
    bot.add_cog(PublisherManager(bot))
