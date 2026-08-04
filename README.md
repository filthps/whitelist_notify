# whitelist_notify

Системные оповещения относительно введения или снятия белых списков для windows.

---
*Python 3.11*

1) create venv
2) <code>pip install -r requirements.txt</code>
3) <code> pyinstaller base/ui.py base/*.py --add-data "base/db.json:base/" --add-data "base/images/tray.png:base/images/" --add-data "base/images/wl-off.png:base/images/" --add-data "base/images/wl-on.png:base/images/"  --onefile --noconsole </code>

В полученной папке dist появится <code>.exe</code> для запуска.
