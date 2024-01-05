FROM python:3.9

WORKDIR .

COPY . .

RUN pip install poetry
RUN poetry install

ENV LANGSERVE_HOST=0.0.0.0
EXPOSE 8001

CMD ["poetry", "run", "python", "langserver.py"]
