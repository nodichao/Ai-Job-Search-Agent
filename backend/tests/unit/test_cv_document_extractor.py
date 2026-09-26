from io import BytesIO
from zipfile import ZipFile

import pytest
from pypdf import PdfWriter

from app.services.cv_document_extractor import (
    DOCX_MIME_TYPE,
    MAX_CV_FILE_BYTES,
    PDF_MIME_TYPE,
    CvDocumentError,
    CvDocumentExtractor,
)


def _minimal_pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode())
    return bytes(pdf)


def _minimal_docx(text: str) -> bytes:
    content_types = b'''<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>'''
    document = (
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    ).encode()
    stream = BytesIO()
    with ZipFile(stream, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("word/document.xml", document)
    return stream.getvalue()


def test_extracts_text_from_valid_pdf_and_docx():
    extractor = CvDocumentExtractor()
    assert extractor.extract_text("cv.pdf", PDF_MIME_TYPE, _minimal_pdf("Python Engineer")) == "Python Engineer"
    assert extractor.extract_text("cv.docx", DOCX_MIME_TYPE, _minimal_docx("Python Engineer")) == "Python Engineer"


@pytest.mark.parametrize(("filename", "mime", "content"), [
    ("cv.txt", "text/plain", b"Python"),
    ("cv.pdf", "text/plain", _minimal_pdf("Python")),
    ("cv.docx", DOCX_MIME_TYPE, b"not a zip"),
    ("cv.pdf", PDF_MIME_TYPE, b"%PDF-not a valid PDF"),
    ("cv.pdf", PDF_MIME_TYPE, b""),
    ("empty.pdf", PDF_MIME_TYPE, _minimal_pdf("")),
])
def test_rejects_unsupported_empty_malformed_oversized_or_textless_documents(filename, mime, content):
    with pytest.raises(CvDocumentError):
        CvDocumentExtractor().extract_text(filename, mime, content)


def test_rejects_oversized_file():
    with pytest.raises(CvDocumentError, match="5 MiB"):
        CvDocumentExtractor().extract_text("cv.pdf", PDF_MIME_TYPE, b"x" * (MAX_CV_FILE_BYTES + 1))


def test_rejects_encrypted_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("test-password")
    output = BytesIO()
    writer.write(output)
    with pytest.raises(CvDocumentError, match="Encrypted"):
        CvDocumentExtractor().extract_text("cv.pdf", PDF_MIME_TYPE, output.getvalue())
