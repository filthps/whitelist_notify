import re
from tkinter import Text, IntVar
from tkinter.ttk import Frame, Label, Button, Checkbutton
from base.main import run, stop
from storage import get, set_

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
    if not inner.isdigit():
        try:
            float(inner)
        except ValueError:
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


def save_text_value_if_valid(t, key: str, data: str, one_item=False, **kwargs):
    if not isinstance(t, Text):
        raise TypeError
    if type(key) is not str:
        raise TypeError
    if type(data) is not str:
        raise TypeError
    if not data:
        return
    is_valid = validate_textzone_with_sites(t, data, one_item=one_item, **kwargs)
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


class MainFrame(Frame):
    def __init__(self, tk, *args, **kwargs):
        super().__init__(tk, *args, **kwargs)
        tk.geometry("350x200")
        Label(self, text="Отображение текущего состояния").grid(column=1, row=1)
        Button(self, text="Пуск", command=run).grid(column=1, row=2)
        Button(self, text="Стоп", command=stop).grid(column=2, row=2)
        Button(self, text="Настройки", command=lambda: change_frame(tk, self, OptionsFrame)).grid(column=2, row=3)
        self.grid()


class OptionsFrame(Frame):
    def __init__(self, tk, *a, **k):
        super().__init__(tk, *a, **k)
        tk.geometry("500x400")
        Label(self, text="Настройки").grid(column=1, row=1)
        Label(self, text="Сайты, которых нет в белых списках:").grid(column=1, row=2)
        text_n_wl = Text(self, width=20, height=10)
        text_n_wl.grid(column=2, row=2)
        Label(self, text="Сайт, который есть в белых списках:").grid(column=1, row=3)
        text_any_wl = Text(self, width=20, height=1)
        text_any_wl.grid(column=2, row=3)
        Label(self, text="Интервал проверки (сек):").grid(column=1, row=4)
        text_interval = Text(self, width=3, height=1)
        text_interval.grid(column=2, row=4)
        Label(self, text="Количество недоступных сервисов вне белых списков, \r"
              "прежде, чем будет проверяться доступность \r "
              "сервиса из белых списков. \r"
              "(Не больше, чем всего сервисов):").grid(column=1, row=5)
        text_error_counter = Text(self, width=2, height=1)
        text_error_counter.grid(column=2, row=5)
        hidden_launch_chbx = IntVar(value=get("launch_h", 0))
        Checkbutton(self, text="Запуск в свёрнутом виде", onvalue=1, offvalue=0,
                    variable=hidden_launch_chbx,
                    command=lambda *_: self.__toggle_checkbox(hidden_launch_chbx, "launch_h")).grid(column=1, row=6)
        auto_launch_chbx = IntVar(value=get("auto_l", 0))
        Checkbutton(self, text="Автозагрузка", onvalue=1, offvalue=0,
                    variable=auto_launch_chbx,
                    command=lambda *_: self.__toggle_checkbox(auto_launch_chbx, "auto_l")).grid(column=1, row=7)
        Button(self, text="Назад", command=lambda: change_frame(tk, self, MainFrame)).grid(column=2, row=8)
        self.__set_initial_text_input_values(text_n_wl, "text_n_wl")
        self.__set_initial_text_input_values(text_any_wl, "text_any_wl")
        self.__set_initial_text_input_values(text_interval, "text_interval")
        self.__set_initial_text_input_values(text_error_counter, "text_error_counter")
        self.__set_events_site_list(text_n_wl, "text_n_wl")
        self.__set_events_site_list(text_any_wl, "text_any_wl", one_site=True)
        self.__set_events_number_text(text_interval, "text_interval")
        self.__set_events_number_text(text_error_counter, "text_error_counter",
                                      max_value=len(get("text_n_wl", "")))
        self.grid()

    @staticmethod
    def __set_events_site_list(place: Text, key: str, one_site=False):
        place.bind("<FocusOut>", lambda _: save_text_value_if_valid(place, key, get_text_from_text_obj(place),
                                                                    one_item=one_site))
        place.bind("<FocusIn>", lambda _: validate_textzone_with_sites(place, get_text_from_text_obj(place),
                                                                       one_item=one_site))
        place.bind("<Key>", lambda _: validate_textzone_with_sites(place, get_text_from_text_obj(place),
                                                                   one_item=one_site))

    @staticmethod
    def __set_events_number_text(place: Text, key: str, is_float=False, max_value=float("inf")):
        place.bind("<FocusOut>", lambda _: save_number_values_if_valid(place, key, get_text_from_text_obj(place),
                                                                       max_=max_value, type_=float if is_float else int))
        place.bind("<FocusIn>", lambda _: validate_number_text(place, get_text_from_text_obj(place),
                                                               max_=max_value, type_=float if is_float else int))
        place.bind("<Key>", lambda _: validate_number_text(place, get_text_from_text_obj(place),
                                                           max_=max_value, type_=float if is_float else int))

    @staticmethod
    def __toggle_checkbox(place: IntVar, key: str):
        set_(key, place.get())

    @staticmethod
    def __set_initial_text_input_values(p: Text, key: str, separator=TEXT_SEP):
        val = get(key, "")
        if isinstance(val, (tuple, list,)):
            val = separator.join(val)
        p.insert(1.0, val)
