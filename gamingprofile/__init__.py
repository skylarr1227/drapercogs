from .gamingprofile import GamingProfile


def setup(bot):
    bot.add_cog(GamingProfile(bot))
