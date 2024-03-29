import io
import random

import discord
from discord.ext import commands

from backend import novelai
from config.load_config import config
from utils import checks, locale
from utils.logger import MyLogger
from utils.prompt import NovelAIPrompt, parse_prompt_nai


class NovelAICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = MyLogger(__name__)

    @checks.is_allowed_guild()
    @commands.command(name="nai")
    @MyLogger.log_command
    async def generate_with_nai(self, ctx, *args):
        """nai [positive_prompt] -u [negative_prompt] -m [model]"""

        if not config["USE_NOVELAI"]:
            self.logger.info("NovelAI is not enabled")
            return
        user_locale = locale.get_user_locale(ctx.author.id)
        try:
            try:
                prompt: NovelAIPrompt = parse_prompt_nai(args)
            except ValueError as e:
                await ctx.reply(e)
                return
            if prompt.model == 1 and not ctx.channel.is_nsfw():
                await ctx.reply(user_locale["ERROR"]["NSFW_ONLY"])
                return
            if not ctx.channel.is_nsfw():
                # 強制的にNSFWを除外する
                for ng in config["NSFW_EXCLUDE"]:
                    prompt.prompt = prompt.prompt.replace(ng, "")
                prompt.negative_prompt += "(((nsfw)))"
            self.logger.info(str(prompt))
            is_safe = prompt.model == 0
            await ctx.reply(random.choice(user_locale["MESSAGE"]["RESPONSE"]))
            image_data = await novelai.generate_image(
                prompt=prompt.prompt,
                resolution=(512, 768),
                negative_prompt=prompt.negative_prompt,
                is_safe=is_safe,
                quality_toggle=bool(prompt.quality_toggle),
            )
            image_filename = self.logger.save_image(image_data)
            file = discord.File(
                io.BytesIO(image_data), filename=f"{image_filename}.jpg"
            )
            message = await ctx.reply(file=file)
            await message.add_reaction(config["REACTION"]["DELETE"])
        except Exception as e:
            self.logger.error(e)


async def setup(bot):
    await bot.add_cog(NovelAICog(bot))
