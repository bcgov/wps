FROM centos/postgresql-12-centos7

USER root

ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

# we're trying out the official aws s3 tool right now, but should there be any issues, we could
# try s3cmd:
# RUN yum -y --enablerepo=extras install epel-release &&\
# yum -y --enablerepo=epel install s3cmd

USER 26

COPY backup_to_s3.sh .

CMD sh backup_to_s3.sh