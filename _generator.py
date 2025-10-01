"""
builder/generator.py

Orchestrates multiple search engine downloads, aggregates results,
manages concurrent operations, and provides comprehensive dataset generation.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from _downloader import (
    BaseDownloader,
    GoogleDownloader,
    BingDownloader,
    DuckDuckGoDownloader,
    BaiduDownloader,
    SearchResponse,
    SearchResult
)


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
@dataclass
class GeneratorConfig:
    """Configuration for the search results generator"""
    queries: List[str]
    engines: List[str] = field(default_factory=lambda: ["duckduckgo"])
    pages_per_query: int = 1
    results_per_page: int = 10
    max_workers: int = 3
    timeout: int = 15
    deduplicate: bool = True
    api_keys: Dict[str, str] = field(default_factory=dict)
    delay_between_requests: float = 0.5
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.queries:
            raise ValueError("At least one query is required")
        
        valid_engines = {"google", "bing", "duckduckgo", "baidu"}
        for engine in self.engines:
            if engine not in valid_engines:
                raise ValueError(f"Invalid engine: {engine}. Valid: {valid_engines}")
        
        if self.pages_per_query < 1:
            raise ValueError("pages_per_query must be at least 1")
        
        if self.results_per_page < 1:
            raise ValueError("results_per_page must be at least 1")


@dataclass
class GeneratorMetrics:
    """Aggregated metrics for the entire generation process"""
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    total_queries: int = 0
    total_downloads: int = 0
    successful_downloads: int = 0
    failed_downloads: int = 0
    total_results: int = 0
    unique_results: int = 0
    duplicates_removed: int = 0
    engines_used: List[str] = field(default_factory=list)
    query_metrics: List[Dict[str, Any]] = field(default_factory=list)
    
    def finish(self):
        """Mark generation as complete"""
        self.end_time = datetime.now()
        self.total_duration_seconds = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_seconds": self.total_duration_seconds,
            "total_queries": self.total_queries,
            "total_downloads": self.total_downloads,
            "successful_downloads": self.successful_downloads,
            "failed_downloads": self.failed_downloads,
            "success_rate": self.successful_downloads / self.total_downloads if self.total_downloads > 0 else 0,
            "total_results": self.total_results,
            "unique_results": self.unique_results,
            "duplicates_removed": self.duplicates_removed,
            "engines_used": self.engines_used,
            "query_metrics": self.query_metrics
        }


@dataclass
class GeneratorResult:
    """Complete result from generator including all data and metrics"""
    queries: List[str]
    engines: List[str]
    results: List[SearchResult]
    results_by_query: Dict[str, List[SearchResult]]
    results_by_engine: Dict[str, List[SearchResult]]
    errors: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    config: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "queries": self.queries,
            "engines": self.engines,
            "total_results": len(self.results),
            "results": self.results,
            "results_by_query": self.results_by_query,
            "results_by_engine": self.results_by_engine,
            "errors": self.errors,
            "metrics": self.metrics,
            "config": self.config
        }
    
    def save_json(self, filepath: str):
        """Save results to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    def save_csv(self, filepath: str):
        """Save results to CSV file"""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if not self.results:
                return
            
            fieldnames = ['title', 'url', 'snippet', 'query', 'engine']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                writer.writerow({
                    'title': result['title'],
                    'url': result['url'],
                    'snippet': result['snippet'],
                    'query': result.get('query', ''),
                    'engine': result.get('engine', '')
                })


