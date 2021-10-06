FROM centos/postgresql-12-centos7

USER root

ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

USER 26

COPY backup_to_s3.sh .

CMD sh backup_to_s3.sh