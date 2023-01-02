# wps-tileserver

Vector tile server setup for the Wildfire Predictive Services Unit

## Overview

The intention of this module is to build/configure/deploy a postgis and pg_tileserv deployment with nginx caching

### Components

- postgis database server (crunchydb) - backing data store
- pg_tileserv - serves up vector tiles from postgis server.
- proxy server (nginx) - caches pg_tileserv responses.

### Reference

https://github.com/bcgov/wps-vector-tileserver (lots of code pulled and reused from here)
https://blog.crunchydata.com/blog/production-postgis-vector-tiles-caching
https://github.com/CrunchyData/pg_tileserv

## Local development

### Natively

- Create a new `pyenv` within the `tileserv` module with `poetry shell`
- Run `poetry install`
- Create a `tileserv` db locally with user `tileserv` and password `tileserv`
- Run migrations with `poetry run alembic upgrade head`
  Note: No official arm build for `pg_tileserv`, but and image can be pulled from `docker pull pramsey/pg_tileserv`

### Docker

- Build with `docker build . -t pg_tileserv`
- Run with `docker run -dit -e DATABASE_URL=postgresql://tileserv:tileserv@host.docker.internal/tileserv pg_tileserv`
  Note: May not run with mac m1 machines since `pg_tileserv` is only built for platform `linux/amd64`

### Nginx build

- Shouldn't need to be built often besides updates
- Make any changes then run `oc -n e1e498-tools start-build nginx-tileserv --from-dir .` while in this folder

## Deployment

See `deploy-tileserv` job defined in `.github/workflows/deployment.yml`
