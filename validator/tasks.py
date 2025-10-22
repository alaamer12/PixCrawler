from celery_core.app import app
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from validator.validation import CheckManager
from validator.integrity import (
    validate_dataset, remove_duplicates, process_integrity, 
    ImageHasher, DuplicationManager, ImageValidator
)
from validator.level import get_validation_strategy, ValidationLevel

def check_duplicates_impl(directory: str, category_name: str = "", keyword: str = "") -> Dict[str, Any]:
    try:
        if not Path(directory).exists():
            return {'error': f'Directory does not exist: {directory}'}
        
        check_manager = CheckManager()
        result = check_manager.check_duplicates(directory, category_name, keyword)
        
        return {
            'total_images': result.total_images,
            'duplicates_found': result.duplicates_found,
            'duplicates_removed': result.duplicates_removed,
            'unique_kept': result.unique_kept,
            'duplicate_groups': result.duplicate_groups,
            'processing_time': result.processing_time,
            'errors': result.errors
        }
    except Exception as e:
        return {'error': str(e)}

def check_integrity_impl(directory: str, expected_count: int = 0, category_name: str = "", keyword: str = "") -> Dict[str, Any]:
    try:
        if not Path(directory).exists():
            return {'error': f'Directory does not exist: {directory}'}
        
        check_manager = CheckManager()
        result = check_manager.check_integrity(directory, expected_count, category_name, keyword)
        
        return {
            'total_images': result.total_images,
            'valid_images': result.valid_images,
            'corrupted_images': result.corrupted_images,
            'corrupted_files': result.corrupted_files,
            'size_violations': result.size_violations,
            'processing_time': result.processing_time,
            'errors': result.errors
        }
    except Exception as e:
        return {'error': str(e)}

def check_all_impl(directory: str, expected_count: int = 0, category_name: str = "", keyword: str = "") -> Dict[str, Any]:
    try:
        if not Path(directory).exists():
            return {'error': f'Directory does not exist: {directory}'}
        
        check_manager = CheckManager()
        duplicate_result, integrity_result = check_manager.check_all(directory, expected_count, category_name, keyword)
        
        return {
            'duplicate_result': {
                'total_images': duplicate_result.total_images,
                'duplicates_found': duplicate_result.duplicates_found,
                'duplicates_removed': duplicate_result.duplicates_removed,
                'unique_kept': duplicate_result.unique_kept,
                'processing_time': duplicate_result.processing_time,
                'errors': duplicate_result.errors
            },
            'integrity_result': {
                'total_images': integrity_result.total_images,
                'valid_images': integrity_result.valid_images,
                'corrupted_images': integrity_result.corrupted_images,
                'corrupted_files': integrity_result.corrupted_files,
                'processing_time': integrity_result.processing_time,
                'errors': integrity_result.errors
            }
        }
    except Exception as e:
        return {'error': str(e)}

def validate_dataset_impl(directory: str) -> Dict[str, Any]:
    try:
        if not Path(directory).exists():
            return {'error': f'Directory does not exist: {directory}'}
        
        valid_count, total_count, corrupted_files = validate_dataset(directory)
        
        return {
            'valid_count': valid_count,
            'total_count': total_count,
            'corrupted_count': len(corrupted_files),
            'corrupted_files': corrupted_files
        }
    except Exception as e:
        return {'error': str(e)}

def remove_duplicates_impl(directory: str) -> Dict[str, Any]:
    try:
        if not Path(directory).exists():
            return {'error': f'Directory does not exist: {directory}'}
        
        removed_count, originals_kept = remove_duplicates(directory)
        
        return {
            'removed_count': removed_count,
            'originals_kept_count': len(originals_kept),
            'originals_kept': originals_kept
        }
    except Exception as e:
        return {'error': str(e)}

def process_integrity_impl(directory: str, remove_duplicates: bool = True, remove_corrupted: bool = True) -> Dict[str, Any]:
    try:
        if not Path(directory).exists():
            return {'error': f'Directory does not exist: {directory}'}
        
        result = process_integrity(directory, remove_duplicates, remove_corrupted)
        
        return {
            'directory': result['directory'],
            'validation': result['validation'],
            'duplicates': result['duplicates'],
            'processed_at': result['processed_at']
        }
    except Exception as e:
        return {'error': str(e)}

