FROM python:3
LABEL maintainer="Rogério <rsalmei@gmail.com>"

WORKDIR /usr/src/clearly

COPY . .
RUN pip install --no-cache-dir -e .

ENV BROKER_CONNECT_TIMEOUT 5
ENV CLI_DISPLAY_MODES ?

EXPOSE 12223

# clearly is already installed, the workdir doesn't really matter anymore.
# but in client, the REPL autocomplete works better if there isn't other
# "clearlys" to suggest, like the source dir or the egg-info.
WORKDIR /

ENTRYPOINT ["clearly"]
