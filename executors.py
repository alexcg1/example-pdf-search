from jina import Executor, requests
import numpy


def preproc(doc):
    for chunk in doc.chunks:
        if isinstance(chunk.content, numpy.ndarray):
            # print("Image")
            chunk.set_image_tensor_shape((224, 224))
            chunk.tensor = chunk.tensor.astype(numpy.uint8)
            chunk.set_image_tensor_normalization()
        # else:
            # print("Text")


class PdfPreprocessor(Executor):
    @requests
    def process_pdf(self, docs, **kwargs):
        for doc in docs:
            preproc(doc)
        # docs.apply(preproc) # this crashes
