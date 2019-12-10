# -*- coding: utf-8 -*-
from .gamingprofile import GamingProfile

from cog_shared.draper_lib import extra_setup


@extra_setup
def setup(bot):
    bot.add_cog(GamingProfile(bot))
