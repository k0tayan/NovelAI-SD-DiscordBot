# NovelAI-SD-DiscordBot

Discord Bot For StableDiffusion and NovelAI
![キャプチャ](https://user-images.githubusercontent.com/16555696/209456814-a87625a7-0091-4e4d-8b3e-3003d86426ac.PNG)

## Features

- Generate images with StableDiffusion
- Generate images with NovelAI
- Generate images form elemental code prompt
- Generate images form message link
- Reaction to remove generated images

## Command

- `sd prompt -u [negative_prompt] -s [steps] -c [scale] -w [width] -h [height] -b [batch_size] -t(translate prompt) -q(add quality tag)`
  - Generate images with stable-diffusion-webui
  - You must run stable-diffusion-webui with `--api` option in `COMMANDLINE_ARGS`
  - quality tag: masterpiece, best quality,
- ❌ `nai prompt -u [negative_prompt] -m [model]`
  - Generate images with NovelAI
  - model: 0=Curated, 1=Full
  - Currently not working
- `ele`
  - Generate images form elemental code prompt
- `link [message link]`
  - Generate images form message link
- `locale [locale]`
  - Set locale
- `locale`
  - Show current locale
- `locales`
  - Show available locales
- `help`
  - Show help

## Installation

Create `.env` file referring to `example.env.`  
If you do not use NovelAI, you do not need to enter your NovelAI email address and password.  
Create `config.yml` file referring to `example_config.yml`.  
If you do not use NovelAI, set `USE_NOVELAI` to `False`.  
If you want to use google translate, set `USE_GOOGLE_TRANS` to `True` in `config.yml` and set `GOOGLE_APPLICATION_CREDENTIALS` to your API key file in `.env`.  
then

```
git clone --recursive git@github.com:k0tayan/NovelAI-SD-DiscordBot.git
poetry install
poetry run python main.py
```
