from .publishermanager import PublisherManager


def setup(bot):
    bot.add_cog(PublisherManager(bot))
