"""
Optimized engine processing method for high-throughput parallel downloads.
This will be integrated into _engine.py.
"""

def process_engine_with_target(self, config: EngineConfig, variations: List[str],
                               out_dir: str, target: int, initial_file_count: int) -> EngineResult:
    """
    Processes a single engine with pre-allocated target (ZERO lock contention).
    Each engine works independently without checking global counters.
    
    This is the key optimization:
    - Pre-allocated target eliminates need to check global counter
    - Count files once at start, once at end (not per variation)
    - Sequential variation processing (no thread explosion)
    - Only updates global counter at the very end
    
    Args:
        config (EngineConfig): The engine configuration.
        variations (List[str]): Search variations for this engine.
        out_dir (str): Output directory for images.
        target (int): Pre-allocated target for THIS engine only.
        initial_file_count (int): File count when this engine started.
        
    Returns:
        EngineResult: Results from this engine.
    """
    import time
    start_time = time.time()
    variation_results = []
    
    try:
        logger.info(f"[{config.name}] Starting with target={target}, initial_files={initial_file_count}")
        
        # Select variations to process
        variations_to_process = select_variations(variations, target)
        downloaded_so_far = 0
        
        # Process variations SEQUENTIALLY (no variation-level parallelism)
        for i, variation in enumerate(variations_to_process):
            if downloaded_so_far >= target:
                logger.info(f"[{config.name}] Target reached, stopping")
                break
                
            remaining = target - downloaded_so_far
            if remaining <= 0:
                break
            
            # Process this variation
            var_start = time.time()
            try:
                # Calculate offset for diversity
                current_offset = config.random_offset + (i * config.variation_step)
                
                logger.info(f"[{config.name}] Variation {i+1}/{len(variations_to_process)}: '{variation}' "
                          f"(need {remaining} more)")
                
                # Create crawler
                crawler = self._create_enhanced_crawler(config.name, out_dir)
                
                # Perform crawl (this is the actual download)
                crawler.crawl(
                    keyword=variation,
                    max_num=remaining,
                    min_size=self.image_downloader.min_image_size,
                    offset=current_offset,
                    file_idx_offset=0  # Not used for counting
                )
                
                # Count new files (batch count after this variation)
                current_file_count = self.engine_processor._get_current_file_count(out_dir)
                new_downloads = max(0, current_file_count - initial_file_count - downloaded_so_far)
                downloaded_so_far += new_downloads
                
                var_time = time.time() - var_start
                
                variation_results.append(VariationResult(
                    variation=variation,
                    downloaded_count=new_downloads,
                    success=True,
                    processing_time=var_time
                ))
                
                logger.info(f"[{config.name}] Variation complete: +{new_downloads} images "
                          f"(total: {downloaded_so_far}/{target}) in {var_time:.1f}s")
                
            except Exception as e:
                var_time = time.time() - var_start
                logger.warning(f"[{config.name}] Variation '{variation}' failed: {e}")
                variation_results.append(VariationResult(
                    variation=variation,
                    downloaded_count=0,
                    success=False,
                    error=str(e),
                    processing_time=var_time
                ))
            
            # Small delay between variations
            if i < len(variations_to_process) - 1:
                time.sleep(0.3)
        
        # Final count for this engine
        final_file_count = self.engine_processor._get_current_file_count(out_dir)
        total_downloaded = max(0, final_file_count - initial_file_count)
        
    except Exception as e:
        logger.error(f"[{config.name}] Engine failed: {e}")
        variation_results.append(VariationResult(
            variation="engine_failure",
            downloaded_count=0,
            success=False,
            error=str(e)
        ))
        total_downloaded = 0
    
    processing_time = time.time() - start_time
    success_rate = self._calculate_success_rate(variation_results)
    
    logger.info(f"[{config.name}] Completed: {total_downloaded} images in {processing_time:.1f}s")
    
    return EngineResult(
        engine_name=config.name,
        total_downloaded=total_downloaded,
        variations_processed=len(variation_results),
        success_rate=success_rate,
        processing_time=processing_time,
        variations=variation_results
    )
