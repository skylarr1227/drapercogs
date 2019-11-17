# -*- coding: utf-8 -*-
# Standard Library
from contextlib import suppress

# Cog Relative Imports
from .dev import Dev
from .jsonoverload import DraperDevJson


def setup(bot):
    with suppress(Exception):
        bot.add_cog(DraperDevJson(bot))
    with suppress(Exception):
        bot.add_cog(Dev())
