# -*- coding: utf-8 -*-
import importlib
from functools import wraps
from . import lib

# Thanks Sinbad


def extra_setup(func):
    @wraps(func)
    def _new_setup(bot):
        try:
            module = importlib.reload(lib)
            cog = module.ToolBox(bot)
            bot.remove_cog("Draper's Lib")
            bot.add_cog(cog)
        finally:  # Yes, I am intentionally returning in a finally statement.
            return func(bot)  # pylint: disable=lost-exception

    return _new_setup
