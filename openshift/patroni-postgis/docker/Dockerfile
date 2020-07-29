FROM postgres:10

# Patroni install from https://github.com/zalando/patroni
# OpenShift config from https://github.com/BCDevOps/platform-services
# PostGIS install adapted from https://github.com/appropriate/docker-postgis
# PostGIS install further adapted from https://gist.github.com/stephenhillier/17bf0a7365f00c916d80733028f34ae9

ARG PGHOME=/home/postgres

ENV POSTGIS_MAJOR 3
ENV POSTGIS_VERSION 3.0.1+dfsg-4.pgdg90+1

RUN export DEBIAN_FRONTEND=noninteractive \
    && echo 'APT::Install-Recommends "0";\nAPT::Install-Suggests "0";' > /etc/apt/apt.conf.d/01norecommend \
    && apt-get update -y \
    && apt-get upgrade -y \
    && apt-cache depends patroni | sed -n -e 's/.* Depends: \(python3-.\+\)$/\1/p' \
    | grep -Ev '^python3-(sphinx|etcd|consul|kazoo|kubernetes)' \
    | xargs apt-get install -y gettext curl jq locales git python3-pip python3-wheel pgloader \
    && apt-cache showpkg postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
    && apt-get install -y --no-install-recommends \
    postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR=$POSTGIS_VERSION \
    postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts=$POSTGIS_VERSION \
    ## Make sure we have a en_US.UTF-8 locale available
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8 \
    && pip3 install setuptools \
    && pip3 install 'git+https://github.com/zalando/patroni.git#egg=patroni[kubernetes]' \
    && mkdir -p $PGHOME \
    && sed -i "s|/var/lib/postgresql.*|$PGHOME:/bin/bash|" /etc/passwd \
    # Set permissions for OpenShift
    && chmod 775 $PGHOME \
    && chmod 664 /etc/passwd \
    && mkdir -p $PGHOME/pgdata/pgroot \
    && chgrp -R 0 $PGHOME \
    && chown -R postgres $PGHOME \
    && chmod -R 775 $PGHOME \
    # Clean up
    && apt-get remove -y git python3-pip python3-wheel \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* /root/.cache

COPY contrib/root /

VOLUME /home/postgres/pgdata
EXPOSE 5432 8008
ENV LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
USER postgres
WORKDIR /home/postgres
CMD ["/bin/bash", "/usr/bin/entrypoint.sh"]