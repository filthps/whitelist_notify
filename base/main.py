""" Запуск во время действия белых списков будет мониторить их отключение и выдаст соответствующее уведомление;
Напротив, запуск во время работы полноценного интернета, будет мониторить включение белых списков, выдав уведомление,
что белые списки включены.
"""
import os
import re
import sys
import datetime
from typing import Optional
from threading import Thread, Lock, Event, current_thread
from itertools import cycle
from socket import timeout as timeout_exc
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from winotify import Notification, audio
from base.storage import get, set_

IMAGES_PATH = os.path.join(os.getcwd(), "images")
AUDIO_PATH = os.path.join(os.getcwd(), "audio")
INTERVAL_SEC = ...
TIMEOUT_MS = ...
NO_WL_SITE = ...
WHITELIST_SITE = ...
IS_LONG_NOTI = ...
NOTI_VOLUME = ...
IS_CYCLIC = ...

worker: Optional[Thread] = None
worker_is_alive = True


def freeze(call):
    """ Блокировка потока для передачи данных главному потоку """
    def inner(*a, **kwargs):
        lock = Lock()
        lock.acquire(blocking=True)
        call(*a, **kwargs)
        lock.release()
    return inner


def main(msg_box_getter, stop_callback=None):
    global worker_is_alive
    worker_is_alive = True

    @freeze
    def exit_():
        stop_callback() if callable(stop_callback) else None
    send_state(msg_box_getter,
               f"< Процесс {current_thread().ident} запущен > {datetime.datetime.now().strftime('%H:%M:%S')}")
    check_online = not check_available_any_resource(NO_WL_SITE)
    if check_online:
        send_state(msg_box_getter, other_message="Ожидаем появление доступа в нормальный интернет...")
    else:
        send_state(msg_box_getter, other_message="Доступ к нормальному интернету есть, \n мониторим момент введения белых списков")
    checked_sites = set()
    checked_wl = set()
    sites = cycle(NO_WL_SITE)
    white_list_sites = cycle(WHITELIST_SITE)
    current_path = ""
    request = ...
    white_list_call_counter = 0
    set_("active_task", True)
    Event().wait(INTERVAL_SEC)
    while True:
        if not worker_is_alive:
            send_state(msg_box_getter,
                       other_message=f"< Процесс {current_thread().ident} убит> "
                                     f"{datetime.datetime.now().strftime('%H:%M:%S')}")
            set_("active_task", False)
            exit_()
            sys.exit()
        if len(checked_sites) < NO_WL_SITE.__len__():
            current_path = next(sites)
            request = create_request(current_path)
        if not isinstance(request, (HTTPError, URLError, timeout_exc,)) and request.msg == "OK":
            send_state(msg_box_getter, current_path, request.code)
            if check_online:
                send_notification(True, websites=(current_path,))
                if IS_CYCLIC:
                    Event().wait(INTERVAL_SEC)
                    main(msg_box_getter, stop_callback=stop_callback)
                    return
                else:
                    worker_is_alive = False
            else:
                checked_sites = set()
        else:
            if not check_online:
                if len(checked_sites) < NO_WL_SITE.__len__():
                    send_state(msg_box_getter, current_path, str(request))
                checked_sites.add(current_path)
                if NO_WL_SITE.__len__() == len(checked_sites):
                    current_path_wl = next(white_list_sites)
                    send_state(msg_box_getter,
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
                            send_notification(False)
                            if IS_CYCLIC:
                                Event().wait(INTERVAL_SEC)
                                main(msg_box_getter, stop_callback=stop_callback)
                                return
                            else:
                                worker_is_alive = False
                    else:
                        checked_wl.remove(current_path_wl) if current_path_wl in checked_wl else None
        Event().wait(INTERVAL_SEC)


@freeze
def send_notification(state: bool):
    if state:
        n = Notification(app_id="Интернет детектор by filthps",
                         title="Дали интернет!", msg=f"Наконец-то.",
                         icon=os.path.join(IMAGES_PATH, "wl-off.png"))
    else:
        n = Notification(app_id="Интернет детектор by filthps",
                         title="Белые списки!", msg=f"Охуеть. Опять эти пидоры всё отключили к хуям.",
                         icon=os.path.join(IMAGES_PATH, "wl-on.png"))
    if NOTI_VOLUME == "1":
        n.set_audio(audio.LoopingAlarm6 if state else audio.LoopingCall9, loop=IS_LONG_NOTI)
    if NOTI_VOLUME == "2":
        n.set_audio(audio.Silent, False)
    n.show()


@freeze
def send_state(msg_box_getter, *args, other_message=""):
    str_ = other_message or " ---- ".join(map(str, args))
    msg_box_getter(str_)


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
    global IS_CYCLIC

    INTERVAL_SEC = get("text_interval")
    TIMEOUT_MS = get("text_timeout")
    NO_WL_SITE = get("text_n_wl")
    WHITELIST_SITE = get("text_wl")
    IS_LONG_NOTI = get("is_long_song")
    NOTI_VOLUME = get("volume", "1")
    IS_CYCLIC = get("is_cycle_task", False)


def run(msg_box_getter, **k):
    global worker
    load_const()
    try:
        is_valid()
    except Exception as exp:
        send_state(msg_box_getter, other_message=exp.__str__())
        return
    process = Thread(target=main, args=(msg_box_getter,), kwargs=k)
    process.start()
    worker = process


def stop(text_place_getter: callable):
    global worker_is_alive
    send_state(text_place_getter, f"< Процесс {worker.ident} ожидание завершения > "
                                  f"{datetime.datetime.now().strftime('%H:%M:%S')}")
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
