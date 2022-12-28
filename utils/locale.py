from config.load_config import config

import os
import yaml

_bot_locale_name = config['LOCALE']
_locales = {}
for i in os.listdir('locales'):
    with open(f'locales/{i}', encoding='utf-8') as file:
        _locales[i.strip('.yml')] = yaml.safe_load(file)

_user_locale = {}


def get_all_locale_names() -> list:
    """Get all locale names"""
    return list(_locales.keys())


def get_bot_locale() -> dict:
    """Get the bot locale"""
    return _locales[_bot_locale_name]


def get_bot_locale_name() -> str:
    """Get the bot locale name"""
    return _bot_locale_name


def set_bot_locale(locale_name: str) -> None:
    """Set the locale for bot"""
    if locale_name not in get_all_locale_names():
        raise ValueError("Invalid locale name")
    else:
        global _bot_locale_name
        _bot_locale_name = locale_name


def get_user_locale(user_id: int) -> dict:
    """Get the user locale"""
    if user_id in _user_locale:
        return _user_locale[user_id]
    else:
        return get_bot_locale()


def set_user_locale(user_id: int, locale_name: str) -> None:
    """Set the locale for user"""
    if locale_name not in get_all_locale_names():
        raise ValueError("Invalid locale name")
    else:
        _user_locale[user_id] = _locales[locale_name]
