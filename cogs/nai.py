from config.load_config import config
import discord
from discord.ext import commands
from utils import locale, checks
from utils.logger import MyLogger

from utils.prompt import parse_prompt_nai
from backend import novelai
import uuid
import random
import io


class NovelAICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = MyLogger(__name__)

    @checks.is_allowed_guild()
    @commands.command(name='nai')
    async def generate_with_nai(self, ctx, *prompt):
        """nai [positive_prompt] -u [negative_prompt] -m [model]"""

        self.logger.info('Start nai command')
        if not config['USE_NOVELAI']:
            self.logger.info('NovelAI is not enabled')
            return
        user_locale = locale.get_user_locale(ctx.author.id)
        if ctx.guild is None:
            self.logger.info(f'{ctx.author}({ctx.author.id}) {ctx.command}')
        else:
            self.logger.info(f'{ctx.author}({ctx.author.id}) {ctx.command} in {ctx.guild}({ctx.guild.id})')
        try:
            try:
                args = parse_prompt_nai(prompt)
            except ValueError as e:
                await ctx.reply(e)
                return
            if args['model'] == 1 and not ctx.channel.is_nsfw():
                await ctx.reply(user_locale['ERROR']['NSFW_ONLY'])
                return
            if not ctx.channel.is_nsfw():
                # 強制的にNSFWを除外する
                for ng in config['NSFW_EXCLUDE']:
                    args['positive_prompt'] = args['positive_prompt'].replace(ng, "")
                args['negative_prompt'] += '(((nsfw)))'
            self.logger.info(str(args))
            is_safe = args['model'] == 0
            await ctx.reply(random.choice(user_locale['MESSAGE']['RESPONSE']))
            image_data = await novelai.generate_image(
                prompt=args['positive_prompt'],
                resolution=(512, 768),
                negative_prompt=args['negative_prompt'],
                is_safe=is_safe
            )
            image_filename = self.logger.save_image(image_data)
            file = discord.File(io.BytesIO(image_data), filename=f'{image_filename}.jpg')
            message = await ctx.reply(file=file)
            await message.add_reaction(config['REACTION']['DELETE'])
            self.logger.info('End nai command')
        except Exception as e:
            self.logger.error(e)


async def setup(bot):
    await bot.add_cog(NovelAICog(bot))
