FROM ubuntu:20.04

# Get apache
RUN apt-get -y update &&  DEBIAN_FRONTEND="noninteractive" apt-get -y install apache2 \
    apache2-bin apache2-utils

# Get mapserver
RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install cgi-mapserver \
    mapserver-bin mapserver-doc libmapscript-perl\
    libapache2-mod-fcgid

RUN sed -i 's/80/8080/g' /etc/apache2/ports.conf

COPY mapserver.conf /etc/apache2/sites-available/000-default.conf
RUN a2ensite 000-default.conf

RUN a2enmod cgi fcgid headers
RUN service apache2 restart

# COPY sigh.map /etc/mapserver/mapserver.map

EXPOSE 8080

# RUN chown -R 1001:0 /var/log/apache2
# RUN chown -R 1001:0 /var/run/apache2
# RUN chown -R 1001:0 /var/lib/apache2

RUN chmod -R a+rwx /var/run/apache2
RUN chmod -R a+rwx /var/log/apache2
RUN chmod -R a+rwx /var/lib/apache2

RUN ln -sf /proc/$$/fd/1 /var/log/apache2/access.log
RUN ln -sf /proc/$$/fd/2 /var/log/apache2/error.log
# RUN ln -sf /proc/$$/fd/1 /var/log/apache2/other_vhosts_access.log

USER 1001

CMD apache2ctl -D FOREGROUND