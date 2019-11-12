# -*- coding: utf-8 -*-
# Cog Relative Imports
from .dev import Dev
from .jsonoverload import DraperDevJson


def setup(bot):
    bot.add_cog(DraperDevJson(bot))
    bot.add_cog(Dev(bot))
