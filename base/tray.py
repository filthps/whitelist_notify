import sys
import os
from pystray import Icon, Menu, MenuItem
from PIL import Image
from base.main import IMAGES_PATH


def minimize(tk, **kwargs):
    icon = create_icon(tk, **kwargs)
    icon.run()
    tk.withdraw()


def open_from_tray(tk, frame):
    frame = frame(tk)
    frame.grid()
    tk.eval('tk::PlaceWindow . center')
    tk.mainloop()


def close_app(tk, icon):
    icon.stop()
    tk.destroy()
    sys.exit()


def create_icon(tk, main_frame=None, options_frame=None) -> Icon:
    menu = Menu(
        MenuItem("Открыть", lambda: open_from_tray(tk, main_frame), default=True),
        MenuItem("Настройки", lambda: open_from_tray(tk, options_frame)),
        MenuItem("Выход", lambda: close_app(tk, icon))
    )
    image = Image.open(os.path.join(IMAGES_PATH, "tray.png"))
    image.resize((10, 10,), Image.NEAREST)
    icon = Icon("Детектор белых списков", icon=image, title="Детектор белых списков", menu=menu)
    return icon
