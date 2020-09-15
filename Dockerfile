# This Dockerfile is primarily supposed to run unit tests and
# generate the documentation of this python project within Gitlab-CE.
#
# However, you can also use it to run the actual code. This might be interesting
# if you want to seperate this project from your workstation and cannot use
# virtualenv. It might also be an option if you use Windows or some other
# environment such as Gitlab-CE.

# Docker quick reference:
# Build image: sudo docker build -t svek/pydda  .
# Run sth:     sudo docker run -it  svek/pydda bash
# Register for uploading: sudo docker login -- or cp /root/.docker/config.json from some machine
# Upload:      sudo docker push svek/pydda
# You can see the image then at https://hub.docker.com/u/svek

# Due to latex, this base image is huge (2GB)
# Use sphinxdoc/sphinx for a slimmer one. They both base on python:slim,
# which itself is based on debian:buster-slim.
FROM sphinxdoc/sphinx-latexpdf

# The following adds another 1GB of docker image layers. Well, that's docker!

RUN apt-get update && apt-get install -y --no-install-recommends \
     bash openssh-client curl make build-essential graphviz-dev python-pygraphviz pandoc librsvg2-bin imagemagick \
     && rm -rf /var/lib/apt/lists/*

WORKDIR /docs
ADD requirements.txt /docs
RUN pip3 install -r requirements.txt

