import os
import requests
from llama_index.core.node_parser import HierarchicalNodeParser, SimpleNodeParser
from llama_index.core import Document
from llama_parse import LlamaParse

class IngestionService:
    def __init__(self):
        self.llama_cloud_api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        self.firecrawl_api_url = os.getenv("FIRECRAWL_API_URL", "http://localhost:3002")
        
        # Determine preferred provider based on available keys/config
        if self.llama_cloud_api_key:
            self.provider = "llama_parse"
        else:
            self.provider = "firecrawl"

    def parse_url(self, url: str) -> str:
        """
        Parses a URL or PDF and returns structured Markdown.
        """
        # Determine priority: If URL is web-based, prefer Firecrawl.
        if url.startswith("http"):
             if self.firecrawl_api_url:
                 try:
                    return self._parse_with_firecrawl(url)
                 except Exception as e:
                     print(f"Firecrawl failed ({e}). Falling back to direct fetch.")
                     return self._parse_with_fallback(url)
             
             # Fallback if no Firecrawl configured
             return self._parse_with_fallback(url)
        else:
             # Local file path
             return self._parse_with_llama(url)
            
    def get_chunks(self, text: str, chunk_size: int = 1024):
        """
        Splits text into hierarchical chunks.
        """
        doc = Document(text=text)
        parser = SimpleNodeParser.from_defaults(chunk_size=chunk_size, chunk_overlap=128)
        nodes = parser.get_nodes_from_documents([doc])
        return [node.text for node in nodes]

    def _parse_with_llama(self, filepath: str) -> str:
        """Parse local PDF/document file with LlamaParse or fallback parsers."""
        print(f"Parsing local file: {filepath}")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Try LlamaParse first (if API key available)
        if self.llama_cloud_api_key:
            try:
                print("Attempting LlamaParse...")
                parser = LlamaParse(
                    api_key=self.llama_cloud_api_key,
                    result_type="markdown",
                    verbose=True
                )
                documents = parser.load_data(filepath)
                content = "\n\n".join([doc.text for doc in documents])
                if content.strip():
                    return content
                print("LlamaParse returned empty content, trying fallbacks...")
            except Exception as e:
                print(f"LlamaParse failed: {e}, trying fallbacks...")
        
        # Fallback 1: PyMuPDF (fitz) - good for general PDFs
        try:
            import fitz  # PyMuPDF
            print("Attempting PyMuPDF (fitz)...")
            doc = fitz.open(filepath)
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            content = "\n\n".join(text_parts)
            if content.strip():
                print(f"PyMuPDF extracted {len(content)} chars")
                return content
        except ImportError:
            print("PyMuPDF not installed, trying other fallbacks...")
        except Exception as e:
            print(f"PyMuPDF failed: {e}")
        
        # Fallback 2: pypdf
        try:
            from pypdf import PdfReader
            print("Attempting pypdf...")
            reader = PdfReader(filepath)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            content = "\n\n".join(text_parts)
            if content.strip():
                print(f"pypdf extracted {len(content)} chars")
                return content
        except ImportError:
            print("pypdf not installed, trying other fallbacks...")
        except Exception as e:
            print(f"pypdf failed: {e}")
        
        # Fallback 3: pdfplumber
        try:
            import pdfplumber
            print("Attempting pdfplumber...")
            text_parts = []
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text_parts.append(page.extract_text() or "")
            content = "\n\n".join(text_parts)
            if content.strip():
                print(f"pdfplumber extracted {len(content)} chars")
                return content
        except ImportError:
            print("pdfplumber not installed")
        except Exception as e:
            print(f"pdfplumber failed: {e}")
        
        raise ValueError(f"Could not extract text from PDF. Install PyMuPDF: pip install pymupdf")

    def _parse_with_firecrawl(self, url: str) -> str:
        print(f"Parsing with Firecrawl: {url}")
        # Firecrawl API endpoint: /v0/scrape
        payload = {
            "url": url,
            "pageOptions": {
                "onlyMainContent": True
            }
        }
        # Don't catch exception here, let it propagate to parse_url to trigger fallback
        response = requests.post(f"{self.firecrawl_api_url}/v0/scrape", json=payload, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data and 'data' in data and 'markdown' in data['data']:
            return data['data']['markdown']
        else:
            raise ValueError(f"Firecrawl response missing markdown: {data}")

    def _parse_with_fallback(self, url: str) -> str:
        """
        Fallback: Direct simplistic HTML fetch.
        """
        print(f"Parsing with Direct Request Fallback: {url}")
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            
            # Very basic cleanup without BS4 dependency
            text = resp.text
            import re
            
            # Remove scripts and styles
            text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
            text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL)
            
            # Simple tag removal
            clean_text = re.sub(r'<[^>]+>', '\n', text)
            
            # Collapse whitespace
            clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
            
            return clean_text.strip()
            
        except Exception as e:
            raise ConnectionError(f"Failed to fetch content from {url}. Check internet connection. Error: {e}")


# Example usage
if __name__ == "__main__":
    # Mock usage
    service = IngestionService()
    try:
        # result = service.parse_url("https://example.com")
        # print(result)
        pass
    except Exception as e:
        print(e)