# -------------------------------
# MAIN GENERATOR CLASS
# -------------------------------
class SearchResultsGenerator:
    """Orchestrates search result generation across multiple engines and queries"""
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.downloaders: Dict[str, BaseDownloader] = {}
        self._initialize_downloaders()
    
    def _initialize_downloaders(self):
        """Initialize downloader instances for requested engines"""
        engine_classes = {
            "google": GoogleDownloader,
            "bing": BingDownloader,
            "duckduckgo": DuckDuckGoDownloader,
            "baidu": BaiduDownloader
        }
        
        for engine in self.config.engines:
            api_key = self.config.api_keys.get(engine)
            downloader_class = engine_classes[engine]
            self.downloaders[engine] = downloader_class(
                api_key=api_key,
                timeout=self.config.timeout
            )
            self.logger.info(f"Initialized {engine} downloader")
    
    def generate(self) -> GeneratorResult:
        """
        Generate search results for all configured queries and engines
        
        Returns:
            GeneratorResult containing all results and metrics
        """
        self.logger.info("="*60)
        self.logger.info("Starting Search Results Generation")
        self.logger.info("="*60)
        self.logger.info(f"Queries: {len(self.config.queries)}")
        self.logger.info(f"Engines: {self.config.engines}")
        self.logger.info(f"Pages per query: {self.config.pages_per_query}")
        self.logger.info(f"Results per page: {self.config.results_per_page}")
        
        # Initialize metrics
        metrics = GeneratorMetrics(
            start_time=datetime.now(),
            total_queries=len(self.config.queries),
            engines_used=self.config.engines
        )
        
        # Storage for results and errors
        all_results: List[SearchResult] = []
        results_by_query: Dict[str, List[SearchResult]] = {q: [] for q in self.config.queries}
        results_by_engine: Dict[str, List[SearchResult]] = {e: [] for e in self.config.engines}
        errors: List[Dict[str, Any]] = []
        
        # Generate download tasks
        tasks = self._generate_tasks()
        metrics.total_downloads = len(tasks)
        
        self.logger.info(f"Total download tasks: {len(tasks)}")
        
        # Execute downloads
        if self.config.max_workers == 1:
            # Sequential execution
            results = self._execute_sequential(tasks)
        else:
            # Concurrent execution
            results = self._execute_concurrent(tasks)
        
        # Process results
        seen_urls: Set[str] = set()
        
        for response in results:
            query = response['query']
            engine = response['engine']
            
            # Track metrics
            if response['error']:
                metrics.failed_downloads += 1
                errors.append({
                    "query": query,
                    "engine": engine,
                    "page": response['page'],
                    "error": response['error']
                })
            else:
                metrics.successful_downloads += 1
            
            # Process each result
            for result in response['results']:
                url = result['url']
                
                # Add metadata
                result_with_meta = {
                    **result,
                    'query': query,
                    'engine': engine
                }
                
                # Deduplication
                if self.config.deduplicate:
                    if url in seen_urls:
                        metrics.duplicates_removed += 1
                        continue
                    seen_urls.add(url)
                
                all_results.append(result_with_meta)
                results_by_query[query].append(result_with_meta)
                results_by_engine[engine].append(result_with_meta)
                metrics.total_results += 1
        
        metrics.unique_results = len(all_results)
        
        # Add query-level metrics
        for query in self.config.queries:
            query_result_count = len(results_by_query[query])
            metrics.query_metrics.append({
                "query": query,
                "results": query_result_count
            })
        
        # Finalize metrics
        metrics.finish()
        
        # Log summary
        self.logger.info("="*60)
        self.logger.info("Generation Complete")
        self.logger.info("="*60)
        self.logger.info(f"Duration: {metrics.total_duration_seconds:.2f}s")
        self.logger.info(f"Successful downloads: {metrics.successful_downloads}/{metrics.total_downloads}")
        self.logger.info(f"Total results: {metrics.total_results}")
        self.logger.info(f"Unique results: {metrics.unique_results}")
        if self.config.deduplicate:
            self.logger.info(f"Duplicates removed: {metrics.duplicates_removed}")
        
        # Create final result
        return GeneratorResult(
            queries=self.config.queries,
            engines=self.config.engines,
            results=all_results,
            results_by_query=results_by_query,
            results_by_engine=results_by_engine,
            errors=errors,
            metrics=metrics.to_dict(),
            config={
                "queries": self.config.queries,
                "engines": self.config.engines,
                "pages_per_query": self.config.pages_per_query,
                "results_per_page": self.config.results_per_page,
                "deduplicate": self.config.deduplicate
            }
        )
    
    def _generate_tasks(self) -> List[Dict[str, Any]]:
        """Generate list of download tasks"""
        tasks = []
        for query in self.config.queries:
            for engine in self.config.engines:
                for page in range(1, self.config.pages_per_query + 1):
                    tasks.append({
                        "query": query,
                        "engine": engine,
                        "page": page,
                        "results_per_page": self.config.results_per_page
                    })
        return tasks
    
    def _execute_sequential(self, tasks: List[Dict[str, Any]]) -> List[SearchResponse]:
        """Execute downloads sequentially"""
        results = []
        for i, task in enumerate(tasks, 1):
            self.logger.info(f"Task {i}/{len(tasks)}: {task['engine']} - {task['query'][:50]}...")
            
            downloader = self.downloaders[task['engine']]
            response = downloader.download(
                query=task['query'],
                page=task['page'],
                results_per_page=task['results_per_page']
            )
            results.append(response)
            
            # Delay between requests
            if i < len(tasks) and self.config.delay_between_requests > 0:
                time.sleep(self.config.delay_between_requests)
        
        return results
    
    def _execute_concurrent(self, tasks: List[Dict[str, Any]]) -> List[SearchResponse]:
        """Execute downloads concurrently"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(
                    self._download_task,
                    task['query'],
                    task['engine'],
                    task['page'],
                    task['results_per_page']
                ): task
                for task in tasks
            }
            
            # Collect results as they complete
            for i, future in enumerate(as_completed(future_to_task), 1):
                task = future_to_task[future]
                try:
                    response = future.result()
                    results.append(response)
                    self.logger.info(
                        f"Completed {i}/{len(tasks)}: {task['engine']} - "
                        f"{task['query'][:50]}... ({len(response['results'])} results)"
                    )
                except Exception as e:
                    self.logger.error(f"Task failed: {task} - {str(e)}")
                    # Create error response
                    results.append({
                        "engine": task['engine'],
                        "query": task['query'],
                        "page": task['page'],
                        "results": [],
                        "error": f"Task execution failed: {str(e)}",
                        "total_results": None,
                        "metrics": {}
                    })
        
        return results
    
    def _download_task(self, query: str, engine: str, page: int, 
                      results_per_page: int) -> SearchResponse:
        """Execute single download task"""
        downloader = self.downloaders[engine]
        response = downloader.download(query, page, results_per_page)
        
        # Add delay after download
        if self.config.delay_between_requests > 0:
            time.sleep(self.config.delay_between_requests)
        
        return response
    
    def get_downloader_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics from all downloaders"""
        return {
            engine: downloader.get_metrics_summary()
            for engine, downloader in self.downloaders.items()
        }

