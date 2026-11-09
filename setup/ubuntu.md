# Ubuntu development setup

Use this guide with the Ubuntu release supported by the setup script, either
natively or in WSL 2.

You need a Bash terminal, a normal Linux user with sudo access, and an existing
WPS checkout. From the repository root, run the setup script:

```bash
bash setup/ubuntu.sh
```

The script requires systemd to start PostgreSQL and Redis. If systemd is disabled
in WSL, follow [Microsoft's systemd instructions](https://learn.microsoft.com/en-us/windows/wsl/systemd)
before running setup.

**Local development only:** the script creates a PostgreSQL superuser named `wps`
with password `wps`. It retains existing database contents but resets the `wps`
role/password. Do not run it on production or shared database servers.

The script installs the system and project dependencies for the backend and
frontend. It displays colored progress banners and writes detailed output to a
private log file. The log path appears at startup and completion.

## Finish setup in the current terminal

After the script completes, run:

```bash
exec bash -l
```

This replaces the current shell with a Bash login shell and loads the configured
tools. Save or finish running work first, since shell-local settings are lost and
background jobs may be disrupted.

**Stopping point:** if you only need a local checkout and installed tools to
contribute to GitHub, setup is complete. Continue below only to run the application
in developer testing mode.

## Developer testing mode

Application environment settings, secrets, and development data are not supplied
by setup. Arrange these with an internal developer before proceeding. The shared
[manual setup guide](../docs/MANUAL_SETUP.md) describes the environment and database
steps. For running the applications, see the [API guide](../backend/packages/wps-api/README.md)
and [web guide](../web/README.md).

## Troubleshooting

- **Setup fails:** review the error and log path printed by the script. Check log
  lines for sensitive information before sharing them with a developer, then
  correct the reported issue and rerun setup.
- **uv, Node, or Yarn is not found after setup:** run `exec bash -l` in the same
  Ubuntu distribution. If the problem persists, share the setup output and
  shell-profile configuration with a developer. Do not replace PATH with a value
  that omits Ubuntu's system directories.
- **PostgreSQL or Redis fails to start in WSL:** if you use multiple WSL distros,
  terminate the others and rerun setup in this distro. They may be using the same
  localhost ports.
