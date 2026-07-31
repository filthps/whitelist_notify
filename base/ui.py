from tkinter import Tk
from base.frames import MainFrame

base = Tk()
base.title("Детектор белых списков")
MainFrame(base)

if __name__ == "__main__":
    base.mainloop()
