# copied directly from
# https://github.com/bcgov/cas-metabase/blob/develop/Dockerfile
#
FROM metabase/metabase:v0.41.4

RUN mkdir -p /home/metabase
COPY ./run_metabase.sh /app/run_metabase.sh
RUN chmod -R g+rwX /app /home/metabase
RUN chmod o+r /app/metabase.jar
ENV HOME=/app