from .Adventure import Adventure


async def setup(bot):
    bot.add_cog(Adventure(bot))
