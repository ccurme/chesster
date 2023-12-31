FROM base_image:latest

EXPOSE 8000

ENV LANGSERVE_HOST=langserver
CMD ["poetry", "run", "uvicorn", "chesster.app.app:app", "--host", "0.0.0.0", "--port", "8000"]
