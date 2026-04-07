"""MOBI file reader."""

from .base_reader import FileReader


class MobiReader(FileReader):
    """Reader for MOBI files."""

    def supports(self, file_path: str) -> bool:
        """Check if file is a MOBI."""
        return file_path.lower().endswith('.mobi')

    def read(self, file_path: str) -> str:
        """
        Read MOBI file and extract text content.

        Args:
            file_path: Path to the MOBI file

        Returns:
            str: Extracted text content
        """
        try:
            import mobi
            from bs4 import BeautifulSoup

            tempdir, filepath = mobi.extract(file_path)

            # Read the extracted HTML file
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Parse HTML to extract text
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)

            return text
        except ImportError as e:
            raise ImportError(
                f"Missing dependency for MOBI support: {e.name}. "
                "Install it with: pip install mobi beautifulsoup4"
            )
        except Exception as e:
            raise ValueError(f"Failed to read MOBI file: {str(e)}")
