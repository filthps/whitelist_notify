""" Запуск во время действия белых списков будет мониторить их отключение и выдаст соответствующее уведомление;
Напротив, запуск во время работы полноценного интернета, будет мониторить включение белых списков, выдав уведомление,
что белые списки включены.
"""
import sys
import datetime
import os
import re
import typing
from threading import Thread, Lock, Event, current_thread
from itertools import cycle
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from winotify import Notification, audio
from base.storage import get, set_

INTERVAL_SEC = get("text_interval")
ERRORS_COUNTER_TO_SHOW_MSG = get("text_error_counter")
TIMEOUT_MS = get("text_timeout")
WEB_RESOURCE = get("text_n_wl")
ANY_WHITELIST_SITE = get("text_any_wl")
IMAGES_PATH = os.path.join(os.getcwd(), "images")
AUDIO_PATH = os.path.join(os.getcwd(), "audio")
IS_LONG_NOTI = get("is_long_song")
NOTI_VOLUME = get("volume")

sites = cycle([])
worker_is_alive = True


def launch_callback(call):
    def wrap(*a, main_thread=False, **kwargs):
        if main_thread:
            call(*a, **kwargs)
            return
        lock = Lock()
        lock.acquire(blocking=True)
        call(*a, **kwargs)
        lock.release()
    return wrap


@launch_callback
def send_state(callback, *args, other_message=""):
    """ Сформировать строку состояния и передать её главному потоку, в ui, обновив виджет состояния. """
    str_ = other_message or " ---- ".join(map(str, args))
    callback(str_)


def main(callback=None, stop_callback=None):
    global worker_is_alive
    worker_is_alive = True

    @launch_callback
    def stop_():
        stop_callback() if callable(stop_callback) else None
    check_online = not get_current_state()
    if check_online:
        send_state(callback, other_message="Ожидаем появление доступа в нормальный интернет...")
    else:
        send_state(callback, other_message="Доступ к нормальному интернету есть, \n мониторим момент введения белых списков")
    Event().wait(INTERVAL_SEC)
    checked_sites = []
    while True:
        if not worker_is_alive:
            send_state(callback,
                       other_message=f"< Процесс {current_thread().ident} убит> "
                                     f"{datetime.datetime.now().strftime('%H:%M:%S')}", )
            if stop_callback:
                stop_()
            set_("active_task", False)
            sys.exit()
        current_path = next(sites)
        request = create_request(current_path)
        if isinstance(request, (URLError, HTTPError,)):
            send_state(callback, current_path, str(request))
        else:
            send_state(callback, current_path, request.code)
        if not isinstance(request, (HTTPError, URLError,)) and request.msg == "OK":
            if check_online:
                checked_sites.append(current_path)
                if checked_sites.__len__() == ERRORS_COUNTER_TO_SHOW_MSG:
                    show_notification(True, websites=tuple(checked_sites))
                    stop_() if stop_callback else None
                    send_state(callback,
                               other_message=f"< Процесс {current_thread().ident} убит> "
                                             f"{datetime.datetime.now().strftime('%H:%M:%S')}")
            else:
                checked_sites.remove(current_path) if current_path in checked_sites else None
        else:
            if not check_online:
                checked_sites.append(current_path)
                if ERRORS_COUNTER_TO_SHOW_MSG == len(checked_sites):
                    if not final_check():
                        show_notification(False, websites=tuple(checked_sites))
                        stop_() if stop_callback else None
                        send_state(callback,
                                   other_message=f"< Процесс {current_thread().ident} убит> "
                                                 f"{datetime.datetime.now().strftime('%H:%M:%S')}", center=True)
                    else:
                        checked_sites = []
            else:
                checked_sites.remove(current_path) if current_path in checked_sites else None
        Event().wait(INTERVAL_SEC)


def create_request(path: str):
    try:
        r = urlopen(path, timeout=TIMEOUT_MS)
    except HTTPError as error:
        return error
    except URLError as error:
        return error
    return r


def final_check() -> bool:
    """ Допустим все наши проверки на доступность ресурсов оказались ложны.
     Это, само по себе, ничего не значит, - возможно, просто отключен интернет.
     Тогда нужно проверить доступность любого сайта, который есть в белых списках """
    request = create_request(ANY_WHITELIST_SITE)
    return not isinstance(URLError, HTTPError) and request.msg == "OK"


def show_notification(state: bool, websites=tuple()):
    def get_str(u: typing.Iterable) -> str:
        return ", \r".join([x[8:x.rindex(".")] for x in u])
    if not websites:
        return
    end = "лись" if len(websites) > 1 else "лся"
    if state:
        n = Notification(app_id="Интернет детектор by filthps",
                         title="Дали интернет!", msg=f"Наконец-то. \r{get_str(websites)} откры{end}.",
                         icon=os.path.join(IMAGES_PATH, "wl-off.png"))
    else:
        n = Notification(app_id="Интернет детектор by filthps",
                         title="Белые списки!", msg=f"Охуеть. Опять эти пидоры всё отключили к хуям. \r"
                                                    f"{get_str(websites)} не откры{end}.",
                         icon=os.path.join(IMAGES_PATH, "wl-on.png"))
    if NOTI_VOLUME == "1":
        n.set_audio(audio.LoopingAlarm10, IS_LONG_NOTI)
    if NOTI_VOLUME == "2":
        n.set_audio(audio.Silent, False)
    n.show()


def get_current_state():
    """
    Определить состояние интернета на текущий момент.
    True - Интернет полноценен
    False - Действуют WL
    """
    r = create_request(next(sites))
    return not isinstance(r, (HTTPError, URLError,)) and r.msg == "OK"


def load_const():
    global INTERVAL_SEC
    global ERRORS_COUNTER_TO_SHOW_MSG
    global TIMEOUT_MS
    global WEB_RESOURCE
    global ANY_WHITELIST_SITE
    global IS_LONG_NOTI
    global NOTI_VOLUME
    global sites

    INTERVAL_SEC = get("text_interval")
    ERRORS_COUNTER_TO_SHOW_MSG = get("text_error_counter")
    TIMEOUT_MS = get("text_timeout")
    WEB_RESOURCE = get("text_n_wl")
    ANY_WHITELIST_SITE = get("text_any_wl")
    IS_LONG_NOTI = get("is_long_song")
    NOTI_VOLUME = get("volume", "1")
    sites = cycle(WEB_RESOURCE)


def run(callback=None, stop_callback=None) -> typing.Optional[Thread]:
    load_const()
    try:
        is_valid()
    except Exception as exp:
        send_state(callback, other_message=exp.__str__(), main_thread=True)
        return
    process = Thread(target=lambda: main(callback=callback, stop_callback=stop_callback))
    process.start()
    set_("active_task", True)
    return process


def stop():
    global worker_is_alive
    worker_is_alive = False


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
