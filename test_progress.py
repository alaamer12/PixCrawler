"""
Test the progress manager functionality.

This script provides a simple way to verify that the progress manager
is working correctly with the enhanced progress bar display.
"""

import time
import random
from pathlib import Path
import sys

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent))

from helpers import ProgressManager

def simulate_dataset_generation():
    """Simulate the dataset generation process with progress bars."""
    # Create a progress manager
    progress = ProgressManager()
    
    # Step 1: Initialization
    progress.start_step("init")
    time.sleep(1)  # Simulate initialization work
    progress.update_step(1)
    progress.close()
    
    # Step 2: Download/Generate Images
    categories = ["animals", "vehicles", "nature", "buildings"]
    keywords_per_category = {
        "animals": ["cat", "dog", "elephant", "tiger", "lion"],
        "vehicles": ["car", "truck", "motorcycle", "bicycle", "boat"],
        "nature": ["mountain", "forest", "beach", "desert", "sky"],
        "buildings": ["house", "skyscraper", "bridge", "tower", "castle"]
    }
    
    total_keywords = sum(len(keywords) for keywords in keywords_per_category.values())
    progress.start_step("download", total=total_keywords)
    
    for category in categories:
        progress.start_subtask(f"Category: {category}", total=len(keywords_per_category[category]))
        
        for keyword in keywords_per_category[category]:
            progress.set_subtask_description(f"Downloading: {keyword}")
            progress.set_subtask_postfix(target=10)
            
            # Simulate downloading images
            download_time = random.uniform(0.5, 1.5)
            time.sleep(download_time)
            
            # Simulate checking duplicates
            progress.set_subtask_description(f"Checking duplicates: {keyword}")
            time.sleep(0.2)
            
            # Simulate checking integrity
            progress.set_subtask_description(f"Checking integrity: {keyword}")
            progress.set_subtask_postfix(valid=8, corrupted=2)
            time.sleep(0.3)
            
            # Update main progress
            progress.update_step(1)
            
        progress.close_subtask()
    
    progress.close()
    
    # Step 3: Generate Labels
    progress.start_step("labels", total=100)
    
    # Generate labels for each category
    for i in range(4):  # 4 categories
        category = categories[i]
        progress.start_subtask(f"Category: {category}")
        
        # Process each keyword in this category
        for j in range(5):  # 5 keywords per category
            keyword = keywords_per_category[category][j]
            progress.set_subtask_description(f"Keyword: {keyword}")
            
            # Simulate processing 5 images per keyword
            for k in range(5):
                progress.update_step(1)
                time.sleep(0.05)
        
        progress.close_subtask()
    
    progress.close()
    
    # Step 4: Generate Report
    progress.start_step("report")
    time.sleep(1.5)  # Simulate report generation
    progress.update_step(1)
    progress.close()
    
    # Step 5: Finalizing
    progress.start_step("finalizing")
    time.sleep(1)  # Simulate finalization
    progress.update_step(1)
    progress.close()
    
    # Print final message
    print("\n✅ Dataset generation complete!")
    print("   - Output directory: ./test_dataset")
    print("   - Log file: ./logs/pixcrawler.log")
    print("   - See the REPORT.md file in the output directory for detailed statistics")

if __name__ == "__main__":
    simulate_dataset_generation() 