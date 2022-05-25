# PDF Search Engine with Jina

This search engine will index a folder of PDF files, break them down into chunks, and then let you search using text for relevant chunks. In the frontend you'll see the returned chunks with a link to their associated PDF file.

Bear in mind this is a **work in progress**

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

- Settings are in `config.yml`
- Additional frontend settings are in `frontend/.streamlit/config.toml`

## Deploy

`docker-compose up`

## Test

If you're planning to use "Print to PDF" from your web browser for testing, I recommend using Chrome over Firefox. Firefox converts characters strangely (for example `fi` becomes `ﬁ`) which *could* affect search results depending on what the encoder recognizes as a meaningful unit.

## TODO

Feel free to make a PR to help out with these!

- [ ] Test image display in frontend
- [ ] Embed original image as `datauri` when indexing images
- [ ] Single restful endpoint for both indexing and search
- [ ] Working `docker-compose.yml`
