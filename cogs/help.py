from discord.ext import commands
from utils import locale

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def help(self, ctx: commands.Context):
        """help"""
        help_message = locale.get_bot_locale()["MESSAGE"]["HELP"]['start']
        help_message += '\n\n' + locale.get_bot_locale()["MESSAGE"]["HELP"]['sd']
        help_message += '\n\n' if help_message != "" else "" + locale.get_bot_locale()["MESSAGE"]["HELP"]['sfw']
        help_message += '\n\n' + locale.get_bot_locale()["MESSAGE"]["HELP"]['nsfw']
        help_message += '\n\n' + locale.get_bot_locale()["MESSAGE"]["HELP"]['ele']
        help_message += '\n\n' + locale.get_bot_locale()["MESSAGE"]["HELP"]['locale']
        help_message += '\n\n' + locale.get_bot_locale()["MESSAGE"]["HELP"]['help']
        await ctx.reply(help_message)

async def setup(bot):
    await bot.add_cog(Help(bot))