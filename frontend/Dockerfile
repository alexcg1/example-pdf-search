FROM jinaai/jina:3.3.10-py39-standard

COPY . /workspace
WORKDIR /workspace

RUN pip install streamlit==1.8.1

EXPOSE 8512

ENTRYPOINT ["streamlit", "run"]
CMD ["frontend.py"]
