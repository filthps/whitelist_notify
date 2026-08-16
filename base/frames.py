import tkinter
from typing import Union
from tkinter import Text, IntVar, StringVar
from tkinter.ttk import Frame, Label, Button, Checkbutton, Radiobutton
from base.main import run, stop
from base.storage import get, set_
from base.tray import minimize, create_icon_or_update
from base.autostart import autostart as set_autostart
from base.form_tools import save_text_value_if_valid, save_number_values_if_valid, get_text_from_text_obj, \
    validate_number_text, validate_textzone_with_sites, get_error_string_from_settings, get_alert_window_size, TEXT_SEP


def center_window(main: tkinter, width=500, height=500):
    screen_w, screen_h = main.winfo_screenwidth(), main.winfo_screenheight()
    pos_x, pos_y = (screen_w - width) // 2, (screen_h - height) // 2
    main.geometry(f"{width}x{height}+{pos_x}+{pos_y}")


def show_message_window(main, text="", title="", size="100x50"):
    """ Вывести окно с текстом """
    new_window = tkinter.Toplevel(main, takefocus=True)
    new_window.title(title)
    new_window.geometry(size)
    label = tkinter.Label(new_window, text=text or get_error_string_from_settings())
    label.pack(pady=20)
    x, y = size.split("x")
    center_window(new_window, width=int(x), height=int(y))


def change_frame(parent, old_frame, new_frame, **show_kwargs):
    old_frame.__class__.destroy(old_frame)
    fr = new_frame(parent)
    fr.grid(**show_kwargs)
    
    
class BaseOptions:
    """ Универсальный набор событий, пригодится на многих Frame. """
    def __init__(self, tk, *args, **kwargs):
        def handle_window_buttons():
            """ Из-за функционала связанного с иконкой трея придётся изменить стандартное поведение кнопок [ _ [] X ] окна """
            is_active_task = get("active_task", False)
            minimize(tk, reload_menu=not is_active_task, options_disabled=is_active_task)
        tk.protocol("WM_DELETE_WINDOW", handle_window_buttons)
        super().__init__(tk, *args, **kwargs)

    @staticmethod
    def _check_settings(tk):
        error_str = get_error_string_from_settings()
        if not error_str:
            return
        show_message_window(tk, title="Исправьте некоторые ошибки", text=error_str,
                            size=get_alert_window_size(error_str))

    @staticmethod
    def _set_events_number_text(place: Text, key: str, is_float=False, min_value: Union[float, int] = 0,
                                max_value=float("inf")):
        place.bind("<FocusOut>", lambda _: save_number_values_if_valid(place, key, get_text_from_text_obj(place),
                                                                       min_=min_value, max_=max_value,
                                                                       type_=float if is_float else int))
        place.bind("<FocusIn>", lambda _: validate_number_text(place, get_text_from_text_obj(place),
                                                               min_=min_value, max_=max_value,
                                                               type_=float if is_float else int))
        place.bind("<KeyPress>", lambda _: validate_number_text(place, get_text_from_text_obj(place),
                                                                min_=min_value, max_=max_value,
                                                                type_=float if is_float else int))

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
        def run_task():
            def stop_callback():
                unlock_ui()
                create_icon_or_update(tk, reload_menu=True, options_disabled=False)
            self._check_settings(tk)
            if get_error_string_from_settings():
                return
            center_window(tk, width=638, height=175)
            run(self.move_state_window, stop_callback=stop_callback)
            lock_ui()
            create_icon_or_update(tk, reload_menu=True, options_disabled=True, create_icon=False)

        def lock_ui():
            self.launch_button.config(state="disabled")
            self.options_button.config(state="disabled")
            self.stop_button.config(state="normal")

        def unlock_ui():
            self.launch_button.config(state="normal")
            self.options_button.config(state="normal")
            self.stop_button.config(state="disabled")
        super().__init__(tk, *args, **kwargs)
        center_window(tk, width=230, height=26)
        self.launch_button = Button(self, text="Пуск", command=run_task)
        self.stop_button = Button(self, text="Стоп", command=lambda: stop(self.move_state_window))
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
        if self.state_w_inner is None:
            self.state_w_inner = ["" for _ in range(size)]
        self.state_w_inner.insert(0, new_msg)
        del self.state_w_inner[-1]
        place = self.__get_state_window()
        place.config(state="normal")
        place.insert("1.0", "\n".join(self.state_w_inner))
        place.config(state="disabled")
        place.grid(column=2, row=1)

    def __get_state_window(self):
        place = Text(self, height=9, width=60)
        place.config(background="#CCC")
        return place


