# -*- coding: utf-8 -*-

# Cog Relative Imports
from .audiodb import AudioDB31


async def setup(bot):
    cog = AudioDB31(bot)
    bot.add_cog(cog)
