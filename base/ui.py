from tkinter import Tk
from base.storage import get
from base.frames import MainFrame, OptionsFrame
from base.tray import minimize


def handle_window_buttons(tk):
    """ Из-за функционала связанного с иконкой трея придётся изменить стандартное поведение кнопок [ _ [] X ] окна """
    tk.protocol("WM_DELETE_WINDOW", lambda: tk.withdraw())


base = Tk()
base.title("Детектор белых списков")
handle_window_buttons(base)


if __name__ == "__main__":
    if get("launch_h"):
        minimize(base, main_frame=MainFrame, options_frame=OptionsFrame)
    else:
        MainFrame(base).grid()
        base.eval('tk::PlaceWindow . center')
    base.mainloop()
