FROM centos/postgresql-12-centos7

USER root

RUN yum -y --enablerepo=extras install epel-release &&\
    yum -y --enablerepo=epel install s3cmd

USER 26

COPY backup_to_s3.sh .

CMD sh backup_to_s3.sh