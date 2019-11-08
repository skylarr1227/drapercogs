# -*- coding: utf-8 -*-
# Cog Relative Imports
from .audiodb import AudioDB


async def setup(bot):
    audio = bot.get_cog("Audio")
    if audio is None:
        raise RuntimeError("Audio cog needs to be loaded first.")
    cog = AudioDB(bot)
    await cog.initialize(
        audio
    )  # TODO: Move this to a lock event that waits for audio to be loaded before initializing
    bot.add_cog(cog)
