FROM python:3.7
LABEL maintainer "Jack Laxson <jack@getpizza.cat>"

RUN mkdir -p /usr/src/clearly /usr/share/cache/ && \
        chmod 777 /usr/share/cache/

COPY Pipfile Pipfile.lock /usr/src/clearly/

ENV XDG_CACHE_HOME /usr/share/cache/

WORKDIR /usr/src/clearly/

RUN pip install pipenv==2018.10.13

COPY . /usr/src/clearly/

RUN pipenv sync -d

EXPOSE 12223

CMD ["pipenv", "run", "clearly"]