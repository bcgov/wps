## Coding conventions

Code must be [PEP8](https://www.python.org/dev/peps/pep-0008/) compliant with the exception of allowing for line lengths up to 110 characters.
Compliance is enforced using [ruff](https://docs.astral.sh/ruff/), configured in [ruff.toml](../ruff.toml).

Run ruff to check that your code conforms before pushing code to the repository:

```bash
cd backend
uv run ruff check packages/wps-api/src packages/wps-shared/src packages/wps-jobs/src
```

This is the same check that runs in CI — see the `lint-api` job in
[.github/workflows/integration.yml](../.github/workflows/integration.yml).

### Branch naming conventions

Branches must be named in accordance with the rules specified in [.githooks/pre-push](../.githooks/pre-push).

- branch names should be informative, meaningful and concise.
- branch names should follow the pattern (category)/(description)/(ticket number)

```
# Enforce branch naming conventions for this project using git hooks.
git config core.hooksPath .githooks
```

example of a good branch name:

```
# Task related to re-factoring of logging, the ticket number being 123:
task/re-factor-logging/123
```

example of a bad branch name:

```
wps-123
```
