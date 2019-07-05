from .status import MemberStatus


def setup(bot):
    cog = MemberStatus(bot)
    bot.add_cog(cog)
