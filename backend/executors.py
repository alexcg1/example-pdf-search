from config import METADATA_DIR
from jina import Executor, requests
import pikepdf
import subprocess
import os
import re
from dateutil.tz import tzutc, tzoffset
import datetime

pdf_date_pattern = re.compile(
    "".join(
        [
            r"(D:)?",
            r"(?P<year>\d\d\d\d)",
            r"(?P<month>\d\d)",
            r"(?P<day>\d\d)",
            r"(?P<hour>\d\d)",
            r"(?P<minute>\d\d)",
            r"(?P<second>\d\d)",
            r"(?P<tz_offset>[+-zZ])?",
            r"(?P<tz_hour>\d\d)?",
            r"'?(?P<tz_minute>\d\d)?'?",
        ]
    )
)


def transform_date(date_str):
    """
    Convert a pdf date such as "D:20120321183444+07'00'" into a usable datetime
    http://www.verypdf.com/pdfinfoeditor/pdf-date-format.htm
    (D:YYYYMMDDHHmmSSOHH'mm')
    :param date_str: pdf date string
    :return: datetime object
    """
    global pdf_date_pattern
    match = re.match(pdf_date_pattern, date_str)
    if match:
        date_info = match.groupdict()

        for k, v in date_info.items():  # transform values
            if v is None:
                pass
            elif k == "tz_offset":
                date_info[k] = v.lower()  # so we can treat Z as z
            else:
                date_info[k] = int(v)

        if date_info["tz_offset"] in ("z", None):  # UTC
            date_info["tzinfo"] = tzutc()
        else:
            multiplier = 1 if date_info["tz_offset"] == "+" else -1
            date_info["tzinfo"] = tzoffset(
                None,
                multiplier
                * (3600 * date_info["tz_hour"] + 60 * date_info["tz_minute"]),
            )

        for k in ("tz_offset", "tz_hour", "tz_minute"):  # no longer needed
            del date_info[k]

        return datetime.datetime(**date_info)

def uri_to_title(uri):
    title = uri.split(".")[-2].split("/")[-1]

    return title


class PdfPreprocessor(Executor):
    """
    - Generates cover and stores uri in tag
    - Converts PDF to blob
    - Gets PDF metadata, stores as Document metadata (todo)
    """

    @requests(on="/index")
    def preprocess_pdf(self, docs, **kwargs):
        covers_dir = f"{METADATA_DIR}/covers"
        if not os.path.isdir(covers_dir):
            os.makedirs(covers_dir)

        for doc in docs:
            # Load to blob
            if doc.uri:
                doc.load_uri_to_blob()

            # Extract PDF metadata to doc.tags
            if "metadata" not in doc.tags.keys():
                doc.tags["metadata"] = {}

            pdf = pikepdf.Pdf.open(doc.uri)
            doc_info = dict(pdf.docinfo)
            for key, value in doc_info.items():
                new_key_name = str(key).lower()[1:]
                doc.tags["metadata"][new_key_name] = str(value)

            # Convert weird PDF date to real date time
            datetime_keys = ["moddate", "creationdate"]
            for key, value in doc.tags["metadata"].items():
                if key in datetime_keys:
                    doc.tags["metadata"][key] = str(transform_date(value))

            if "title" not in doc.tags["metadata"].keys():
                # Convert doc.uri to readable title
                doc.tags["metadata"]["title"] = (
                    uri_to_title(doc.uri)
                )

            # Create cover image
            bare_filename = doc.uri.split("/")[-1]
            thumbnail_filename = f"{covers_dir}/{bare_filename}.png"
            subprocess.call(["convert", doc.uri + "[0]", thumbnail_filename])
            doc.tags["cover"] = thumbnail_filename


class RecurseTags(Executor):
    """
    Bubble Document tags to doc.chunk["parent"] dict
    """

    @requests(on="/index")
    def copy_doc_tags_to_chunk_tags(self, docs, **kwargs):
        for doc in docs:
            for chunk in doc.chunks["@c, cc, ccc"]:
                if not "parent" in chunk.tags:
                    chunk.tags["parent"] = doc.tags
                    chunk.tags["parent"]["uri"] = doc.uri


class ChunkSentencizer(Executor):
    """
    Cleans up and sentencizes a Document's chunks
    """

    @requests(on="/index")
    def sentencize_text_chunks(self, docs, **kwargs):
        for doc in docs:
            sentencizer = Executor.from_hub(
                "jinahub://SpacySentencizer/v0.4",
                install_requirements=True,
            )
            sentencizer.segment(doc.chunks, parameters={})


class ChunkMerger(Executor):
    """
    Merges all doc.chunks.chunks to doc.chunks
    """

    @requests(on="/index")
    def merge_chunks(self, docs, **kwargs):
        for doc in docs:  # level 0 document
            doc.chunks = doc.chunks[...]
            # doc.chunks.extend(doc.chunks["@c, cc, ccc"])


class DebugChunkPrinter(Executor):
    """
    Print debug statements
    """

    @requests
    def print_chunks(self, docs, **kwargs):
        levels = ["@c"]
        for level in levels:
            print(f"Chunks for {level}")
            print("=" * 10)
            for doc in docs[level]:
                print(level)
                print(doc.text)
                print(f"Tags: {doc.tags}")
                print("-" * 10)
