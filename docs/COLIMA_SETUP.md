# Running Docker with Colima on macOS

[Colima](https://github.com/abiosoft/colima) provides a Docker-compatible runtime on
macOS without Docker Desktop. It is the recommended option for running WPS's local
object-store sidecar on Apple silicon.

## Install or update the tooling

Install Colima, the Docker CLI, and Docker Compose with Homebrew:

```bash
brew install colima docker docker-compose
```

If they are already installed, update them with:

```bash
brew upgrade colima docker docker-compose
```

Homebrew installs Docker Compose as a CLI plugin. Merge the following property into
`~/.docker/config.json` so the Docker CLI can discover it. Preserve any other existing
properties in that file.

```json
{
  "cliPluginsExtraDirs": [
    "/opt/homebrew/lib/docker/cli-plugins"
  ]
}
```

The path above is Homebrew's default on Apple silicon. Run `brew --prefix` and replace
`/opt/homebrew` with the returned path if Homebrew is installed elsewhere.

## Start Colima

For the standalone SeaweedFS object store, a small VM is sufficient:

```bash
colima start \
  --cpu 2 \
  --memory 4 \
  --disk 60 \
  --vm-type vz
```

If experimenting with the currently unsupported complete WPS Docker Compose stack, use
more resources:

```bash
colima start \
  --cpu 4 \
  --memory 8 \
  --disk 60 \
  --vm-type vz
```

Colima remembers these settings, so subsequent starts only require:

```bash
colima start
```

With the `vz` VM type, Colima selects the `virtiofs` mount type automatically. The
SeaweedFS image supports Apple silicon, so `--vz-rosetta` is not needed. Add Rosetta
only when another required image reports that it has no `linux/arm64` manifest.

## Verify Docker

Confirm that Docker Compose is installed and the Colima daemon is active:

```bash
docker compose version
docker context ls
docker info
```

The active context should be `colima`. If it is not, select it explicitly:

```bash
docker context use colima
```

## Run the WPS local object store

From the repository root, start SeaweedFS and create the local application buckets:

```bash
make local-object-store-up
```

See [Manual Setup](MANUAL_SETUP.md#local-object-storage) for the contributor environment
file and Weather Toolkit data-generation steps.

Stop the object store while preserving its data:

```bash
make local-object-store-down
```

Stop the Colima VM when it is no longer needed:

```bash
colima stop
```

To deliberately delete the local object-store volume and recreate empty buckets, run:

```bash
make local-object-store-reset
```

## Troubleshooting

If `docker compose` is not recognized, confirm that `docker-compose` is installed with
Homebrew and that `cliPluginsExtraDirs` points to Homebrew's `lib/docker/cli-plugins`
directory.

If Docker cannot connect to a daemon, start Colima and select its Docker context:

```bash
colima start
docker context use colima
```

## References

- [Colima releases](https://github.com/abiosoft/colima/releases)
- [Colima default configuration](https://github.com/abiosoft/colima/blob/main/embedded/defaults/colima.yaml)
- [Homebrew Docker Compose formula](https://formulae.brew.sh/formula/docker-compose)
