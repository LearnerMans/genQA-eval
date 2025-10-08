from abc import ABC, abstractmethod
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
import os
import requests
from bs4 import BeautifulSoup
import html2text


class TextExtractor(ABC):
    """
    Abstract base class for text extractors.
    """
    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        self.file_path = file_path

    @abstractmethod
    def extract_text(self) -> str:
        """
        Extract text from the file.

        Returns:
            Str: The extracted text content.
        """
        pass


class PDFExtractor(TextExtractor):
    """
    Extractor for PDF files.
    """
    def extract_text(self) -> str:
        text = ""
        reader = PdfReader(self.file_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()


class DOCXExtractor(TextExtractor):
    """
    Extractor for DOCX files.
    """
    def extract_text(self) -> str:
        doc = Document(self.file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()


class MarkdownExtractor(TextExtractor):
    """
    Extractor for Markdown files (plain text).
    """
    def extract_text(self) -> str:
        with open(self.file_path, 'r', encoding='utf-8') as file:
            return file.read()


class CSVExtractor(TextExtractor):
    """
    Extractor for CSV files. Converts tabular data to text representation.
    """
    def extract_text(self) -> str:
        df = pd.read_csv(self.file_path)
        # Convert to a readable text format
        text = f"Columns: {', '.join(df.columns)}\n\n"
        text += df.to_string(index=False)
        return text


class ExcelExtractor(TextExtractor):
    """
    Extractor for Excel files. Converts tabular data to text representation.
    """
    def extract_text(self, sheet_name=0) -> str:
        df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        text = f"Sheet: {sheet_name}\nColumns: {', '.join(df.columns)}\n\n"
        text += df.to_string(index=False)
        return text


# Factory function to get appropriate extractor
def get_extractor(file_path: str) -> TextExtractor:
    """
    Factory function to return the appropriate extractor based on file extension.

    Args:
        file_path: Path to the file.

    Returns:
        TextExtractor: Instance of the appropriate extractor.

    Raises:
        ValueError: If file type is not supported.
    """
    _, ext = os.path.splitext(file_path.lower())

    extractors = {
        '.pdf': PDFExtractor,
        '.docx': DOCXExtractor,
        '.md': MarkdownExtractor,
        '.markdown': MarkdownExtractor,
        '.csv': CSVExtractor,
        '.xlsx': ExcelExtractor,
        '.xls': ExcelExtractor,
    }

    extractor_cls = extractors.get(ext)
    if extractor_cls is None:
        raise ValueError(f"Unsupported file type: {ext}")

    return extractor_cls(file_path)


def crawl_and_extract_markdown(url: str, depth: int = 1) -> str:
    """
    Fetches HTML from the given URL, crawls to the specified depth to find linked URLs,
    converts all HTML pages to Markdown, and returns the combined Markdown text.

    Args:
        url: The starting URL to crawl.
        depth: The maximum depth to crawl (default 1 means only the initial page).

    Returns:
        str: Combined Markdown text from all crawled pages.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    visited = set()
    texts = []
    queue = [(url, 0)]

    while queue and len(visited) < 1000:  # Limit to 1000 pages to avoid excessive crawling
        current_url, current_depth = queue.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()
            html = response.text

            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            md = h.handle(html).strip()

            texts.append(f"# {current_url}\n\n{md}\n\n---\n\n")

            if current_depth < depth:
                soup = BeautifulSoup(html, 'html.parser')
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http'):
                        full_url = href
                    elif href.startswith('/'):
                        # Assuming http/https
                        base = current_url.split('/', 3)[:3]
                        full_url = '/'.join(base) + href
                    elif href.startswith('?') or href.startswith('#'):
                        # Relative query or fragment, append to current
                        base = current_url.split('?')[0].split('#')[0]
                        full_url = base + href
                    else:
                        # Relative path
                        base_parts = current_url.rstrip('/').split('/')
                        if '/' in href:
                            href_parts = href.strip('/').split('/')
                            # Go up if needed, but simplify
                            full_url = '/'.join(base_parts[:-1]) + '/' + href
                        else:
                            full_url = '/'.join(base_parts[:-1]) + '/' + href
                        if not full_url.startswith('http'):
                            if current_url.startswith('http'):
                                full_url = 'https://' + full_url if current_url.startswith('https') else 'http://' + full_url
                            else:
                                continue

                    if full_url not in visited:
                        queue.append((full_url, current_depth + 1))
        except requests.RequestException as e:
            texts.append(f"# Error fetching {current_url}\n\nError: {str(e)}\n\n---\n\n")

    return ''.join(texts)
