# -*- coding: utf-8 -*-
# Cog Relative Imports
from .jsonoverload import DraperDevJson


def setup(bot):
    bot.add_cog(DraperDevJson(bot))
