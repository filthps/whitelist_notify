import os
import winreg

KEY_NAME = "wl_detector"
PACKAGE = ["dist", "ui.exe"]


def autostart(state=False):
    """ Изменить запись в реестре Windows
        :arg state: True добавить в автозагрузку, False удалить из автозагрузки
     """
    app = os.path.dirname(os.path.abspath(__file__))
    app = os.path.join(app, os.path.sep.join(PACKAGE))
    reg = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                         winreg.KEY_SET_VALUE)
    if state:
        winreg.SetValueEx(reg, KEY_NAME, 0, winreg.REG_SZ, app)
    else:
        winreg.DeleteKey(reg, app)
    winreg.CloseKey(reg)
