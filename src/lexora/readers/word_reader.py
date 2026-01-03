"""Word document reader."""

from docx import Document
from .base_reader import FileReader


class WordReader(FileReader):
    """Reader for Word documents (.docx)."""

    def supports(self, file_path: str) -> bool:
        """Check if file is a Word document."""
        lower_path = file_path.lower()
        return lower_path.endswith('.docx') or lower_path.endswith('.doc')

    def read(self, file_path: str) -> str:
        """
        Read Word document and extract text content.

        Args:
            file_path: Path to the Word document

        Returns:
            str: Extracted text content
        """
        try:
            doc = Document(file_path)
            text_content = []

            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)

            return '\n\n'.join(text_content)
        except Exception as e:
            raise ValueError(f"Failed to read Word document: {str(e)}")
