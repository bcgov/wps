## Getting Started

You will need an environment file. See: `.env.example`. Contact current maintainers for current variable settings.

### Installing

- Automated (mac only):
  - Run `setup/mac.sh` in parent folder
  - Follow [lima setup steps](../setup/LIMA.md)
  - then run `poetry_setup.sh`
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
