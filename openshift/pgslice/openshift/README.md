Create new build with: `oc -n e1e498-tools process -f build.yaml -p VERSION=05-11-2024 | oc -n e1e498-tools apply -f -`
Start new build with: `oc -n e1e498-tools start-build pgslice --follow`
