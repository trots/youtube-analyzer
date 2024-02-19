.venv\Scripts\python.exe -m nuitka --standalone --disable-console --include-package-data=googleapiclient --enable-plugin=pyside6 --windows-icon-from-ico=logo.png youtube-analyzer.py

copy logo.png youtube-analyzer.dist\logo.png

call compile_translations.bat
mkdir youtube-analyzer.dist\translations
copy translations\en.qm youtube-analyzer.dist\translations\en.qm
copy translations\ru.qm youtube-analyzer.dist\translations\ru.qm
