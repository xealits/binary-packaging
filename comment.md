Let's consider 2 packages: `d` and `s`.
And `d` depends on the package `s`.
Some module in `d` literally loads stuff from `s` with:

    from s import foo

Apparently, loading it depends on where the current working directory of interpreter is.

And, as tests show, really nothing default (without changing the code in d itself)
can make it load `s` from the package's own directory.
Everything is loaded with respect to current interpreter session -- pythonpath, sys.path its' working directory etc.
(So, dynamic scoping instead of lexical.)

Thus, the first idea does not apply to Python...


# Interpreter session based packaging

Итак с созданием окружения для пакетов неудача.
Питон грузит всё динамически, всё в сессии интерпретатора.
Нужно создавать окружение не для пакета, а для интерпретатора

* Надо проверить откуда втягиваются `.so` файлы для `ctypes`.

* И раз импорт завязан на интерпретатор, мб стоит делать модуль для пакетов в самом питоне?
  Затем как-то расширить его на баш а-ля `virtualenv`.

