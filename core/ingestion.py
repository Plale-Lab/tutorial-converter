import os
import requests
from llama_index.core.node_parser import HierarchicalNodeParser, SimpleNodeParser
from llama_index.core import Document

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
        if self.provider == "llama_parse":
            return self._parse_with_llama(url)
        elif self.provider == "firecrawl":
            return self._parse_with_firecrawl(url)
        else:
            raise ValueError("No valid ingestion provider configured.")
            
    def get_chunks(self, text: str, chunk_size: int = 1024):
        """
        Splits text into hierarchical chunks.
        """
        doc = Document(text=text)
        # Using SimpleNodeParser for simplicity if Hierarchical is too complex to setup without index structure
        # parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128])
        parser = SimpleNodeParser.from_defaults(chunk_size=chunk_size, chunk_overlap=128)
        nodes = parser.get_nodes_from_documents([doc])
        return [node.text for node in nodes]

    def _parse_with_llama(self, url: str) -> str:
        print(f"Parsing with LlamaParse: {url}")
        # Initialize LlamaParse
        parser = LlamaParse(
            api_key=self.llama_cloud_api_key,
            result_type="markdown",
            verbose=True
        )
        # Check if local file or URL
        # LlamaParse loads data via the load_data method which handles files.
        # For URLs, we might need to download first or use their web parsing if supported.
        # Assuming URL for now invokes their web-reader or we treat it as file if local path.
        
        # Quick check if it looks like a file path that exists
        if os.path.exists(url):
            documents = parser.load_data(url)
        else:
            # LlamaParse traditionally parses FILES (PDFs). 
            # For direct URL scraping (HTML), Firecrawl is better.
            # But let's assume we might feed it a downloaded PDF or generic web loader.
            # For simplicity, if it's a web URL, LlamaParse might not be the direct tool unless using LlamaIndex's SimpleWebPageReader first.
            # Let's fallback to rudimentary download or raise.
             raise NotImplementedError("Direct URL parsing with LlamaParse requires integration with a web loader. Use Firecrawl for web pages.")

        # Combine loaded documents
        return "\n\n".join([doc.text for doc in documents])

    def _parse_with_firecrawl(self, url: str) -> str:
        print(f"Parsing with Firecrawl: {url}")
        # Firecrawl API endpoint: /v0/scrape
        payload = {
            "url": url,
            "pageOptions": {
                "onlyMainContent": True
            }
        }
        try:
            response = requests.post(f"{self.firecrawl_api_url}/v0/scrape", json=payload)
            response.raise_for_status()
            data = response.json()
            
            if data and 'data' in data and 'markdown' in data['data']:
                return data['data']['markdown']
            else:
                raise ValueError(f"Firecrawl response missing markdown: {data}")
                
        except Exception as e:
            print(f"Firecrawl error: {e}")
            # Fallback or re-raise
            raise e

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
