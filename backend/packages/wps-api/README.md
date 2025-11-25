## Getting Started

You will need an environment file. See: `.env.example`. Contact current maintainers for current variable settings.

### Installing

- Automated (mac only):
  - Run `setup/mac.sh` in parent folder
  - Follow [manual setup](../docs/MANUAL_SETUP.md) for database setup notes as of Nov 2024.
  - Follow [lima setup steps](../setup/LIMA.md)
  - then add run `eval "$(pyenv init -)"` in your current shell and add it to your `rc` or `zshrc` file
  - then run `poetry-workspaces-setup.sh` from the root of the wps project
  - Follow [vsc setup steps](../setup/VSC.md)
- Manual (linux): See [manual setup](../docs/MANUAL_SETUP.md).
  Note: you may want to alias `python3` as `python` in your profile

### Running

Assumes:

- Installation section above is completed
- `.env` is correctly configured in the project root
- this dynamic library is set in the env: `DYLD_LIBRARY_PATH=/Library/Frameworks/R.framework/Resources/lib`

Installing:

````
cd wps/backend
uv sync --all-extras
```


Run API with:

```bash
uv run --package wps-api python -m app.main
````

### Testing

Code must pass all unit tests.

```bash
uv run pytest
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
