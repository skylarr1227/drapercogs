from .dynamicchannels import DynamicChannels


def setup(bot):
    bot.add_cog(DynamicChannels(bot))
