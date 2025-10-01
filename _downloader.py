"""
builder/_downloader.py

Search engine downloader with per-engine classes, comprehensive metrics,
and consistent error handling.
"""

import requests
import time
import logging
from typing import TypedDict, List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from abc import ABC, abstractmethod


# -------------------------------
# LOGGING SETUP
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# -------------------------------
# TYPE DEFINITIONS
# -------------------------------
class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str


@dataclass
class DownloadMetrics:
    """Metrics for a single download operation"""
    engine: str
    query: str
    page: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    result_count: int = 0
    total_results: Optional[int] = None
    success: bool = False
    error: Optional[str] = None
    status_code: Optional[int] = None
    retry_count: int = 0
    
    def finish(self, success: bool, result_count: int = 0, 
               total_results: Optional[int] = None, error: Optional[str] = None,
               status_code: Optional[int] = None):
        """Mark the operation as complete and calculate duration"""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
        self.success = success
        self.result_count = result_count
        self.total_results = total_results
        self.error = error
        self.status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format"""
        return {
            "engine": self.engine,
            "query": self.query,
            "page": self.page,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "result_count": self.result_count,
            "total_results": self.total_results,
            "success": self.success,
            "error": self.error,
            "status_code": self.status_code,
            "retry_count": self.retry_count
        }


class SearchResponse(TypedDict):
    engine: str
    query: str
    page: int
    results: List[SearchResult]
    error: Optional[str]
    total_results: Optional[int]
    metrics: Dict[str, Any]


# -------------------------------
# BASE DOWNLOADER CLASS
# -------------------------------
class BaseDownloader(ABC):
    """Base class for all search engine downloaders"""
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.session = self._create_session()
        self._metrics_history: List[DownloadMetrics] = []
    
    def _create_session(self) -> requests.Session:
        """Create session with retry logic"""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        return session
    
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Return the engine name"""
        pass
    
    @abstractmethod
    def _download(self, query: str, page: int, results_per_page: int) -> SearchResponse:
        """Internal download method to be implemented by subclasses"""
        pass
    
    def download(self, query: str, page: int = 1, results_per_page: int = 10) -> SearchResponse:
        """
        Public download method with metrics tracking and logging
        
        Args:
            query: Search keywords
            page: Results page number (1-indexed)
            results_per_page: Number of results per page
        
        Returns:
            SearchResponse with results and metrics
        """
        metrics = DownloadMetrics(
            engine=self.engine_name,
            query=query,
            page=page,
            start_time=datetime.now()
        )
        
        self.logger.info(f"Starting download: query='{query}', page={page}, results_per_page={results_per_page}")
        
        try:
            response = self._download(query, page, results_per_page)
            
            metrics.finish(
                success=response['error'] is None,
                result_count=len(response['results']),
                total_results=response.get('total_results'),
                error=response['error']
            )
            
            response['metrics'] = metrics.to_dict()
            
            if response['error']:
                self.logger.warning(
                    f"Download completed with error: {response['error']} "
                    f"(duration: {metrics.duration_seconds:.2f}s)"
                )
            else:
                self.logger.info(
                    f"Download successful: {metrics.result_count} results "
                    f"(duration: {metrics.duration_seconds:.2f}s)"
                )
            
            self._metrics_history.append(metrics)
            return response
            
        except Exception as e:
            metrics.finish(success=False, error=str(e))
            self._metrics_history.append(metrics)
            
            self.logger.error(f"Download failed with exception: {str(e)}", exc_info=True)
            
            return {
                "engine": self.engine_name,
                "query": query,
                "page": page,
                "results": [],
                "error": f"Unexpected error: {str(e)}",
                "total_results": None,
                "metrics": metrics.to_dict()
            }
    
    def get_metrics_history(self) -> List[Dict[str, Any]]:
        """Get all metrics from this downloader instance"""
        return [m.to_dict() for m in self._metrics_history]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all downloads"""
        if not self._metrics_history:
            return {"message": "No downloads yet"}
        
        total = len(self._metrics_history)
        successful = sum(1 for m in self._metrics_history if m.success)
        failed = total - successful
        
        durations = [m.duration_seconds for m in self._metrics_history if m.duration_seconds]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        total_results = sum(m.result_count for m in self._metrics_history)
        
        return {
            "engine": self.engine_name,
            "total_downloads": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "total_results_retrieved": total_results,
            "average_duration_seconds": avg_duration,
            "min_duration_seconds": min(durations) if durations else 0,
            "max_duration_seconds": max(durations) if durations else 0
        }
    
    def _create_error_response(self, query: str, page: int, error_msg: str) -> SearchResponse:
        """Create standardized error response"""
        return {
            "engine": self.engine_name,
            "query": query,
            "page": page,
            "results": [],
            "error": error_msg,
            "total_results": None,
            "metrics": {}
        }


# -------------------------------
# GOOGLE DOWNLOADER
# -------------------------------
class GoogleDownloader(BaseDownloader):
    """Google Custom Search API downloader"""
    
    @property
    def engine_name(self) -> str:
        return "google"
    
    def _download(self, query: str, page: int, results_per_page: int) -> SearchResponse:
        """Download Google search results"""
        if not self.api_key:
            return self._create_error_response(query, page, "API key required for Google Search")
        
        if results_per_page > 10:
            results_per_page = 10
        
        try:
            start = (page - 1) * results_per_page + 1
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "q": query,
                "start": start,
                "num": results_per_page,
                "key": self.api_key
            }
            
            start_time = time.time()
            resp = self.session.get(url, params=params, timeout=self.timeout)
            request_duration = time.time() - start_time
            
            self.logger.debug(f"API request took {request_duration:.2f}s, status={resp.status_code}")
            
            resp.raise_for_status()
            data = resp.json()
            
            if "items" not in data:
                return {
                    "engine": self.engine_name,
                    "query": query,
                    "page": page,
                    "results": [],
                    "error": None,
                    "total_results": 0,
                    "metrics": {}
                }
            
            results = [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                }
                for item in data.get("items", [])
            ]
            
            return {
                "engine": self.engine_name,
                "query": query,
                "page": page,
                "results": results,
                "error": None,
                "total_results": int(data.get("searchInformation", {}).get("totalResults", 0)),
                "metrics": {}
            }
            
        except requests.RequestException as e:
            return self._create_error_response(query, page, f"Request error: {str(e)}")
        except (KeyError, ValueError) as e:
            return self._create_error_response(query, page, f"Parse error: {str(e)}")


# -------------------------------
# BING DOWNLOADER
# -------------------------------
class BingDownloader(BaseDownloader):
    """Bing Web Search API downloader"""
    
    @property
    def engine_name(self) -> str:
        return "bing"
    
    def _download(self, query: str, page: int, results_per_page: int) -> SearchResponse:
        """Download Bing search results"""
        if not self.api_key:
            return self._create_error_response(query, page, "API key required for Bing Search")
        
        try:
            offset = (page - 1) * results_per_page
            
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {
                "q": query,
                "count": results_per_page,
                "offset": offset
            }
            
            start_time = time.time()
            resp = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
            request_duration = time.time() - start_time
            
            self.logger.debug(f"API request took {request_duration:.2f}s, status={resp.status_code}")
            
            resp.raise_for_status()
            data = resp.json()
            
            web_pages = data.get("webPages", {})
            results = [
                {
                    "title": item.get("name", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", "")
                }
                for item in web_pages.get("value", [])
            ]
            
            return {
                "engine": self.engine_name,
                "query": query,
                "page": page,
                "results": results,
                "error": None,
                "total_results": web_pages.get("totalEstimatedMatches"),
                "metrics": {}
            }
            
        except requests.RequestException as e:
            return self._create_error_response(query, page, f"Request error: {str(e)}")
        except (KeyError, ValueError) as e:
            return self._create_error_response(query, page, f"Parse error: {str(e)}")


# -------------------------------
# DUCKDUCKGO DOWNLOADER
# -------------------------------
class DuckDuckGoDownloader(BaseDownloader):
    """DuckDuckGo Instant Answer API downloader"""
    
    @property
    def engine_name(self) -> str:
        return "duckduckgo"
    
    def _download(self, query: str, page: int, results_per_page: int) -> SearchResponse:
        """Download DuckDuckGo search results"""
        try:
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            start_time = time.time()
            resp = self.session.get(url, params=params, timeout=self.timeout)
            request_duration = time.time() - start_time
            
            self.logger.debug(f"API request took {request_duration:.2f}s, status={resp.status_code}")
            
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            
            for topic in data.get("RelatedTopics", []):
                if "Topics" in topic:
                    for subtopic in topic["Topics"]:
                        if "Text" in subtopic and "FirstURL" in subtopic:
                            results.append({
                                "title": subtopic["Text"][:100],
                                "url": subtopic["FirstURL"],
                                "snippet": subtopic["Text"]
                            })
                elif "Text" in topic and "FirstURL" in topic:
                    results.append({
                        "title": topic["Text"][:100],
                        "url": topic["FirstURL"],
                        "snippet": topic["Text"]
                    })
            
            start_idx = (page - 1) * results_per_page
            end_idx = start_idx + results_per_page
            paginated_results = results[start_idx:end_idx]
            
            return {
                "engine": self.engine_name,
                "query": query,
                "page": page,
                "results": paginated_results,
                "error": None,
                "total_results": len(results),
                "metrics": {}
            }
            
        except requests.RequestException as e:
            return self._create_error_response(query, page, f"Request error: {str(e)}")
        except (KeyError, ValueError) as e:
            return self._create_error_response(query, page, f"Parse error: {str(e)}")


# -------------------------------
# BAIDU DOWNLOADER
# -------------------------------
class BaiduDownloader(BaseDownloader):
    """Baidu search downloader (web scraping)"""
    
    @property
    def engine_name(self) -> str:
        return "baidu"
    
    def _download(self, query: str, page: int, results_per_page: int) -> SearchResponse:
        """Download Baidu search results via web scraping"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return self._create_error_response(
                query, page,
                "BeautifulSoup4 not installed. Install with: pip install beautifulsoup4"
            )
        
        try:
            pn = (page - 1) * results_per_page
            
            url = "https://www.baidu.com/s"
            params = {
                "wd": query,
                "pn": pn,
                "rn": results_per_page
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            start_time = time.time()
            resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            request_duration = time.time() - start_time
            
            self.logger.debug(f"Request took {request_duration:.2f}s, status={resp.status_code}")
            
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            
            for div in soup.select(".result, .result-op"):
                try:
                    title_elem = div.select_one("h3, h3 a")
                    link_elem = div.select_one("a")
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        link = link_elem.get("href", "")
                        
                        snippet_elem = div.select_one(".c-abstract, .c-span-last")
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        results.append({
                            "title": title,
                            "url": link,
                            "snippet": snippet
                        })
                except Exception:
                    continue
            
            return {
                "engine": self.engine_name,
                "query": query,
                "page": page,
                "results": results,
                "error": None,
                "total_results": None,
                "metrics": {}
            }
            
        except ImportError as e:
            return self._create_error_response(query, page, f"Import error: {str(e)}")
        except requests.RequestException as e:
            return self._create_error_response(query, page, f"Request error: {str(e)}")
        except Exception as e:
            return self._create_error_response(query, page, f"Parse error: {str(e)}")

