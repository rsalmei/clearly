FROM python:3
LABEL maintainer="Rogério <rsalmei@gmail.com>"

WORKDIR /usr/src/clearly

COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 12223

ENTRYPOINT [ "clearly"]
