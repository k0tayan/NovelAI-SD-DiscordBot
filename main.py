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
from collections.abc import Callable
import json

load_dotenv()
with open('config.yml', encoding='utf-8') as file:
    config = yaml.safe_load(file)

bot = commands.Bot(command_prefix='', intents=discord.Intents.all())

use_webui = config['USE_WEBUI']
use_novelai = config['USE_NOVELAI']
admin_ids = config['ADMIN_IDS']
allowed_guild_ids = config['ALLOWED_GUILD_IDS']
default_negative_prompt = config['DEFAULT_NEGATIVE_PROMPT']

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

elemental_code_jsons = [config['ELEMENTAL_CODE_JSON_PATH'] + '/' + i for i in os.listdir(config['ELEMENTAL_CODE_JSON_PATH'])]

def save_image(binary, filename:str):
    dir = config['GENERATED_IMAGE_OUTDIR']
    with open(f'{dir}/{filename}.jpg', 'wb') as f:
        f.write(binary)

def parse_option(prompt: list, option: str, default: int, max: int, f: Callable=None, error: ValueError=None) -> int:
    if option in prompt:
        index = prompt.index(option)
        if index >= len(prompt)-1 or not prompt[index+1].isdecimal():
            raise ValueError(f"{option}が不正です。")
        if int(prompt[index+1]) < 1 or int(prompt[index+1]) > max:
            raise ValueError(f"{option}は1~{max}の間で指定してください。")
        value = int(prompt[index+1])
        if f is not None:
            result = f(value)
            if result:
                prompt.pop(index) # optionの分を削除(-option)
                prompt.pop(index) # optionの分を削除(数値)
            else:
                raise error
    else:
        value = default
    return value

def parse_prompt(prompt: tuple) -> dict:
    prompt = list(prompt)
    scale = parse_option(prompt, '-c', config['SCALE']['DEFAULT'], config['SCALE']['MAXIMUM'])
    steps = parse_option(prompt, '-s', config['STEPS']['DEFAULT'], config['STEPS']['MAXIMUM'])
    width = parse_option(prompt, '-w', config['SIZE']['WIDTH']['DEFAULT'], config['SIZE']['WIDTH']['MAXIMUM'], lambda x : x % 64 == 0, ValueError("widthは64の倍数で指定してください。"))
    height = parse_option(prompt, '-h', config['SIZE']['HEIGHT']['DEFAULT'], config['SIZE']['HEIGHT']['MAXIMUM'], lambda x : x % 64 == 0, ValueError("heightは64の倍数で指定してください。"))
    batch_size = parse_option(prompt, '-b', config['BATCH_SIZE']['DEFAULT'], config['BATCH_SIZE']['MAXIMUM'])
    # negative_promptの処理
    n = (lambda x : x.index('-u') if '-u' in x else -1)(prompt)
    if n >= len(prompt)-1:
        raise ValueError("パラメーターが不正です。")
    negative_prompt = ' '.join("" if n == -1 else prompt[n+1:])
    positive_prompt = ' '.join(prompt if n == -1 else prompt[:n])
    response = {
        'positive_prompt': positive_prompt,
        'negative_prompt': negative_prompt,
        'steps': steps,
        'scale': scale,
        'width': width,
        'height': height,
        'batch_size': batch_size
    }
    return response

def log_command(ctx, image_filename):
    if(ctx.guild is None):
        logger.info(f'{ctx.author}({ctx.author.id}) {ctx.command} {image_filename}')
    else:
        logger.info(f'{ctx.author}({ctx.author.id}) {ctx.command} in {ctx.guild}({ctx.guild.id}) {image_filename}')

def log_prompt(prompt: dict):
    print(prompt)

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

@bot.event
async def on_raw_reaction_add(payload):
    if payload.emoji.name == '🗑️':
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.author == bot.user:
            if len(message.attachments) > 0:
                logger.info(f'{payload.member.name}({message.author.id}) delete {message.attachments[0].url}')
                await message.delete()
            else:
                logger.info(f'{payload.member.name}({message.author.id}) delete {message.content}')
                await message.delete()

