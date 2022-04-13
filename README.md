# PDF Search Engine with Jina

This search engine will index a folder of PDF files, break them down into chunks, and then let you search using text or image for relevant chunks. In the frontend you'll see the returned chunks with a link to their associated PDF file.

## Run the example

1. Create a virtual environment
2. `pip install -r requirements.txt`

### Backend

1. `cd backend`
2. `python app.py -t index` to index your documents
3. `python app.py -t search` to open a RESTful search interface

### Frontend

1. `cd frontend`
2. `streamlit run frontend.py`

## Configure

- Backend: Settings are in `backend/config.py`
- Frontend: Settings are in `frontend/.streamlit/foo.toml` and `frontend/config.py`

## Deploy

`docker-compose up`

## Understand


