"""In-memory text extraction for the explicitly supported CV formats."""
from io import BytesIO
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from pypdf import PdfReader


MAX_CV_FILE_BYTES = 5 * 1024 * 1024
MAX_CV_TEXT_CHARS = 100_000
MAX_DOCX_UNCOMPRESSED_BYTES = 20 * 1024 * 1024
MAX_DOCX_ZIP_ENTRIES = 2_000
MAX_PDF_PAGES = 100

PDF_MIME_TYPE = "application/pdf"
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class CvDocumentError(ValueError):
    """A safe, user-correctable document input error."""


class CvDocumentExtractor:
    def extract_text(self, filename: str, media_type: str | None, content: bytes) -> str:
        if not content:
            raise CvDocumentError("Uploaded CV is empty")
        if len(content) > MAX_CV_FILE_BYTES:
            raise CvDocumentError("Uploaded CV exceeds the 5 MiB limit")

        extension = filename.rsplit(".", 1)[-1].casefold() if "." in filename else ""
        mime = (media_type or "").split(";", 1)[0].strip().casefold()
        if extension == "pdf" and mime == PDF_MIME_TYPE:
            text = self._pdf_text(content)
        elif extension == "docx" and mime == DOCX_MIME_TYPE:
            text = self._docx_text(content)
        else:
            raise CvDocumentError("Only PDF and DOCX files with matching media types are supported")

        text = "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()
        if not text:
            raise CvDocumentError("No extractable text was found in the uploaded CV")
        if len(text) > MAX_CV_TEXT_CHARS:
            raise CvDocumentError("Extracted CV text exceeds the 100,000 character limit")
        return text

    @staticmethod
    def _pdf_text(content: bytes) -> str:
        if not content.startswith(b"%PDF-"):
            raise CvDocumentError("Uploaded PDF is malformed")
        try:
            reader = PdfReader(BytesIO(content), strict=True)
            if reader.is_encrypted:
                raise CvDocumentError("Encrypted PDFs are not supported")
            if len(reader.pages) > MAX_PDF_PAGES:
                raise CvDocumentError("PDF exceeds the 100 page limit")
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except CvDocumentError:
            raise
        except Exception:
            raise CvDocumentError("Uploaded PDF is malformed or unreadable") from None

    @staticmethod
    def _docx_text(content: bytes) -> str:
        try:
            with ZipFile(BytesIO(content)) as archive:
                infos = archive.infolist()
                if len(infos) > MAX_DOCX_ZIP_ENTRIES:
                    raise CvDocumentError("DOCX archive contains too many entries")
                if sum(info.file_size for info in infos) > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise CvDocumentError("DOCX expands beyond the permitted size")
                names = {info.filename for info in infos}
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise CvDocumentError("Uploaded DOCX is malformed")
                if any(info.flag_bits & 0x1 for info in infos):
                    raise CvDocumentError("Encrypted DOCX files are not supported")
                document_xml = archive.read("word/document.xml")
            upper_xml = document_xml.upper()
            if b"<!DOCTYPE" in upper_xml or b"<!ENTITY" in upper_xml:
                raise CvDocumentError("DOCX XML declarations are not supported")
            root = ElementTree.fromstring(document_xml)
            namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            paragraphs = []
            for paragraph in root.iter(f"{namespace}p"):
                parts = []
                for element in paragraph.iter():
                    if element.tag == f"{namespace}t":
                        parts.append(element.text or "")
                    elif element.tag == f"{namespace}tab":
                        parts.append("\t")
                    elif element.tag == f"{namespace}br":
                        parts.append("\n")
                paragraphs.append("".join(parts))
            return "\n".join(paragraphs)
        except CvDocumentError:
            raise
        except (BadZipFile, KeyError, ValueError, OSError):
            raise CvDocumentError("Uploaded DOCX is malformed or unreadable") from None
        except Exception:
            raise CvDocumentError("Uploaded DOCX is malformed or unreadable") from None
