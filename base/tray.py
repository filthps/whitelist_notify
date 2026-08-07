import os
from typing import Optional
from pystray import Icon, Menu, MenuItem
from PIL import Image
from base.main import IMAGES_PATH

icon: Optional[Icon] = None


def minimize(tk, reload_menu=True, options_disabled=False):
    tk.withdraw()
    create_icon_or_update(tk, reload_menu=reload_menu, options_disabled=options_disabled, create_icon=True)


def open_from_tray(tk, new_frame=None):
    tk.deiconify()
    if new_frame is not None:
        [any_children.destroy() for any_children in tk.winfo_children()]
        new_frame(tk).grid()
    tk.mainloop()


def close_app(tk, icon):
    icon.stop()
    tk.destroy()


def create_icon_or_update(tk, create_icon=True, options_disabled=False, reload_menu=False) -> Icon:
    """ Создать иконку в трее или изменить меню иконки трея
     ВНИМАНИЕ: метод run почему-то блокирует дольнейшее выполнение кода в потоке,
     поэтому вызывать данный метод всегда последним, ибо после строки вызова этой функции - ничего выполнено не будет!
      """
    from base.frames import OptionsFrame
    global icon
    if icon is None:
        if create_icon:
            menu = Menu(
                MenuItem("Открыть", lambda: open_from_tray(tk), default=True),
                MenuItem("Настройки", lambda: open_from_tray(tk, new_frame=OptionsFrame),
                         enabled=not options_disabled),
                MenuItem("Выход", lambda: close_app(tk, icon))
            )
            image = Image.open(os.path.join(IMAGES_PATH, "tray.png"))
            image.resize((10, 10,), Image.NEAREST)
            icon = Icon("Детектор белых списков", icon=image, title="Детектор белых списков", menu=menu)
            icon.run()
        return
    if reload_menu:
        icon.menu = Menu(
            MenuItem("Открыть", lambda: open_from_tray(tk), default=True),
            MenuItem("Настройки", lambda: open_from_tray(tk, new_frame=OptionsFrame),
                     enabled=not options_disabled),
            MenuItem("Выход", lambda: close_app(tk, icon))
        )
        icon.update_menu()
