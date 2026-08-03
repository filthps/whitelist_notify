import re
import datetime
import threading
import typing
from typing import Union
from tkinter import Text, IntVar, StringVar
from tkinter.ttk import Frame, Label, Button, Checkbutton, Radiobutton
from base.main import run, stop
from base.storage import get, set_
from base.tray import minimize, create_icon_or_update
from base.autostart import autostart as set_autostart

TEXT_SEP = ","


def change_frame(parent, old_frame, new_frame, **show_kwargs):
    old_frame.__class__.destroy(old_frame)
    fr = new_frame(parent)
    fr.grid(**show_kwargs)


def get_text_from_text_obj(t: Text):
    """ get: Первый аргумент: начать чтение с первой строки и нулевого символа;
     Второй: читать до конца. """
    if not isinstance(t, Text):
        raise TypeError
    return t.get("1.0", "end-1c")


def set_validation_text_obj(t: Text, is_valid=True):
    """ Подсветить текстовую зону красной рамкой, если данные невалидны,
     убрать рамку, если валидны. """
    if not is_valid:
        t.config(highlightthickness=2, highlightbackground="#F87C63")
        return
    t.config(highlightthickness=0)


def validate_textzone_with_sites(place: Text, inner: str, one_item=False, blank=True) -> bool:
    """ Произвести валидацию данных в инпуте, где содержится один или несколько url,
     стилизировать инпут согласно валидности,
      вернуть логическое значение """
    if type(inner) is not str:
        raise TypeError
    if not isinstance(place, Text):
        raise TypeError
    if type(blank) is not bool:
        raise TypeError
    if not inner:
        if blank:
            set_validation_text_obj(place)
            return True
        set_validation_text_obj(place, is_valid=False)
        return False
    if type(one_item) is not bool:
        raise TypeError
    reg = re.compile(r"^https://\S+\.\S+/$")
    if one_item:
        if not reg.match(inner):
            set_validation_text_obj(place, is_valid=False)
            return False
        set_validation_text_obj(place)
        return True
    valid = False
    for site_path in inner.split(TEXT_SEP):
        if not reg.match(site_path):
            set_validation_text_obj(place, is_valid=False)
            break
    else:
        set_validation_text_obj(place)
        valid = True
    return valid


def validate_number_text(place: Text, inner: str, max_=float("inf"), type_=int):
    if not type_ == int and not type_ == float:
        raise TypeError
    if not isinstance(max_, (int, float,)):
        raise TypeError
    if type(place) is not Text:
        raise TypeError
    if type(inner) is not str:
        raise TypeError
    if not inner:
        set_validation_text_obj(place)
        return True
    if type_ is float:
        if "." in inner:
            try:
                float(inner)
            except ValueError:
                set_validation_text_obj(place, is_valid=False)
                return False
        else:
            set_validation_text_obj(place, is_valid=False)
            return False
    try:
        inner = type_(inner)
    except ValueError:
        set_validation_text_obj(place, is_valid=False)
        return False
    if inner > max_:
        set_validation_text_obj(place, is_valid=False)
        return False
    set_validation_text_obj(place)
    return True


def save_text_value_if_valid(t, key: str, data: str, one_item=False, blank=False, **kwargs):
    if not isinstance(t, Text):
        raise TypeError
    if type(key) is not str:
        raise TypeError
    if type(data) is not str:
        raise TypeError
    if not blank:
        if not data:
            return
    is_valid = validate_textzone_with_sites(t, data, blank=blank, one_item=one_item, **kwargs)
    if not is_valid:
        return
    if not one_item:
        data = data.split(TEXT_SEP)
    set_(key, data)


def save_number_values_if_valid(t, key: str, value: str, **kw):
    if not isinstance(t, Text):
        raise TypeError
    if type(key) is not str:
        raise TypeError
    if not isinstance(value, str):
        raise TypeError
    is_valid = validate_number_text(t, value, **kw)
    if not is_valid:
        return
    if not value:
        set_(key, "")
        return
    if value.isdigit():
        value = int(value)
    else:
        value = float(value)
    set_(key, value)
    
    