if use_webui:
    # WebUIを使用する場合
    ui = webui.WebUI(config['WEBUI_URI'], 'v1')
    @is_allowed_guild()
    @is_nsfw()
    @bot.command(name='sd')
    async def generate_with_sd(ctx, *prompt):
        """sd [positive_prompt] -u [negative_prompt] -s [steps] -c [scale] -w [width] -h [height] -b [batch_size]"""

        try:
            args = parse_prompt(prompt)
        except ValueError as e:
            await ctx.reply(e)
            return
        reply_message = random.choice(config["MESSAGE"]["RESPONSE"])
        if args["steps"] != config['STEPS']['DEFAULT']:
            reply_message += '\n' + random.choice(config["MESSAGE"]["STEPS"]).replace("<0>", str(args["steps"]))
        positive_prompt = args["positive_prompt"].replace('{', '(').replace('}', ')')
        negative_prompt = args["negative_prompt"].replace('{', '(').replace('}', ')')
        if '{' in args['positive_prompt']+args['negative_prompt'] or '}' in args['positive_prompt']+args['negative_prompt']:
            reply_message += '\n' + random.choice(config["MESSAGE"]["BRACKET"])
        if args['batch_size'] == 1:
            await ctx.reply(reply_message)
            response = await ui.generate_image(
                positive_prompt, (args['width'], args['height']), default_negative_prompt+negative_prompt, steps=args["steps"], scale=args["scale"])
            b64_image = response["images"][0]
            image_data = base64.b64decode(b64_image)
            image_filename = str(uuid.uuid4())
            file = discord.File(io.BytesIO(image_data), filename="image.jpg")
            await ctx.reply(file=file)
        else:
            if type(ctx.message.channel) is discord.channel.TextChannel:
                thread = await ctx.message.create_thread(name=" ".join(prompt)[:100])
                await thread.send(reply_message)
            else:
                await ctx.reply(reply_message)
            response = await ui.generate_image(
                positive_prompt, (args['width'], args['height']), default_negative_prompt+negative_prompt, steps=args["steps"], scale=args["scale"], batch_size=args['batch_size'])
            for b64_image in response["images"]:
                image_data = base64.b64decode(b64_image)
                image_filename = str(uuid.uuid4())
                logger.info(f"Generated image: {image_filename}")
                file = discord.File(io.BytesIO(image_data), filename="image.jpg")
                if type(ctx.message.channel) is discord.channel.TextChannel:
                    await thread.send(file=file)
                else:
                    await ctx.reply(file=file)                    
        save_image(image_data, image_filename)
        log_command(ctx, image_filename)
        log_prompt(args)
    
    @bot.command(name='ele')
    async def generate_with_ele(ctx):
        json_path = random.choice(elemental_code_jsons)
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        positive_prompt = json_data['prompt'].replace('{', '(').replace('}', ')')
        negative_prompt = json_data["negative_prompt"].replace('{', '(').replace('}', ')')
        reply_message = random.choice(config["MESSAGE"]["ELEMENTAL_CODE"])
        reply_message += '\n sd ' + positive_prompt + '\n -u ' + negative_prompt
        await ctx.reply(reply_message)
        if 'width' not in json_data:
            json_data['width'] = config['WIDTH']['DEFAULT']
        if 'height' not in json_data:
            json_data['height'] = config['HEIGHT']['DEFAULT']
        if 'steps' not in json_data:
            json_data['steps'] = config['STEPS']['DEFAULT']
        if 'cfg_scale' not in json_data:
            json_data['cfg_scale'] = config['SCALE']['DEFAULT']
        response = await ui.generate_image(
                positive_prompt, (json_data['width'][0], json_data['height'][0]), negative_prompt, steps=json_data["steps"][0], scale=json_data["cfg_scale"][0], batch_size=1)
        b64_image = response["images"][0]
        image_data = base64.b64decode(b64_image)
        image_filename = str(uuid.uuid4())
        file = discord.File(io.BytesIO(image_data), filename="image.jpg")
        await ctx.reply(file=file)
        save_image(image_data, image_filename)
        log_command(ctx, image_filename)
        log_prompt(json_data)
        

