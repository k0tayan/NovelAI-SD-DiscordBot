from discord.ext import commands

from config.load_config import config
from utils import locale
from utils.logger import MyLogger


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = MyLogger(__name__)

    @commands.command(name="help")
    @MyLogger.log_command
    async def help(self, ctx: commands.Context):
        """help"""

        user_locale = locale.get_user_locale(ctx.author.id)
        try:
            help_message = user_locale["MESSAGE"]["HELP"]["start"]
            if config["USE_WEBUI"]:
                help_message += "\n\n" + user_locale["MESSAGE"]["HELP"]["sd"]
                help_message += "\n\n" + user_locale["MESSAGE"]["HELP"]["ele"]
            if config["USE_NOVELAI"]:
                help_message += "\n\n" + user_locale["MESSAGE"]["HELP"]["nai"]
            help_message += "\n\n" + user_locale["MESSAGE"]["HELP"]["locale"]
            help_message += "\n\n" + user_locale["MESSAGE"]["HELP"]["help"]
            await ctx.reply(help_message)
        except Exception as error:
            self.logger.error(error)


async def setup(bot):
    await bot.add_cog(Help(bot))
