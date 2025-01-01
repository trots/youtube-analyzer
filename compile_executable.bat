.venv\Scripts\pyinstaller.exe --windowed --icon=logo.png youtube-analyzer.py
copy logo.png dist\youtube-analyzer\logo.png

call compile_translations.bat
mkdir dist\youtube-analyzer\translations
copy translations\ru.qm dist\youtube-analyzer\translations\ru.qm
