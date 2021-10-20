FROM centos/postgresql-12-centos7

# Download the installer
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip

# Switch to root user for package installs
USER root
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

RUN yum install -y python3
# RUN yum install -y python-is-python3
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | POETRY_HOME=/opt/poetry python3 && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install

# we're trying out the official aws s3 tool right now, but should there be any issues, we could
# try s3cmd:
# RUN yum -y --enablerepo=extras install epel-release &&\
# yum -y --enablerepo=epel install s3cmd

# Switch back to default user
USER 26

COPY backup_to_s3.sh .
COPY cleanup_bucket.sh .

CMD sh backup_to_s3.sh