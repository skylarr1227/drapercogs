from .jsonoverload import DraperDevJson


def setup(bot):
    bot.add_cog(DraperDevJson(bot))
