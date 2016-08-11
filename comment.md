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




# Name of the program

"Content packager"?
("As easy as copy" like.)





# Задача, в линуксовых ELF бинарниках и в питоне

Зависимость: "что-где" ("что-как") пара.
Линковщик/процедура разбора зависимостей в линуксе и в питоне.
"Общая задача" (на сколько возможно) и реализации в процедурах линукса и питона.





# Требования

* полное окружение зависимостей и корректный разбор при простом копировании всех бинарников в 1 директорию

* простая и доступная работа в локальном пространстве юзера, без привилегий

* поддержка разных версий пакетов/бинарников в хранилище менеджера пакетов (хеши содержимого)

* сборка окружений из доступных пакетов ссылками/наиболее лёгким методом, поменьше копирования,
  т.е. по возможности символьными ссылками, так как они могут указывать на разные девайсы/файловые системы

* зависимость от наличия некоего простого файла? (разбор пересечений таких зависимостей?)

* интерфейс-ссылка в собранный граф зависимостей

* рабочее пространство (build/dev)


