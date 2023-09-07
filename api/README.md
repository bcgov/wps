## Getting Started

You will need an environment file. See: `.env.example`. Contact current maintainers for current variable settings.

### Installing

- Automated (mac only):
  - Run `setup/mac.sh` in parent folder
  - Follow [lima setup steps](../setup/LIMA.md)
  - then add run `eval "$(pyenv init -)"` in your current shell and add it to your `rc` file
  - then run `poetry_setup.sh`
  - then activate the virtual environment with `poetry shell`
  - then run:
    - python -m pip install gdal==$(gdal-config --version)
    - pip install greenlet
  - Follow [vsc setup steps](../setup/VSC.md)
- Manual (linux): See [manual setup](../docs/MANUAL_SETUP.md).
  Note: you may want to alias `python3` as `python` in your profile

### Running

Assumes:

- Installation section above is completed
- `app/.env` is correctly configured

Run API with:

```bash
make run
```

### Testing

Code must pass all unit tests.

```bash
make test
```

Or run continuously with pytest-testmon and pytest-watch (`ptw --runner "pytest --testmon"` or `ptw -- --testmon`):

```bash
make test-watch
```

### Troubleshooting

**Poetry can't install rpy2**
Error: `ld: library not found for -lpcre2-8`

pcre2 should be installed after running [mac.sh](../setup/mac.sh). This can be verified by running

```bash
brew list pcre2
```

This issue can be resolved by running the following command before `poetry_setup.sh`: (adjust path as necessary)

```bash
export LIBRARY_PATH="/opt/homebrew/Cellar/pcre2/10.42/lib/:$LIBRARY_PATH"
```
