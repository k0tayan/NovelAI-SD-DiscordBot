from config.load_config import config
from discord.ext import commands
from utils import locale
import logging

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
    
    @commands.command(name='help')
    async def help(self, ctx: commands.Context):
        """help"""

        user_locale = locale.get_user_locale(ctx.author.id)
        try:
            help_message = user_locale["MESSAGE"]["HELP"]['start']
            if config['USE_WEBUI']:
                help_message += '\n\n' + user_locale["MESSAGE"]["HELP"]['sd']
                help_message += '\n\n' + user_locale["MESSAGE"]["HELP"]['ele']
            if config['USE_NOVELAI']:
                help_message += '\n\n' if help_message != "" else "" + user_locale["MESSAGE"]["HELP"]['sfw']
                help_message += '\n\n' + user_locale["MESSAGE"]["HELP"]['nsfw']
            help_message += '\n\n' + user_locale["MESSAGE"]["HELP"]['locale']
            help_message += '\n\n' + user_locale["MESSAGE"]["HELP"]['help']
            await ctx.reply(help_message)
        except Exception as error:
            self.logger.error(error)

async def setup(bot):
    await bot.add_cog(Help(bot))