from tkinter import Tk
from base.storage import get, set_
from base.frames import MainFrame
from base.tray import minimize

base = Tk()
base.title("Детектор белых списков")

if __name__ == "__main__":
    set_("active_task", False)
    frame = MainFrame(base)
    frame.grid()
    if get("launch_h"):
        minimize(base, reload_menu=False)
    else:
        base.eval('tk::PlaceWindow . center')
    base.mainloop()