def build_hashmap_impl(image_files: List[str]) -> Dict[str, Any]:
    try:
        hasher = ImageHasher()
        content_hash_map, perceptual_hash_map = hasher.build_hashmap(image_files)
        
        return {
            'content_hash_map': content_hash_map,
            'perceptual_hash_map': perceptual_hash_map,
            'total_files_processed': len(image_files)
        }
    except Exception as e:
        return {'error': str(e)}

def detect_duplicates_impl(directory: str) -> Dict[str, Any]:
    try:
        if not Path(directory).exists():
            return {'error': f'Directory does not exist: {directory}'}
        
        manager = DuplicationManager()
        duplicates = manager.detect_duplicates(directory)
        
        return {
            'duplicates': duplicates,
            'duplicate_groups': len(duplicates),
            'total_duplicates': sum(len(dups) for dups in duplicates.values())
        }
    except Exception as e:
        return {'error': str(e)}

def count_valid_impl(directory: str) -> Dict[str, Any]:
    try:
        if not Path(directory).exists():
            return {'error': f'Directory does not exist: {directory}'}
        
        validator = ImageValidator()
        valid_count, total_count, corrupted_files = validator.count_valid(directory)
        
        return {
            'valid_count': valid_count,
            'total_count': total_count,
            'corrupted_count': len(corrupted_files),
            'corrupted_files': corrupted_files
        }
    except Exception as e:
        return {'error': str(e)}

def validate_image_impl(image_path: str, validation_level: str = "FAST") -> Dict[str, Any]:
    try:
        if not Path(image_path).exists():
            return {'error': f'Image file does not exist: {image_path}'}
        
        level_map = {
            'FAST': ValidationLevel.FAST,
            'MEDIUM': ValidationLevel.MEDIUM,
            'SLOW': ValidationLevel.SLOW
        }
        
        level = level_map.get(validation_level.upper(), ValidationLevel.FAST)
        strategy = get_validation_strategy(level)
        result = strategy.validate(image_path)
        
        return {
            'is_valid': result.is_valid,
            'issues_found': result.issues_found,
            'metadata': result.metadata,
            'processing_time': result.processing_time,
            'validation_level': result.validation_level.name,
            'file_path': result.file_path,
            'file_size_bytes': result.file_size_bytes
        }
    except Exception as e:
        return {'error': str(e)}

@app.task
def check_duplicates_task(directory: str, category_name: str = "", keyword: str = "") -> Dict[str, Any]:
    return check_duplicates_impl(directory, category_name, keyword)

@app.task
def check_integrity_task(directory: str, expected_count: int = 0, category_name: str = "", keyword: str = "") -> Dict[str, Any]:
    return check_integrity_impl(directory, expected_count, category_name, keyword)

@app.task
def check_all_task(directory: str, expected_count: int = 0, category_name: str = "", keyword: str = "") -> Dict[str, Any]:
    return check_all_impl(directory, expected_count, category_name, keyword)

@app.task
def validate_dataset_task(directory: str) -> Dict[str, Any]:
    return validate_dataset_impl(directory)

@app.task
def remove_duplicates_task(directory: str) -> Dict[str, Any]:
    return remove_duplicates_impl(directory)

@app.task
def process_integrity_task(directory: str, remove_duplicates: bool = True, remove_corrupted: bool = True) -> Dict[str, Any]:
    return process_integrity_impl(directory, remove_duplicates, remove_corrupted)

@app.task
def build_hashmap_task(image_files: List[str]) -> Dict[str, Any]:
    return build_hashmap_impl(image_files)

@app.task
def detect_duplicates_task(directory: str) -> Dict[str, Any]:
    return detect_duplicates_impl(directory)

@app.task
def count_valid_task(directory: str) -> Dict[str, Any]:
    return count_valid_impl(directory)

@app.task
def validate_image_task(image_path: str, validation_level: str = "FAST") -> Dict[str, Any]:
    return validate_image_impl(image_path, validation_level)