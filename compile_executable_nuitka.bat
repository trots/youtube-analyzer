.venv\Scripts\python.exe -m nuitka^
    --standalone^
    --windows-console-mode=disable^
    --include-package-data=googleapiclient^
    --enable-plugin=pyside6^
    --include-module=PySide6.support.deprecated^
    --windows-icon-from-ico=logo.png^
    --output-filename=youtube-analyzer^
    --include-package=youtubeanalyzer^
    --include-package=plugins^
    youtubeanalyzer/__main__.py

.venv\Scripts\python.exe -m nuitka^
    --module plugins/autocomplete_plugin/autocomplete_plugin.py^
    --output-dir=__main__.dist/plugins

copy logo.png __main__.dist\logo.png

call compile_translations.bat
mkdir __main__.dist\translations
copy translations\ru.qm __main__.dist\translations\ru.qm
copy translations\autocomplete_plugin_ru.qm __main__.dist\translations\autocomplete_plugin_ru.qm
