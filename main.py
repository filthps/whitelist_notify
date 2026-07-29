""" Запуск во время действия белых списков будет мониторить их отключение и выдаст соответствующее уведомление;
Напротив, запуск во время работы полноценного интернета, будет мониторить включение белых списков, выдав уведомление,
что белые списки включены.
"""
import sys
import re
import os
import time
import typing
from itertools import cycle
import urllib.request as request
from urllib.error import HTTPError
from winotify import Notification, audio

INTERVAL_SEC = 10
ERRORS_COUNTER_TO_SHOW_MSG = 3  # Количество недоступных сервисов, необходимое для понимания ситуации. Дефолт 1
WEB_RESOURCE = (
    "https://pikabu.ru/",
    "https://github.com/",
    "https://aviasales.ru/",
    "https://sberbank.ru/",
    "https://vseinstrumenti.ru/",
    "https://tbank.ru/"
)  # Один или несколько сайтов, которых нет в белых списках
ANY_WHITELIST_SITE = "https://vk.ru/"
TIMEOUT_MS = 1000.0
RINGTON_PATH = ""

sites = cycle(WEB_RESOURCE)


def main(check_online=True):
    checked_sites = []
    while True:
        current_path = next(sites)
        if has_internet(current_path, status=check_online):
            if not check_online:
                checked_sites.append(current_path)
                if checked_sites.__len__() == ERRORS_COUNTER_TO_SHOW_MSG:
                    show_notification(True, websites=tuple(checked_sites))
                    return
            else:
                checked_sites.remove(current_path) if current_path in checked_sites else None
                time.sleep(INTERVAL_SEC)
                continue
        if check_online:
            checked_sites.append(current_path)
        else:
            checked_sites.remove(current_path) if current_path in checked_sites else None
            time.sleep(INTERVAL_SEC)
            continue
        if ERRORS_COUNTER_TO_SHOW_MSG == len(checked_sites):
            if not final_check():
                show_notification(False, websites=tuple(checked_sites))
                return
        time.sleep(INTERVAL_SEC)


def has_internet(path: str, status=True) -> bool:
    try:
        r = request.urlopen(path, timeout=TIMEOUT_MS)
        print(r.__dict__)
    except HTTPError:
        return not status
    if r.msg == "OK":
        if status:
            return True
        return False
    if status:
        return False
    return True


def final_check():
    """ Допустим все наши проверки на доступность ресурсов оказались ложны.
     Это, само по себе, ничего не значит, - возможно, просто отключен интернет.
     Тогда нужно проверить доступность любого сайта, который есть в белых списках """
    return has_internet(ANY_WHITELIST_SITE)


def show_notification(state: bool, websites=tuple()):
    def get_str(u: typing.Iterable) -> str:
        return r", \n".join([x[8:x.rindex(".")] for x in u])
    if not websites:
        return
    end = "лись" if len(websites) > 1 else "лся"
    if state:
        Notification(app_id="Интернет детектор by filthps",
                     title="Дали интернет!", msg=f"Наконец-то. {get_str(websites)} откры{end}.", duration="long").show()
        return
    Notification(app_id="Интернет детектор by filthps",
                 title="Белые списки!", msg=f"Охуеть. Опять эти пидоры всё отключили к хуям. "
                                            f"{get_str(websites)} не откры{end}.", duration="long").show()


def run():
    initial_state = has_internet(next(sites))
    time.sleep(INTERVAL_SEC)
    main(not initial_state)


def stop():
    sys.exit()


def is_valid():
    if type(TIMEOUT_MS) is not float:
        raise TypeError
    if TIMEOUT_MS <= 0:
        raise ValueError
    if not isinstance(INTERVAL_SEC, int):
        raise TypeError
    if INTERVAL_SEC <= 0:
        raise ValueError
    if type(ERRORS_COUNTER_TO_SHOW_MSG) is not int:
        raise TypeError
    if ERRORS_COUNTER_TO_SHOW_MSG < 0:
        raise ValueError
    if TIMEOUT_MS // 1000 >= INTERVAL_SEC:
        raise RuntimeError("Таймаут ожидания ответа не может быть дольше периодичности проверки")
    if ERRORS_COUNTER_TO_SHOW_MSG >= len(WEB_RESOURCE):
        raise ValueError()
    if any(filter(lambda i: not isinstance(i, str), WEB_RESOURCE)):
        raise TypeError
    if not isinstance(ANY_WHITELIST_SITE, str):
        raise TypeError
    regexp = re.compile(r"https://[a-z]+\.[a-z]+/")
    if not regexp.match(ANY_WHITELIST_SITE):
        raise ValueError
    for site in WEB_RESOURCE:
        if not regexp.match(site):
            raise ValueError(f"{site}. Сайт должен быть вида: https://site.zone/.")


if __name__ == "__main__":
    is_valid()
    run()
