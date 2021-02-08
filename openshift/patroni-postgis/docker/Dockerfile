FROM postgres:11
LABEL maintainer="WPS Project - https://github.com/bcgov/wps"
ENV PATRONI_VERSION=1.6.5
ENV LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
ENV PATRONI_HOME=/opt/patroni

# # Credit:
# # Patroni adapted from https://github.com/zalando/patroni (Alexander Kukushkin <alexander.kukushkin@zalando.de>)
# # OpenShift adapted from https://github.com/BCDevOps/platform-services
# # PostGIS adapted from https://github.com/appropriate/docker-postgis
# # PostGIS install further adapted from https://gist.github.com/stephenhillier/17bf0a7365f00c916d80733028f34ae9

# ENV POSTGIS_MAJOR 3
# ENV POSTGIS_VERSION 3.1.1+dfsg-1.pgdg90+1

# RUN apt-get update -y \
#     && apt-cache showpkg postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
#     && apt-get install -y --no-install-recommends \
#     postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR=$POSTGIS_VERSION \
#     postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts=$POSTGIS_VERSION

ARG PGHOME=/home/postgres

RUN export DEBIAN_FRONTEND=noninteractive \
    && set -x \
    && echo 'APT::Install-Recommends "0";\nAPT::Install-Suggests "0";' > /etc/apt/apt.conf.d/01norecommend \
    && apt-get update -y \
    && apt-get install -y curl jq locales git build-essential python3 python3-dev python3-pip python3-wheel python3-setuptools python3-virtualenv \
    && echo 'Make sure we have a en_US.UTF-8 locale available' \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 \
    && pip3 --isolated --no-cache-dir install psycopg2-binary \
    && pip3 --isolated --no-cache-dir install "patroni[kubernetes]==${PATRONI_VERSION}" \
    && PGHOME=/home/postgres \
    && mkdir -p $PGHOME \
    && sed -i "s|/var/lib/postgresql.*|$PGHOME:/bin/bash|" /etc/passwd \
    && echo 'Setting permissions for OpenShift' \
    && chmod 664 /etc/passwd \
    && mkdir -p $PGHOME/pgdata/pgroot \
    && chgrp -R 0 $PGHOME \
    && chown -R postgres $PGHOME \
    && chmod -R 775 $PGHOME \
    && echo 'Cleaning up' \
    && apt-get remove -y git build-essential python3-dev python3-pip python3-wheel python3-setuptools \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache

COPY contrib/root /

VOLUME /home/postgres/pgdata
EXPOSE 5432 8008
USER postgres
WORKDIR /home/postgres
CMD ["/bin/bash", "/usr/bin/entrypoint.sh"]