class BaseOptions:
    """ Универсальный набор событий, пригодится на многих Frame. """
    def __init__(self, tk, *args, **kwargs):
        def handle_window_buttons():
            """ Из-за функционала связанного с иконкой трея придётся изменить стандартное поведение кнопок [ _ [] X ] окна """
            is_active_task = get("active_task")
            minimize(tk, reload_menu=not is_active_task, options_disabled=is_active_task)
        tk.protocol("WM_DELETE_WINDOW", handle_window_buttons)
        super().__init__(tk, *args, **kwargs)

    @staticmethod
    def _set_events_number_text(place: Text, key: str, is_float=False, max_value=float("inf")):
        place.bind("<FocusOut>", lambda _: save_number_values_if_valid(place, key, get_text_from_text_obj(place),
                                                                       max_=max_value, type_=float if is_float else int))
        place.bind("<FocusIn>", lambda _: validate_number_text(place, get_text_from_text_obj(place),
                                                               max_=max_value, type_=float if is_float else int))
        place.bind("<Key>", lambda _: validate_number_text(place, get_text_from_text_obj(place),
                                                           max_=max_value, type_=float if is_float else int))

    @staticmethod
    def _toggle_checkbox(place: Union[IntVar, StringVar], key: str):
        value = place.get()
        set_(key, value)
        return value

    @staticmethod
    def _set_initial_text_input_values(p: Text, key: str, separator=TEXT_SEP):
        val = get(key, "")
        if isinstance(val, (tuple, list,)):
            val = separator.join(val)
        p.insert(1.0, val)


class MainFrame(BaseOptions, Frame):
    def __init__(self, tk, *args, init_run_task=False, **kwargs):
        self.worker: typing.Optional[threading.Thread] = None

        def run_task():
            if self.worker is not None:
                raise RuntimeError("Один процесс уже запущен")

            def stop_callback():
                unlock_ui()
                create_icon_or_update(tk, reload_menu=True, options_disabled=False)
            worker = run(callback=self.move_state_window, stop_callback=stop_callback)
            self.move_state_window(f"< Процесс {worker.ident} запущен > {datetime.datetime.now().strftime('%H:%M:%S')}")
            tk.geometry("560x275")
            lock_ui()
            create_icon_or_update(tk, reload_menu=True, options_disabled=True)
            self.worker = worker

        def stop_task():
            if self.worker is None:
                raise RuntimeError("Процесс не найден")
            stop()
            self.stop_button.config(state="disabled")
            self.move_state_window(f"< Процесс {self.worker.ident} ожидание завершения > "
                                   f"{datetime.datetime.now().strftime('%H:%M:%S')}")

        def lock_ui():
            self.launch_button.config(state="disabled")
            self.options_button.config(state="disabled")
            self.stop_button.config(state="normal")

        def unlock_ui():
            self.launch_button.config(state="normal")
            self.options_button.config(state="normal")
            self.stop_button.config(state="disabled")
        super().__init__(tk, *args, **kwargs)
        tk.geometry("350x26")
        self.launch_button = Button(self, text="Пуск", command=run_task)
        self.stop_button = Button(self, text="Стоп", command=stop_task)
        self.options_button = Button(self, text="Настройки", command=lambda: change_frame(tk, self, OptionsFrame))
        self.launch_button.grid(column=1, row=2)
        self.stop_button.grid(column=2, row=2)
        self.options_button.grid(column=3, row=2)
        self.state_w_inner = None
        if init_run_task:
            run_task()
            return
        unlock_ui()

    def move_state_window(self, new_msg, size=6):
        place: Text = self.__get_state_window()
        place.grid(column=2, row=1)
        if self.state_w_inner is None:
            self.state_w_inner = ["" for _ in range(size)]
        self.state_w_inner.insert(0, new_msg)
        del self.state_w_inner[-1]
        place.config(state="normal")
        place.insert("1.0", "\n".join(self.state_w_inner))
        place.config(state="disabled")

    def __get_state_window(self):
        place = Text(self, height=9, width=50)
        place.config(background="#CCC")
        return place


