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
from base.storage import get

INTERVAL_SEC = ...
ERRORS_COUNTER_TO_SHOW_MSG = ...
TIMEOUT_MS = ...
IMAGES_PATH = os.path.join(os.getcwd(), "images")
AUDIO_PATH = os.path.join(os.getcwd(), "audio")
WEB_RESOURCE = ...
ANY_WHITELIST_SITE = ...

sites = []


def main(check_online=True):
    checked_sites = []
    while True:
        current_path = next(sites)
        if has_internet(current_path):
            if check_online:
                checked_sites.append(current_path)
                if checked_sites.__len__() == ERRORS_COUNTER_TO_SHOW_MSG:
                    show_notification(True, websites=tuple(checked_sites))
                    return
            else:
                checked_sites.remove(current_path) if current_path in checked_sites else None
        else:
            if not check_online:
                checked_sites.append(current_path)
                if ERRORS_COUNTER_TO_SHOW_MSG == len(checked_sites):
                    if not final_check():
                        show_notification(False, websites=tuple(checked_sites))
                        return
                    else:
                        checked_sites = []
            else:
                checked_sites.remove(current_path) if current_path in checked_sites else None
        time.sleep(INTERVAL_SEC)


def has_internet(path: str) -> bool:
    try:
        r = request.urlopen(path, timeout=TIMEOUT_MS)
    except HTTPError:
        return False
    if r.msg == "OK":
        return True
    return False


def final_check():
    """ Допустим все наши проверки на доступность ресурсов оказались ложны.
     Это, само по себе, ничего не значит, - возможно, просто отключен интернет.
     Тогда нужно проверить доступность любого сайта, который есть в белых списках """
    return has_internet(ANY_WHITELIST_SITE)


def show_notification(state: bool, websites=tuple()):
    def get_str(u: typing.Iterable) -> str:
        return ", \r".join([x[8:x.rindex(".")] for x in u])
    if not websites:
        return
    end = "лись" if len(websites) > 1 else "лся"
    if state:
        n = Notification(app_id="Интернет детектор by filthps",
                         title="Дали интернет!", msg=f"Наконец-то. \r{get_str(websites)} откры{end}.", duration="long",
                         icon=os.path.join(IMAGES_PATH, "wl-off.png"))
        n.set_audio(audio.LoopingCall, loop=True)
    else:
        n = Notification(app_id="Интернет детектор by filthps",
                         title="Белые списки!", msg=f"Охуеть. Опять эти пидоры всё отключили к хуям. \r"
                                                    f"{get_str(websites)} не откры{end}.", duration="long",
                         icon=os.path.join(IMAGES_PATH, "wl-on.png"))
        n.set_audio(audio.LoopingAlarm10, loop=True)
    n.show()


def get_current_state():
    """
    Определить состояние интернета на текущий момент.
    True - Интернет полноценен
    False - Действуют WL
    """
    return has_internet(next(sites))


def reload_const():
    global INTERVAL_SEC
    global ERRORS_COUNTER_TO_SHOW_MSG
    global TIMEOUT_MS
    global WEB_RESOURCE
    global ANY_WHITELIST_SITE
    global sites

    INTERVAL_SEC = get("text_interval")
    ERRORS_COUNTER_TO_SHOW_MSG = get("text_error_counter")  # Количество недоступных сервисов, необходимое для понимания ситуации. Дефолт 1
    TIMEOUT_MS = get("text_timeout")
    WEB_RESOURCE = get("text_n_wl")  # Один или несколько сайтов, которых нет в белых списках
    ANY_WHITELIST_SITE = get("text_any_wl")

    sites = cycle(WEB_RESOURCE)


def run():
    reload_const()
    is_valid()
    initial_state = get_current_state()
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
    regexp = re.compile(r"^https://\S+\.\S+/$")
    if not regexp.match(ANY_WHITELIST_SITE):
        raise ValueError
    for site in WEB_RESOURCE:
        if not regexp.match(site):
            raise ValueError(f"{site}. Сайт должен быть вида: https://site.zone/.")
