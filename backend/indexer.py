from jina import Client
from config import HOST, NUM_DOCS, DATA_DIR
from docarray import DocumentArray
import click

client = Client(host=HOST)


def index(docs):
    # client.index(docs)
    client.post("/index", docs)


def prep_docs(directory: str, num_docs: int):
    docs = DocumentArray.from_files(f"{directory}/*.pdf", recursive=True, size=num_docs)

    return docs


@click.command()
@click.option(
    "--task",
    "-t",
    type=click.Choice(["index"], case_sensitive=False),
)
@click.option("--num_docs", "-n", default=NUM_DOCS)
@click.option("--data_dir", "-d", default=DATA_DIR)
def main(task: str, num_docs, data_dir):
    if task == "index":
        docs = prep_docs(directory=data_dir, num_docs=num_docs)
        index(docs)
    else:
        print("Please add '-t index' or '-t search' to your command")


if __name__ == "__main__":
    main()