class OptionsFrame(BaseOptions, Frame):
    def __init__(self, tk, *a, **k):
        def autostart():
            value = self._toggle_checkbox(auto_launch_chbx, "auto_l")
            set_autostart(state=value)

        def leave_frame(target):
            if get_error_string_from_settings():
                self._check_settings(tk)
                return
            change_frame(tk, self, target)
        super().__init__(tk, *a, **k)
        center_window(tk, width=500, height=440)
        Label(self, text="Сайты, которых нет в белых списках:\n https://exemple-name.com/, через ,").grid(column=1, row=1)
        text_n_wl = Text(self, width=35, height=10)
        text_n_wl.grid(column=2, row=1)
        Label(self, text="Сайты, которе есть в белых списках:\n https://exemple-name.com/, через ,").grid(column=1, row=2)
        text_any_wl = Text(self, width=35, height=10)
        text_any_wl.grid(column=2, row=2)
        Label(self, text="Интервал проверки (сек):").grid(column=1, row=3)
        text_interval = Text(self, width=3, height=1)
        text_interval.grid(column=2, row=3)
        Label(self, text="Таймаут ожидания ответа (мс):").grid(column=1, row=4)
        text_timeout = Text(self, width=7, height=1)
        text_timeout.grid(column=2, row=4)
        hidden_launch_chbx = IntVar(value=get("launch_h", 0))
        Checkbutton(self, text="Запуск в свёрнутом виде", onvalue=1, offvalue=0,
                    variable=hidden_launch_chbx,
                    command=lambda: self._toggle_checkbox(hidden_launch_chbx, "launch_h")).grid(column=1, row=6)
        auto_launch_chbx = IntVar(value=get("auto_l", 0))
        Checkbutton(self, text="Автозагрузка", onvalue=1, offvalue=0,
                    variable=auto_launch_chbx,
                    command=autostart).grid(column=1, row=7)
        Button(self, text="Дополнительно", command=lambda: leave_frame(NotifyOptionsFrame)).grid(column=1, row=8)
        Button(self, text="Главная", command=lambda: leave_frame(MainFrame)).grid(column=2, row=8)
        self._set_initial_text_input_values(text_n_wl, "text_n_wl")
        self._set_initial_text_input_values(text_any_wl, "text_wl")
        self._set_initial_text_input_values(text_interval, "text_interval")
        self._set_initial_text_input_values(text_timeout, "text_timeout")
        self._set_events_number_text(text_timeout, "text_timeout", is_float=True,
                                     max_value=float(get("text_interval", 0)), min_value=1.0)
        self._set_events_site_list(text_n_wl, "text_n_wl")
        self._set_events_site_list(text_any_wl, "text_wl")
        self._set_events_number_text(text_interval, "text_interval", min_value=1, max_value=20)

    @staticmethod
    def _set_events_site_list(place: Text, key: str, one_site=False, blank=False):
        place.bind("<FocusOut>", lambda _: save_text_value_if_valid(place, key, get_text_from_text_obj(place),
                                                                    one_item=one_site, blank=blank))
        place.bind("<FocusIn>", lambda _: validate_textzone_with_sites(place, get_text_from_text_obj(place),
                                                                       one_item=one_site))
        place.bind("<KeyPress>", lambda _: validate_textzone_with_sites(place, get_text_from_text_obj(place),
                                                                        one_item=one_site))


class NotifyOptionsFrame(BaseOptions, Frame):
    def __init__(self, tk, *a, **k):
        super().__init__(tk, *a, **k)
        tk.geometry("500x112")
        Label(self, text="Уровень громкости уведомлений:").grid(column=1, row=1)
        radio_button_v = StringVar(self, get("volume", "1"))
        radio_button_values = {
            "Звук": "1",
            "Без звука": "2",
        }
        for index, values in enumerate(radio_button_values.items(), start=1):
            text, val = values
            radio_button = Radiobutton(self, text=text, value=val, variable=radio_button_v,
                                       command=lambda: self._toggle_checkbox(radio_button_v, "volume"))
            radio_button.grid(column=index, row=2)
        long_sound_var = IntVar(value=get("is_long_song", 1))
        cycle_task = IntVar(value=get("is_cycle_task", 0))
        Checkbutton(self, text="Звуковое уведомление ожидает действие пользователя",
                    variable=long_sound_var, command=lambda *_: self._toggle_checkbox(long_sound_var, "is_long_song"),
                    offvalue=0, onvalue=1).grid(column=1, row=3)
        Checkbutton(self, text="Запускать обратную проверку при срабатывании", variable=cycle_task, offvalue=0, onvalue=1,
                    command=lambda *_: self._toggle_checkbox(cycle_task, "is_cycle_task")).grid(column=1, row=4)
        Button(self, text="Настройки", command=lambda: change_frame(tk, self, OptionsFrame)).grid(column=1, row=5)
        Button(self, text="Главная", command=lambda: change_frame(tk, self, MainFrame)).grid(column=2, row=5)
