from config.load_config import config

from collections.abc import Callable
from dotenv import load_dotenv

load_dotenv()
from google.cloud import translate
from dataclasses import dataclass, field


@dataclass
class StableDiffusionPrompt:
    prompt: str
    negative_prompt: str
    steps: int
    scale: int
    width: int
    height: int
    batch_size: int
    translate: bool
    original_prompt: str = None
    original_negative_prompt: str = None

    def __post_init__(self):
        self.original_prompt = self.prompt
        self.original_negative_prompt = self.negative_prompt
        self.prompt = self.prompt.replace('{', '(').replace('}', ')')
        self.negative_prompt = self.negative_prompt.replace('{', '(').replace('}', ')')
        if self.translate:
            self.prompt, self.negative_prompt = translate_prompt(self.prompt, self.negative_prompt)


def parse_option(prompt: list, option: str, value_range: list[int, int, int] = None, f: Callable = None, error: ValueError = None) -> int:
    if value_range is None:
        index = prompt.index(option)
        if index > 0:
            prompt.pop(index)
            return True
        else:
            return False
    _min, _max, default = value_range
    if option in prompt:
        index = prompt.index(option)
        if index >= len(prompt)-1 or not prompt[index+1].isdecimal():
            raise ValueError({'message': 'INVALID_OPTION', 'args': {'option': option}})
        if int(prompt[index+1]) < _min or int(prompt[index+1]) > _max:
            raise ValueError({'message': 'INVALID_OPTION_RANGE', 'args': {'option': option, 'max': _max, 'min': _min}})
        value = int(prompt[index+1])
        if f is not None:
            result = f(value)
            if result is False:
                raise error
        prompt.pop(index)  # optionの分を削除(-option)
        prompt.pop(index)  # optionの分を削除(数値)
    else:
        value = default
    return value


def parse_prompt(args: list) -> StableDiffusionPrompt:
    scale = parse_option(args, '-c', config['SCALE'])
    steps = parse_option(args, '-s', config['STEPS'])
    width = parse_option(args, '-w', config['WIDTH'], lambda x: x % 64 == 0, ValueError({'message': 'WIDTH_NOT_MULTIPLE_OF_64'}))
    height = parse_option(args, '-h', config['HEIGHT'], lambda x: x % 64 == 0, ValueError({'message': 'HEIGHT_NOT_MULTIPLE_OF_64'}))
    batch_size = parse_option(args, '-b', config['BATCH_SIZE'])
    translate = parse_option(args, '-t')
    # negative_promptの処理
    n = (lambda x: x.index('-u') if '-u' in x else -1)(args)
    if n >= len(args)-1:
        raise ValueError({'message': 'INVALID_NEGATIVE_PROMPT'})
    negative_prompt = ' '.join("" if n == -1 else args[n+1:])
    _prompt = ' '.join(args if n == -1 else args[:n])
    response = StableDiffusionPrompt(
        prompt=_prompt,
        negative_prompt=negative_prompt,
        steps=steps,
        scale=scale,
        width=width,
        height=height,
        batch_size=batch_size,
        translate=translate
    )
    return response


def parse_prompt_nai(prompt: tuple) -> dict:
    prompt = list(prompt)
    model = parse_option(prompt, '-m', [0, 1, 0])
    # negative_promptの処理
    n = (lambda x: x.index('-u') if '-u' in x else -1)(prompt)
    if n >= len(prompt)-1:
        raise ValueError({'message': 'INVALID_NEGATIVE_PROMPT'})
    negative_prompt = ' '.join("" if n == -1 else prompt[n+1:])
    positive_prompt = ' '.join(prompt if n == -1 else prompt[:n])
    response = {
        'positive_prompt': positive_prompt,
        'negative_prompt': negative_prompt,
        'model': model
    }
    return response


def translate_prompt(positive_prompt: str, negative_prompt: str) -> dict:
    if not config['USE_GOOGLE_TRANS']:
        return positive_prompt, negative_prompt
    location = "global"
    project_id = config['GOOGLE_TRANS_PROJECT_ID']
    parent = f"projects/{project_id}/locations/{location}"
    client = translate.TranslationServiceClient()
    text = [positive_prompt]
    if negative_prompt != '':
        text.append(negative_prompt)
    response = client.translate_text(
        request={
            'parent': parent,
            'contents': text,
            'mime_type': 'text/plain',  # mime types: text/plain, text/html
            'target_language_code': 'en'
        }
    )
    positive_prompt = response.translations[0].translated_text
    negative_prompt = response.translations[1].translated_text if len(response.translations) > 1 else ''
    return positive_prompt, negative_prompt
