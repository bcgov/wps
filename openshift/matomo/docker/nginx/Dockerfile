FROM nginx:stable

# Required for HTTP Basic feature
RUN apt-get update -y && \
  apt-get install -y openssl ca-certificates && \
  rm -rf /var/lib/apt/lists/*

# support running as arbitrary user which belogs to the root group
RUN chmod g+rwx /var/cache/nginx /var/run /var/log/nginx

# users are not allowed to listen on priviliged ports
RUN sed -i.bak 's/listen\(.*\)80;/listen 8080;/' /etc/nginx/conf.d/default.conf

# Copy config from source to container
ADD docker/nginx/nginx.conf /etc/nginx/

EXPOSE 8080