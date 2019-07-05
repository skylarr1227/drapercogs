from .quotes import Quotes


def setup(bot):
    cog = Quotes(bot)
    bot.add_cog(cog)
