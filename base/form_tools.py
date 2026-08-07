import re
from tkinter import Text
from base.storage import get, set_

TEXT_SEP = ","
MIN_INTERVAL_PER_ONE_SITE_SEC = 5


def get_error_string_from_settings():
    """ Сформировать строку ошибки """
    error_text = []
    check_interval = get("text_interval", 0)
    if not get("text_n_wl"):
        error_text.append("1) Поле с сайтами не из White List не может быть пустым.")
    if not check_interval:
        error_text.append("3) Введите числовое значение 1-20. Интервал запросов в секундах.")
    if not get("text_timeout"):
        error_text.append("4) Введите допустимую задержку ответа.")
    if check_interval < get("text_timeout", 0.0):
        error_text.append("Периодичность запросов не может быть короче ожидания.")
    no_wl_items_l = len(get("text_n_wl", tuple()))
    wl_items_l = len(get("text_wl", tuple()))
    if not no_wl_items_l:
        error_text.append("Не представлено ни одно веб-ресурса не из белых списков")
    else:
        if MIN_INTERVAL_PER_ONE_SITE_SEC > no_wl_items_l * check_interval:
            error_text.append(f"Интервал обращений к одному конкретному ресурсу - {no_wl_items_l * check_interval} сек, \n"
                              f"что подозрительно часто. Интервал должен быть минимум - {MIN_INTERVAL_PER_ONE_SITE_SEC} секунд."
                              f"Добавьте больше адресов ресурсов не из белых списков")
    if not wl_items_l:
        error_text.append("Не представлено ни одно веб-ресурса из белых списков")
    else:
        if MIN_INTERVAL_PER_ONE_SITE_SEC > wl_items_l * check_interval:
            error_text.append(f"Интервал обращений к одному конкретному ресурсу - {wl_items_l * check_interval} сек, \n"
                              f"что подозрительно часто. Интервал должен быть минимум - {MIN_INTERVAL_PER_ONE_SITE_SEC} секунд."
                              f"Добавьте больше адресов ресурсов из белых списков")
    return "\n".join(error_text)


def get_alert_window_size(inner: str):
    inner = inner.split("\n")
    width = max(map(len, inner)) * 8
    if len(inner) == 1:
        return f"{width}x55"
    return "x".join((str(width), str(len(inner) * 30)))


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


def validate_number_text(place: Text, inner: str, min_=0, max_=float("inf"), type_=int):
    if not type_ == int and not type_ == float:
        raise TypeError
    if not isinstance(max_, (int, float,)):
        raise TypeError
    if not isinstance(min_, (int, float,)):
        raise TypeError
    if min_ > max_:
        raise ValueError
    if type(place) is not Text:
        raise TypeError
    if type(inner) is not str:
        raise TypeError
    if not inner:
        set_validation_text_obj(place, is_valid=False)
        return False
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
    if inner < min_:
        set_validation_text_obj(place, is_valid=False)
        return False
    if inner > max_:
        set_validation_text_obj(place, is_valid=False)
        return False
    set_validation_text_obj(place)
    return True


def save_text_value_if_valid(t, key: str, data: str, one_item=False, blank=False):
    if not isinstance(t, Text):
        raise TypeError
    if type(key) is not str:
        raise TypeError
    if type(data) is not str:
        raise TypeError
    if not blank:
        if not data:
            return
    is_valid = validate_textzone_with_sites(t, data, blank=blank, one_item=one_item)
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
