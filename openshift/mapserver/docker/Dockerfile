FROM ubuntu:20.04

# Get apache
RUN apt-get -y update &&  DEBIAN_FRONTEND="noninteractive" apt-get -y install apache2 \
    apache2-bin apache2-utils

# Get mapserver
RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install cgi-mapserver \
    mapserver-bin mapserver-doc libmapscript-perl\
    libapache2-mod-fcgid

COPY mapserver.conf /etc/apache2/sites-available/000-default.conf
RUN a2ensite 000-default.conf

RUN a2enmod cgi fcgid headers
RUN service apache2 restart

# COPY sigh.map /etc/mapserver/mapserver.map

EXPOSE 80
CMD apache2ctl -D FOREGROUND