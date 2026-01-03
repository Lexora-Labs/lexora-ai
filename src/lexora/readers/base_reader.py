"""Base reader interface for different file formats."""

from abc import ABC, abstractmethod


class FileReader(ABC):
    """Abstract base class for file readers."""

    @abstractmethod
    def read(self, file_path: str) -> str:
        """
        Read a file and return its text content.

        Args:
            file_path: Path to the file to read

        Returns:
            str: Text content of the file

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """
        Check if this reader supports the given file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if this reader can read the file
        """
        pass