if use_novelai:
    # NovelAIを使用する
    nai = novelai.NovelAI()

    @is_allowed_guild()
    @bot.command(name='sfw')
    async def generate_with_nai(ctx, *prompt):
        """SFWな画像を生成します sfw [positive_prompt] -u [negative_prompt]"""

        try:
            args = parse_prompt(prompt)
        except ValueError as e:
            await ctx.reply(e)
            return
        await ctx.reply(random.choice(config["MESSAGE"]["RESPONSE"]))
        image_data = await nai.generate(args["positive_prompt"], (512, 768), args["negative_prompt"], True)
        image_filename = str(uuid.uuid4())
        save_image(image_data, image_filename)
        log_command(ctx, image_filename)
        log_prompt(args)
        file = discord.File(io.BytesIO(image_data), filename="image.jpg")
        await ctx.reply(file=file)
    
    @is_allowed_guild()
    @is_nsfw()
    @bot.command(name='nsfw')
    async def generate_with_nai(ctx, *prompt):
        """NSFWチャンネルのみ nsfw [positive_prompt] -u [negative_prompt]"""

        try:
            args = parse_prompt(prompt)
        except ValueError as e:
            await ctx.reply(e)
            return
        await ctx.reply(random.choice(config["MESSAGE"]["RESPONSE"]))
        image_data = await nai.generate(args["positive_prompt"], (512, 768), args["negative_prompt"], False)
        image_filename = str(uuid.uuid4())
        save_image(image_data, image_filename)
        log_command(ctx, image_filename)
        log_prompt(args)
        file = discord.File(io.BytesIO(image_data), filename="image.jpg")
        await ctx.reply(file=file)

@bot.event
async def on_message(message):
    if message.content.startswith('https://discord.com/channels/') or \
        message.content.startswith('https://discordapp.com/channels/') or \
            message.content.startswith('https://canary.discord.com/channels/') or \
                message.content.startswith('https://ptb.discord.com/channels/'):
        # メッセージがリンクの場合
        if use_webui:
            # WebUIを使用する場合
            server_id, channel_id, message_id = message.content.split('/')[-3:]
            if server_id is None or channel_id is None or message_id is None:
                return
            if not server_id.isdigit() or not channel_id.isdigit() or not message_id.isdigit():
                return
            server = bot.get_guild(int(server_id))
            if server is None:
                return
            channel = server.get_channel(int(channel_id))
            if channel is None:
                return
            linked_message = await channel.fetch_message(int(message_id))
            # 取得したメッセージに対して返信する
            if message.author != bot.user and linked_message.content != "" and message.channel.is_nsfw():
                # 自分自身の発言ではない、メッセージが空でない、NSFWチャンネルである場合
                message_text = random.choice(config['MESSAGE']['LINK']) + '\n' + linked_message.content
                await message.reply(message_text)
                response = await ui.generate_image(
                    linked_message.content, (512, 768), default_negative_prompt, steps=config['STEPS']['DEFAULT'], scale=config['SCALE']['DEFAULT'])
                b64_image = response["images"][0]
                image_data = base64.b64decode(b64_image)
                image_filename = str(uuid.uuid4())
                save_image(image_data, image_filename)
                logger.info(f"Prompt from {message.author}: {linked_message.content}")
                logger.info(f"Generated image: {image_filename}")
                file = discord.File(io.BytesIO(image_data), filename="image.jpg")
                await message.reply(file=file)
    else:
        await bot.process_commands(message)

if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
