from jina import Executor, requests
import pikepdf
import numpy


def preproc(doc):
    for chunk in doc.chunks:
        if isinstance(chunk.content, numpy.ndarray):
            chunk.set_image_tensor_shape((224, 224))
            chunk.tensor = chunk.tensor.astype(numpy.uint8)
            chunk.set_image_tensor_normalization()
            chunk.convert_image_tensor_to_blob()
            chunk.tags["parent"] = {}
            chunk.tags["parent"]["uri"] = doc.uri


class PdfPreprocessor(Executor):
    @requests(on="/index")
    def process_pdf(self, docs, **kwargs):
        for doc in docs:
            preproc(doc)
            if doc.uri:
                doc.load_uri_to_blob()

class PdfMetaDataAdder(Executor):
    @requests
    def metadata_to_tags(self, docs, **kwargs):
        for doc in docs:
            pdf = pikepdf.Pdf.open(doc.uri)
            doc_info = pdf.docinfo
            for key, value in doc_info.items():
                print(key, ":", value)
