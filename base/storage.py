""" Документо-ориентированная база данных. """
import os
import json

FILE = os.path.join(os.getcwd(), "db.json")


def file_manager(mode="r+"):
    def manager(call):
        def action(key, value=None):
            if mode not in ("a+", "r+"):
                raise ValueError
            key, value = call(key, value)
            if not os.path.exists(FILE):
                open(FILE, "x").close()
                return value
            with open(FILE, mode, encoding="utf-8") as data:
                data.seek(0)
                raw = data.read()
                d = json.loads(raw) if raw else {}
                if mode == "a+":
                    data.truncate(0)
                    d.update({key: value})
                    data.write(json.dumps(d))
                    return
                return d.get(key, value)
        return action
    return manager


@file_manager()
def get(key: str, default=None):
    if type(key) is not str:
        raise TypeError
    if not key:
        raise ValueError
    return key, default


@file_manager(mode="a+")
def set_(key, value=None):
    if type(key) is not str:
        raise TypeError
    if not key:
        raise ValueError
    if value is not None:
        if not isinstance(value, (str, int, bool, float, tuple, list,)):
            raise TypeError
    return key, value
