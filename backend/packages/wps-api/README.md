Assumes installation and setup is done in [backend/README.md](../../../backend/README.md)

Run API with:

```bash
uv run --package wps-api python -m app.main
```

### Testing

Code must pass all unit tests.

```bash
uv run pytest
```

### Troubleshooting

**Poetry can't install rpy2**
Error: `ld: library not found for -lpcre2-8`

pcre2 should be installed after running [mac.sh](../../../setup/mac.sh). This can be verified by running

```bash
brew list pcre2
```

```bash
export LIBRARY_PATH="/opt/homebrew/Cellar/pcre2/10.42/lib/:$LIBRARY_PATH"
```
