from backend import webui, novelai
import discord
import io
import base64
from discord.ext import commands
from dotenv import load_dotenv
import os
import yaml
import uuid
import random
from logging import getLogger, StreamHandler, DEBUG

load_dotenv()
with open('config.yml', encoding='utf-8') as file:
    config = yaml.safe_load(file)

bot = commands.Bot(command_prefix='', intents=discord.Intents.all())

use_webui = config['USE_WEBUI']
use_novelai = config['USE_NOVELAI']
admin_ids = config['ADMIN_IDS']
allowed_guild_ids = config['ALLOWED_GUILD_IDS']
default_steps = config['STEPS']['DEFAULT']
maximum_steps = config['STEPS']['MAXIMUM']
default_negative_prompt = config['DEFAULT_NEGATIVE_PROMPT']

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

def save_image(binary, filename:str):
    dir = config['GENERATED_IMAGE_OUTDIR']
    with open(f'{dir}/{filename}.jpg', 'wb') as f:
        f.write(binary)

def parse_prompt(prompt: tuple) -> list[str, str, int, int]:
    prompt = list(prompt)
    # stepsの処理
    steps_index = (lambda x : x.index('-s') if '-s' in x else -1)(prompt)
    if steps_index != -1:
        if steps_index >= len(prompt)-1 or not prompt[steps_index+1].isdecimal():
            raise ValueError("stepsが不正です。")
        if int(prompt[steps_index+1]) < 1 or int(prompt[steps_index+1]) > maximum_steps:
            raise ValueError(f"stepsは1~{maximum_steps}の間で指定してください。")
        steps = int(prompt[steps_index+1])
        prompt.pop(steps_index) # stepの分を削除(-step)
        prompt.pop(steps_index) # stepの分を削除(数値)
    else:
        steps = default_steps
    # scaleの処理
    scale_index = (lambda x : x.index('-c') if '-c' in x else -1)(prompt)
    if scale_index != -1:
        if scale_index >= len(prompt)-1 or not prompt[scale_index+1].isdecimal():
            raise ValueError("scaleが不正です。")
        if int(prompt[scale_index+1]) < 1 or int(prompt[scale_index+1]) > 10:
            raise ValueError("scaleは1~10の間で指定してください。")
        scale = int(prompt[scale_index+1])
        prompt.pop(scale_index) # scaleの分を削除(-c)
        prompt.pop(scale_index) # scaleの分を削除(数値)
    else:
        scale = 12
    # negative_promptの処理
    n = (lambda x : x.index('-u') if '-u' in x else -1)(prompt)
    if n >= len(prompt)-1:
        raise ValueError("パラメーターが不正です。")
    negative_prompt = ' '.join("" if n == -1 else prompt[n+1:])
    positive_prompt = ' '.join(prompt if n == -1 else prompt[:n])
    return positive_prompt, negative_prompt, steps, scale

def log_command(ctx, image_filename):
    if(ctx.guild is None):
        logger.info(f'{ctx.author}({ctx.author.id}) {ctx.command} {image_filename}')
    else:
        logger.info(f'{ctx.author}({ctx.author.id}) {ctx.command} in {ctx.guild}({ctx.guild.id}) {image_filename}')

def log_prompt(p, n):
    logger.info(f'positive_prompt: {p}')
    logger.info(f'negative_prompt: {n}')

def bypass_admin(func):
    def predicate(ctx):
        if ctx.author.id in admin_ids:
            return True
        return func(ctx)
    return predicate

def is_allowed_guild():
    @bypass_admin
    async def predicate(ctx):
        if ctx.guild is None:
            await ctx.reply("このコマンドはサーバー内でのみ使用できます。")
            return False
        if ctx.guild.id in allowed_guild_ids:
            return True
        await ctx.reply("このコマンドはこのサーバーで使用できません。")
        return False
    return commands.check(predicate)

def is_nsfw():
    @bypass_admin
    async def predicate(ctx):
        if ctx.guild is not None and ctx.channel.is_nsfw():
            return True
        await ctx.reply("このコマンドはNSFWチャンネルでのみ使用できます。")
        return False
    return commands.check(predicate)

@bot.event
async def on_ready():
    logger.info('We have logged in as {0.user}'.format(bot))

# コマンドが存在しない場合にエラーを出さない
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

if use_webui:
    # WebUIを使用する場合
    ui = webui.WebUI(config['WEBUI_URI'], 'v1')
    @is_allowed_guild()
    @is_nsfw()
    @bot.command(name='sd')
    async def generate_with_sd(ctx, *prompt):
        """NSFWチャンネルのみ sd [positive_prompt] -u [negative_prompt] -s [steps]"""

        try:
            positive_prompt, negative_prompt, steps, scale = parse_prompt(prompt)
        except ValueError as e:
            await ctx.reply(e)
            return
        reply_message = random.choice(config["MESSAGE"]["RESPONSE"])
        if steps != default_steps:
            reply_message += '\n' + random.choice(config["MESSAGE"]["STEPS"]).replace("<0>", str(steps))
        await ctx.reply(reply_message)
        response = await ui.generate_image(
            positive_prompt, (512, 768), default_negative_prompt+negative_prompt, steps=steps, scale=scale)
        b64_image = response["images"][0]
        image_data = base64.b64decode(b64_image)
        image_filename = str(uuid.uuid4())
        save_image(image_data, image_filename)
        log_command(ctx, image_filename)
        log_prompt(positive_prompt, negative_prompt)
        file = discord.File(io.BytesIO(image_data), filename="image.jpg")
        await ctx.reply(file=file)

if use_novelai:
    # NovelAIを使用する
    nai = novelai.NovelAI()

    @is_allowed_guild()
    @bot.command(name='sfw')
    async def generate_with_nai(ctx, *prompt):
        """SFWな画像を生成します sfw [positive_prompt] -u [negative_prompt]"""

        try:
            positive_prompt, negative_prompt, _, _ = parse_prompt(prompt)
        except ValueError as e:
            await ctx.reply(e)
            return
        await ctx.reply(random.choice(config["MESSAGE"]["RESPONSE"]))
        image_data = await nai.generate(positive_prompt, (512, 768), negative_prompt, True)
        image_filename = str(uuid.uuid4())
        save_image(image_data, image_filename)
        log_command(ctx, image_filename)
        log_prompt(positive_prompt, negative_prompt)
        file = discord.File(io.BytesIO(image_data), filename="image.jpg")
        await ctx.reply(file=file)
    
    @is_allowed_guild()
    @is_nsfw()
    @bot.command(name='nsfw')
    async def generate_with_nai(ctx, *prompt):
        """NSFWチャンネルのみ nsfw [positive_prompt] -u [negative_prompt]"""

        try:
            positive_prompt, negative_prompt, _, _ = parse_prompt(prompt)
        except ValueError as e:
            await ctx.reply(e)
            return
        await ctx.reply(random.choice(config["MESSAGE"]["RESPONSE"]))
        image_data = await nai.generate(positive_prompt, (512, 768), negative_prompt, False)
        image_filename = str(uuid.uuid4())
        save_image(image_data, image_filename)
        log_command(ctx, image_filename)
        log_prompt(positive_prompt, negative_prompt)
        file = discord.File(io.BytesIO(image_data), filename="image.jpg")
        await ctx.reply(file=file)

if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
