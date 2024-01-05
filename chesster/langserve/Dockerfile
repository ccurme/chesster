FROM python:3.9

WORKDIR /chesster

COPY . /chesster

RUN pip install poetry
RUN poetry install

EXPOSE 8001

CMD ["poetry", "run", "python", "chesster/langserve/langserver.py"]
