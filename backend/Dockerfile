FROM jinaai/jina:3.3.10-py39-standard

# setup the workspace
COPY . /workspace
WORKDIR /workspace

RUN apt-get update && apt-get install --no-install-recommends -y git build-essential g++

ENTRYPOINT ["python", "app.py", "-t", "search"]

EXPOSE 12345
