import os
import yaml
from contextvars import ContextVar

_current_locale_name = ContextVar("_current_locale_name", default="ja")
_locales = {}
for i in os.listdir('locales'):
    with open(f'locales/{i}', encoding='utf-8') as file:
        _locales[i.strip('.yml')] = yaml.safe_load(file)

def get_all_locale_names() -> list:
    """Get all locale names"""
    return list(_locales.keys())

def get_bot_locale() -> dict:
    """Get the bot locale"""
    return _locales[_current_locale_name.get()]

def get_bot_locale_name() -> str:
    """Get the bot locale name"""
    return _current_locale_name.get()

def set_bot_locale(locale_name: str) -> None:
    """Set the locale for bot"""
    if locale_name not in get_all_locale_names():
        raise ValueError("Invalid locale name")
    else:
        _current_locale_name.set(locale_name)

class Locale:
    def __init__(self, bot):
        self.bot = bot