class OptionsFrame(BaseOptions, Frame):
    def __init__(self, tk, *a, **k):
        def autostart():
            value = self._toggle_checkbox(auto_launch_chbx, "auto_l")
            set_autostart(state=value)
        super().__init__(tk, *a, **k)
        tk.geometry("500x360")
        Label(self, text="Сайты, которых нет в белых списках:").grid(column=1, row=1)
        text_n_wl = Text(self, width=20, height=10)
        text_n_wl.grid(column=2, row=1)
        Label(self, text="Сайт, который есть в белых списках:").grid(column=1, row=2)
        text_any_wl = Text(self, width=20, height=1)
        text_any_wl.grid(column=2, row=2)
        Label(self, text="Интервал проверки (сек):").grid(column=1, row=3)
        text_interval = Text(self, width=3, height=1)
        text_interval.grid(column=2, row=3)
        Label(self, text="Таймаут ожидания ответа (мс):").grid(column=1, row=4)
        text_timeout = Text(self, width=7, height=1)
        text_timeout.grid(column=2, row=4)
        Label(self, text="Количество недоступных сервисов вне белых списков, \r"
              "прежде, чем будет проверяться доступность \r "
              "сервиса из белых списков. \r"
              "(Не больше, чем всего сервисов):").grid(column=1, row=5)
        text_error_counter = Text(self, width=2, height=1)
        text_error_counter.grid(column=2, row=5)
        hidden_launch_chbx = IntVar(value=get("launch_h", 0))
        Checkbutton(self, text="Запуск в свёрнутом виде", onvalue=1, offvalue=0,
                    variable=hidden_launch_chbx,
                    command=lambda: self._toggle_checkbox(hidden_launch_chbx, "launch_h")).grid(column=1, row=6)
        auto_launch_chbx = IntVar(value=get("auto_l", 0))
        Checkbutton(self, text="Автозагрузка", onvalue=1, offvalue=0,
                    variable=auto_launch_chbx,
                    command=autostart).grid(column=1, row=7)
        Button(self, text="Дополнительно", command=lambda: change_frame(tk, self, NotifyOptionsFrame)).grid(column=1, row=8)
        Button(self, text="Главная", command=lambda: change_frame(tk, self, MainFrame)).grid(column=2, row=8)
        self._set_initial_text_input_values(text_n_wl, "text_n_wl")
        self._set_initial_text_input_values(text_any_wl, "text_any_wl")
        self._set_initial_text_input_values(text_interval, "text_interval")
        self._set_initial_text_input_values(text_error_counter, "text_error_counter")
        self._set_initial_text_input_values(text_timeout, "text_timeout")
        self._set_events_number_text(text_timeout, "text_timeout", is_float=True,
                                     max_value=get("text_interval", float("inf")))
        self._set_events_site_list(text_n_wl, "text_n_wl")
        self._set_events_site_list(text_any_wl, "text_any_wl", one_site=True)
        self._set_events_number_text(text_interval, "text_interval")
        self._set_events_number_text(text_error_counter, "text_error_counter",
                                     max_value=len(get("text_n_wl", "")))

    @staticmethod
    def _set_events_site_list(place: Text, key: str, one_site=False, blank=False):
        place.bind("<FocusOut>", lambda _: save_text_value_if_valid(place, key, get_text_from_text_obj(place),
                                                                    one_item=one_site, blank=blank))
        place.bind("<FocusIn>", lambda _: validate_textzone_with_sites(place, get_text_from_text_obj(place),
                                                                       one_item=one_site))
        place.bind("<Key>", lambda _: validate_textzone_with_sites(place, get_text_from_text_obj(place),
                                                                   one_item=one_site))


class NotifyOptionsFrame(BaseOptions, Frame):
    def __init__(self, tk, *a, **k):
        super().__init__(tk, *a, **k)
        tk.geometry("500x90")
        Label(self, text="Уровень громкости уведомлений:").grid(column=1, row=1)
        radio_button_v = StringVar(self, get("volume", "1"))
        radio_button_values = {
            "Полная": "1",
            "Тихая": "2",
            "Без звука": "3",
        }
        for index, values in enumerate(radio_button_values.items(), start=1):
            text, val = values
            radio_button = Radiobutton(self, text=text, value=val, variable=radio_button_v,
                                       command=lambda: self._toggle_checkbox(radio_button_v, "volume"))
            radio_button.grid(column=index, row=2)
        long_sound_var = IntVar(value=get("is_long_song", 1))
        Checkbutton(self, text="Звуковое уведомление ожидает действие пользователя",
                    variable=long_sound_var, command=lambda *_: self._toggle_checkbox(long_sound_var, "is_long_song"),
                    offvalue=0, onvalue=1).grid(column=1, row=3)
        Button(self, text="Настройки", command=lambda: change_frame(tk, self, OptionsFrame)).grid(column=1, row=4)
        Button(self, text="Главная", command=lambda: change_frame(tk, self, MainFrame)).grid(column=2, row=4)
