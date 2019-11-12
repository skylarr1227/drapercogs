from .jsonoverload import DraperDevJson
from .dev import Dev


def setup(bot):
    bot.add_cog(DraperDevJson(bot))
    bot.add_cog(Dev(bot))
