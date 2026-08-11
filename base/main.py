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
from socket import timeout as timeout_exc
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from winotify import Notification, audio
from base.storage import get, set_

INTERVAL_SEC = get("text_interval")
TIMEOUT_MS = get("text_timeout")
NO_WL_SITE = get("text_n_wl")
WHITELIST_SITE = get("text_wl")
IMAGES_PATH = os.path.join(os.getcwd(), "images")
AUDIO_PATH = os.path.join(os.getcwd(), "audio")
IS_LONG_NOTI = get("is_long_song")
NOTI_VOLUME = get("volume")

worker_is_alive = True


def main(callback=None, stop_callback=None):
    global worker_is_alive
    worker_is_alive = True

    @launch_callback
    def stop_():
        stop_callback() if callable(stop_callback) else None
        set_("active_task", False)
        stop()

    @launch_callback
    def start():
        set_("active_task", True)

    check_online = not check_available_any_resource(NO_WL_SITE)
    if check_online:
        send_state(callback, other_message="Ожидаем появление доступа в нормальный интернет...")
    else:
        send_state(callback, other_message="Доступ к нормальному интернету есть, \n мониторим момент введения белых списков")
    checked_sites = set()
    checked_wl = set()
    sites = cycle(NO_WL_SITE)
    white_list_sites = cycle(WHITELIST_SITE)
    current_path = ""
    request = ...
    white_list_call_counter = 0
    start()
    Event().wait(INTERVAL_SEC)
    while True:
        if not worker_is_alive:
            send_state(callback,
                       other_message=f"< Процесс {current_thread().ident} убит> "
                                     f"{datetime.datetime.now().strftime('%H:%M:%S')}", )
            stop_()
            sys.exit()
        if len(checked_sites) < NO_WL_SITE.__len__():
            current_path = next(sites)
            request = create_request(current_path)
        if not isinstance(request, (HTTPError, URLError, timeout_exc,)) and request.msg == "OK":
            send_state(callback, current_path, request.code)
            if check_online:
                send_state(callback,
                           other_message=f"< Процесс {current_thread().ident} убит> "
                                         f"{datetime.datetime.now().strftime('%H:%M:%S')}")
                show_notification(True, websites=(current_path,))
                stop()
            else:
                checked_sites = set()
        else:
            if not check_online:
                if len(checked_sites) < NO_WL_SITE.__len__():
                    send_state(callback, current_path, str(request))
                checked_sites.add(current_path)
                if NO_WL_SITE.__len__() == len(checked_sites):
                    current_path_wl = next(white_list_sites)
                    send_state(callback,
                               other_message=f"< Проверка доступности белых списков {current_path_wl} > "
                                             f"{datetime.datetime.now().strftime('%H:%M:%S')}")
                    white_list_call_counter += 1
                    if check_available(current_path_wl):
                        if white_list_call_counter >= WHITELIST_SITE.__len__():
                            white_list_call_counter = 0
                            checked_sites = set()
                            checked_wl = set()
                            continue
                        checked_wl.add(current_path_wl)
                        if checked_wl.__len__() == len(WHITELIST_SITE):
                            show_notification(False)
                            send_state(callback,
                                       other_message=f"< Процесс {current_thread().ident} убит> "
                                                     f"{datetime.datetime.now().strftime('%H:%M:%S')}", center=True)
                            stop()
                    else:
                        checked_wl.remove(current_path_wl) if current_path_wl in checked_wl else None
            else:
                checked_sites.remove(current_path) if current_path in checked_sites else None
        Event().wait(INTERVAL_SEC)


def launch_callback(call):
    """ Блокировка потока для передачи данных главному потоку """
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
def show_notification(state: bool, websites=tuple()):
    def get_str(u: typing.Iterable) -> str:
        return ", \n".join([x[8:x.rindex(".")] for x in u])
    if not websites:
        return
    end = "лись" if len(websites) > 1 else "лся"
    if state:
        n = Notification(app_id="Интернет детектор by filthps",
                         title="Дали интернет!", msg=f"Наконец-то. \n{get_str(websites)} откры{end}.",
                         icon=os.path.join(IMAGES_PATH, "wl-off.png"))
    else:
        n = Notification(app_id="Интернет детектор by filthps",
                         title="Белые списки!", msg=f"Охуеть. Опять эти пидоры всё отключили к хуям. \n"
                                                    f"{get_str(websites)} не откры{end}.",
                         icon=os.path.join(IMAGES_PATH, "wl-on.png"))
    if NOTI_VOLUME == "1":
        n.set_audio(audio.LoopingAlarm6 if state else audio.LoopingCall9, loop=IS_LONG_NOTI)
    if NOTI_VOLUME == "2":
        n.set_audio(audio.Silent, False)
    n.show()


@launch_callback
def send_state(callback, *args, other_message=""):
    """ Сформировать строку состояния и передать её главному потоку, в ui, обновив виджет состояния. """
    str_ = other_message or " ---- ".join(map(str, args))
    callback(str_)


def create_request(path: str):
    try:
        r = urlopen(path, timeout=TIMEOUT_MS)
    except HTTPError as error:
        return error
    except URLError as error:
        return error
    except TimeoutError as error:
        return error
    return r


def check_available(item):
    r = create_request(item)
    if isinstance(r, (HTTPError, URLError, timeout_exc,)):
        return False
    if r.msg == "OK":
        return True
    return False


def check_available_any_resource(items):
    for item in items:
        if check_available(item):
            return True
    return False


def load_const():
    global INTERVAL_SEC
    global TIMEOUT_MS
    global NO_WL_SITE
    global WHITELIST_SITE
    global IS_LONG_NOTI
    global NOTI_VOLUME

    INTERVAL_SEC = get("text_interval")
    TIMEOUT_MS = get("text_timeout")
    NO_WL_SITE = get("text_n_wl")
    WHITELIST_SITE = get("text_wl")
    IS_LONG_NOTI = get("is_long_song")
    NOTI_VOLUME = get("volume", "1")


def run(callback=None, stop_callback=None) -> typing.Optional[Thread]:
    load_const()
    try:
        is_valid()
    except Exception as exp:
        send_state(callback, other_message=exp.__str__(), main_thread=True)
        return
    process = Thread(target=lambda: main(callback=callback, stop_callback=stop_callback))
    process.start()
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
    if TIMEOUT_MS // 1000 >= INTERVAL_SEC:
        raise RuntimeError("Таймаут ожидания ответа не может быть дольше периодичности проверки")
    if any(filter(lambda i: not isinstance(i, str), NO_WL_SITE)):
        raise TypeError
    regexp = re.compile(r"^https://\S+\.\S+/$")
    for site in NO_WL_SITE:
        if not regexp.match(site):
            raise ValueError(f"{site}. Сайт должен быть вида: https://site.zone/.")
    for site in WHITELIST_SITE:
        if not regexp.match(site):
            raise ValueError(f"{site}. Сайт должен быть вида: https://site.zone/.")
