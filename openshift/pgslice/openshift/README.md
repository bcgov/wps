# pgslice partitioning image

Uses https://hub.docker.com/r/ankane/pgslice to run the pgslice commands
Runs `fill`, `analyze` and `swap` for a newly partitioned table where the original has data, to fill the partitions with existing data.

## Building

### Create a new build

```bash
`oc -n e1e498-tools process -f build.yaml -p VERSION=05-11-2024 | oc -n e1e498-tools apply -f -`
```

### Kick off a new build

```bash
oc -n e1e498-tools start-build pgslice --follow
```
