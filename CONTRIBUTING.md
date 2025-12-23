# How to contribute to YouTube Analyzer

## Reporting bugs

1. Check the [Issues](https://github.com/trots/youtube-analyzer/issues) to see if the bug has already been reported.

2. Create a new issue.

3. Include:
    - Clear description of the problem
    - Steps to reproduce
    - Expected vs. actual behavior
    - Screenshots (if applicable)
    - System information (OS, Python version, PySide6 version)

## Making code contributions

Open a new GitHub pull request with the changes to the `develop` branch.

- Follow our coding standards (see below)
- Write or update tests as needed
- Update documentation (README) if required

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code
- Use Python 3.* syntax only
- Avoid complex code
- Max line length is 127

See also [flake8 rules](https://github.com/trots/youtube-analyzer/blob/master/.github/workflows/python-app.yml) on CI/CD.

## Project Structure

```text
youtube-analyzer/
├── doc/                           # Documentation
├── plugins/                       # Internal plugins
├── tests/                         # Auto tests
├── translations/                  # UI translation ts-files
├── youtubeanalyzer/               # Source code
├── compile_executable_nuitka.bat  # Build distribution package
├── compile_translations.bat       # Compile qm-files
├── CONTRIBUTING.md                # This file
├── coverage.bat                   # Run auto test with coverage analysis
├── LICENSE                        # License agreement
├── logo.xcf                       # Logo image Gimp project
├── logo.png                       # Logo image
├── requirements.txt               # Dependencies
├── update_translations.bat        # Update ts-files from source code
├── youtube-analyzer.iss           # InnoSetup project file
└── README.md
```

## License

By contributing, you agree that your contributions will be licensed under the project's [LICENSE](https://github.com/trots/youtube-analyzer/blob/master/LICENSE) file.

Thank you for contributing!
