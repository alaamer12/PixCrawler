"""
This module provides configuration schema definitions and data classes for managing PixCrawler application configuration. It includes JSON schema validation for configuration files and defines the main configuration data structure.

Classes:
    DatasetGenerationConfig: Holds all configuration options for the dataset generation process.

Functions:
    get_search_variations: Returns a list of search variation templates.
    get_engines: Returns a list of engine configurations.

Features:
    - Defines a JSON schema for validating configuration files.
    - Provides a dataclass for structured access to configuration parameters.
    - Manages predefined search variations and engine configurations.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from constants import DEFAULT_CACHE_FILE, KEYWORD_MODE, AI_MODELS

__all__ = [
    'CONFIG_SCHEMA',
    'DatasetGenerationConfig'
]

# JSON schema for configuration file validation
CONFIG_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["dataset_name", "categories"],
    "properties": {
        "dataset_name": {
            "type": "string",
            "description": "Name of the dataset"
        },
        "categories": {
            "type": "object",
            "description": "Map of category names to lists of keywords",
            "additionalProperties": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "options": {
            "type": "object",
            "description": "Optional configuration settings",
            "properties": {
                "max_images": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum number of images per keyword"
                },
                "output_dir": {
                    "type": ["string", "null"],
                    "description": "Custom output directory"
                },
                "integrity": {
                    "type": "boolean",
                    "description": "Whether to check image integrity"
                },
                "max_retries": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Maximum number of retry attempts"
                },
                "cache_file": {
                    "type": "string",
                    "description": "Path to the progress cache file"
                },
                "keyword_generation": {
                    "type": "string",
                    "enum": ["disabled", "enabled", "auto"],
                    "description": "Keyword generation mode: 'disabled', 'enabled', or 'auto' (generate only if none provided)"
                },
                "ai_model": {
                    "type": "string",
                    "enum": ["gpt4", "gpt4-mini"],
                    "description": "AI model to use for keyword generation"
                },
                "generate_labels": {
                    "type": "boolean",
                    "description": "Whether to generate label files for images"
                }
            }
        }
    }
}


def get_basic_variations() -> List[str]:
    """Basic keyword variations"""
    return [
        "{keyword}",
        "{keyword} photo",
        "{keyword} image",
        "{keyword} picture",
        "{keyword} pic",
        "{keyword} photograph",
        "{keyword} photography",
        "{keyword} stock photo",
        "{keyword} wallpaper",
        "{keyword} background",
    ]


def get_quality_variations() -> List[str]:
    """Quality-related variations"""
    return [
        "{keyword} high resolution",
        "{keyword} high quality",
        "{keyword} high quality picture",
        "{keyword} high quality image",
        "{keyword} HD",
        "{keyword} 4K",
        "{keyword} ultra high resolution",
        "{keyword} crisp image",
        "{keyword} clear photo",
        "{keyword} low quality",
        "{keyword} low quality picture",
        "{keyword} low quality image",
        "{keyword} pixelated",
        "{keyword} grainy",
        "{keyword} compressed",
    ]


def get_style_variations() -> List[str]:
    """Style and artistic variations"""
    return [
        "{keyword} realistic",
        "{keyword} realistic photo",
        "{keyword} photorealistic",
        "{keyword} cartoon",
        "{keyword} cartoon image",
        "{keyword} animated",
        "{keyword} drawing",
        "{keyword} sketch",
        "{keyword} painting",
        "{keyword} artwork",
        "{keyword} digital art",
        "{keyword} 3d render",
        "{keyword} 3d model",
        "{keyword} illustration",
        "{keyword} vector",
        "{keyword} abstract",
        "{keyword} minimalist",
        "{keyword} artistic",
        "{keyword} stylized",
        "{keyword} anime",
        "{keyword} manga",
        "{keyword} comic",
        "{keyword} pixel art",
        "{keyword} watercolor",
        "{keyword} oil painting",
        "{keyword} pencil drawing",
        "{keyword} ink drawing",
    ]


def get_time_period_variations() -> List[str]:
    """Time period variations"""
    return [
        "{keyword} vintage",
        "{keyword} vintage photo",
        "{keyword} retro",
        "{keyword} old",
        "{keyword} classic",
        "{keyword} antique",
        "{keyword} historical",
        "{keyword} modern",
        "{keyword} modern image",
        "{keyword} contemporary",
        "{keyword} recent",
        "{keyword} new",
        "{keyword} current",
    ]


def get_emotional_aesthetic_variations() -> List[str]:
    """Emotional and aesthetic variations"""
    return [
        "{keyword} beautiful",
        "{keyword} beautiful image",
        "{keyword} stunning",
        "{keyword} gorgeous",
        "{keyword} amazing",
        "{keyword} spectacular",
        "{keyword} cute",
        "{keyword} cute picture",
        "{keyword} adorable",
        "{keyword} sweet",
        "{keyword} lovely",
        "{keyword} funny {keyword}",
        "{keyword} hilarious",
        "{keyword} amusing",
        "{keyword} cool",
        "{keyword} awesome",
        "{keyword} impressive",
        "{keyword} dramatic",
        "{keyword} elegant",
        "{keyword} sophisticated",
        "{keyword} rustic",
        "{keyword} cozy",
        "{keyword} peaceful",
        "{keyword} serene",
        "{keyword} vibrant",
        "{keyword} lively",
        "{keyword} exotic",
        "{keyword} mysterious",
        "{keyword} romantic",
        "{keyword} dreamy",
    ]


def get_meme_culture_variations() -> List[str]:
    """Meme and internet culture variations"""
    return [
        "{keyword} meme",
        "{keyword} meme image",
        "{keyword} viral",
        "{keyword} trending",
        "{keyword} popular",
        "{keyword} famous",
        "{keyword} iconic",
        "{keyword} legendary",
    ]


def get_professional_variations() -> List[str]:
    """Professional and technical variations"""
    return [
        "{keyword} professional",
        "{keyword} professional photo",
        "{keyword} commercial",
        "{keyword} editorial",
        "{keyword} documentary",
        "{keyword} journalistic",
        "{keyword} news",
        "{keyword} press",
        "{keyword} amateur",
        "{keyword} amateur photo",
        "{keyword} candid",
        "{keyword} casual",
        "{keyword} lifestyle",
        "{keyword} portrait",
        "{keyword} headshot",
        "{keyword} product shot",
        "{keyword} promotional",
        "{keyword} marketing",
        "{keyword} advertising",
    ]


def get_camera_technique_variations() -> List[str]:
    """Camera and photography technique variations"""
    return [
        "{keyword} close up",
        "{keyword} close up photo",
        "{keyword} closeup",
        "{keyword} macro",
        "{keyword} macro photo",
        "{keyword} wide shot",
        "{keyword} wide shot photo",
        "{keyword} wide angle",
        "{keyword} panoramic",
        "{keyword} telephoto",
        "{keyword} zoom",
        "{keyword} zoomed-in image",
        "{keyword} detail",
        "{keyword} detailed",
        "{keyword} full frame",
        "{keyword} cropped",
        "{keyword} overhead",
        "{keyword} bird's eye view",
        "{keyword} aerial",
        "{keyword} top view",
        "{keyword} side view",
        "{keyword} side image",
        "{keyword} front view",
        "{keyword} back view",
        "{keyword} profile",
        "{keyword} angle",
        "{keyword} perspective",
        "{keyword} low angle",
        "{keyword} high angle",
    ]


def get_focus_sharpness_variations() -> List[str]:
    """Focus and sharpness variations"""
    return [
        "{keyword} sharp",
        "{keyword} sharp image",
        "{keyword} focused",
        "{keyword} in focus",
        "{keyword} blurry",
        "{keyword} blurry image",
        "{keyword} out of focus",
        "{keyword} soft focus",
        "{keyword} bokeh",
        "{keyword} depth of field",
        "{keyword} shallow depth",
        "{keyword} motion blur",
        "{keyword} crisp",
        "{keyword} detailed",
    ]


def get_color_variations() -> List[str]:
    """Color variations"""
    return [
        "{keyword} colorful",
        "{keyword} vibrant colors",
        "{keyword} bright colors",
        "{keyword} pastel colors",
        "{keyword} neon colors",
        "{keyword} rainbow",
        "{keyword} multicolored",
        "{keyword} black and white",
        "{keyword} grayscale",
        "{keyword} monochrome",
        "{keyword} sepia",
        "{keyword} red",
        "{keyword} blue",
        "{keyword} green",
        "{keyword} yellow",
        "{keyword} orange",
        "{keyword} purple",
        "{keyword} pink",
        "{keyword} brown",
        "{keyword} gold",
        "{keyword} silver",
        "{keyword} bronze",
        "{keyword} metallic",
    ]


def get_lighting_variations() -> List[str]:
    """Lighting variations"""
    return [
        "{keyword} bright",
        "{keyword} well lit",
        "{keyword} illuminated",
        "{keyword} dark",
        "{keyword} dimly lit",
        "{keyword} shadow",
        "{keyword} silhouette",
        "{keyword} backlit",
        "{keyword} sunny",
        "{keyword} sunlight",
        "{keyword} golden hour",
        "{keyword} sunset",
        "{keyword} sunrise",
        "{keyword} cloudy",
        "{keyword} overcast",
        "{keyword} night",
        "{keyword} evening",
        "{keyword} dawn",
        "{keyword} dusk",
        "{keyword} natural light",
        "{keyword} daylight",
        "{keyword} artificial light",
        "{keyword} studio lighting",
        "{keyword} flash",
        "{keyword} neon light",
        "{keyword} candlelight",
        "{keyword} firelight",
        "{keyword} moonlight",
        "{keyword} dramatic lighting",
        "{keyword} soft lighting",
        "{keyword} harsh lighting",
        "{keyword} rim lighting",
        "{keyword} ambient light",
    ]


def get_location_variations() -> List[str]:
    """Location and setting variations"""
    return [
        "{keyword} indoor",
        "{keyword} inside",
        "{keyword} interior",
        "{keyword} outdoor",
        "{keyword} outside",
        "{keyword} exterior",
        "{keyword} studio",
        "{keyword} home",
        "{keyword} house",
        "{keyword} office",
        "{keyword} workplace",
        "{keyword} nature",
        "{keyword} landscape",
        "{keyword} cityscape",
        "{keyword} urban",
        "{keyword} rural",
        "{keyword} street",
        "{keyword} park",
        "{keyword} garden",
        "{keyword} beach",
        "{keyword} mountain",
        "{keyword} forest",
        "{keyword} desert",
        "{keyword} field",
        "{keyword} room",
        "{keyword} kitchen",
        "{keyword} bedroom",
        "{keyword} bathroom",
        "{keyword} living room",
        "{keyword} garage",
        "{keyword} basement",
        "{keyword} attic",
        "{keyword} balcony",
        "{keyword} terrace",
        "{keyword} roof",
        "{keyword} window",
        "{keyword} door",
        "{keyword} wall",
        "{keyword} floor",
        "{keyword} ceiling",
    ]


def get_background_variations() -> List[str]:
    """Background variations"""
    return [
        "{keyword} white background",
        "{keyword} black background",
        "{keyword} gray background",
        "{keyword} grey background",
        "{keyword} blue background",
        "{keyword} green background",
        "{keyword} red background",
        "{keyword} yellow background",
        "{keyword} pink background",
        "{keyword} purple background",
        "{keyword} transparent background",
        "{keyword} solid background",
        "{keyword} gradient background",
        "{keyword} textured background",
        "{keyword} plain background",
        "{keyword} simple background",
        "{keyword} clean background",
        "{keyword} minimal background",
        "{keyword} neutral background",
        "{keyword} colorful background",
        "{keyword} busy background",
        "{keyword} blurred background",
        "{keyword} natural background",
        "{keyword} isolated",
        "{keyword} cutout",
        "{keyword} no background",
    ]


def get_size_format_variations() -> List[str]:
    """Size and format variations"""
    return [
        "{keyword} small",
        "{keyword} large",
        "{keyword} tiny",
        "{keyword} huge",
        "{keyword} massive",
        "{keyword} giant",
        "{keyword} miniature",
        "{keyword} full size",
        "{keyword} life size",
        "{keyword} thumbnail",
        "{keyword} icon",
        "{keyword} banner",
        "{keyword} header",
        "{keyword} cover",
        "{keyword} profile picture",
        "{keyword} avatar",
        "{keyword} logo",
        "{keyword} symbol",
        "{keyword} sign",
        "{keyword} poster",
        "{keyword} flyer",
        "{keyword} card",
        "{keyword} stamp",
        "{keyword} sticker",
    ]


def get_texture_material_variations() -> List[str]:
    """Texture and material variations"""
    return [
        "{keyword} smooth",
        "{keyword} rough",
        "{keyword} textured",
        "{keyword} glossy",
        "{keyword} matte",
        "{keyword} shiny",
        "{keyword} reflective",
        "{keyword} transparent",
        "{keyword} opaque",
        "{keyword} metallic",
        "{keyword} wooden",
        "{keyword} plastic",
        "{keyword} glass",
        "{keyword} fabric",
        "{keyword} leather",
        "{keyword} paper",
        "{keyword} stone",
        "{keyword} concrete",
        "{keyword} ceramic",
        "{keyword} rubber",
        "{keyword} fur",
        "{keyword} skin",
        "{keyword} hair",
    ]


def get_condition_age_variations() -> List[str]:
    """Condition and age variations"""
    return [
        "{keyword} new",
        "{keyword} old",
        "{keyword} used",
        "{keyword} worn",
        "{keyword} damaged",
        "{keyword} broken",
        "{keyword} cracked",
        "{keyword} scratched",
        "{keyword} dirty",
        "{keyword} clean",
        "{keyword} fresh",
        "{keyword} stale",
        "{keyword} rusty",
        "{keyword} faded",
        "{keyword} pristine",
        "{keyword} perfect",
        "{keyword} flawless",
        "{keyword} imperfect",
        "{keyword} weathered",
        "{keyword} aged",
    ]


def get_quantity_arrangement_variations() -> List[str]:
    """Quantity and arrangement variations"""
    return [
        "{keyword} single",
        "{keyword} one",
        "{keyword} multiple",
        "{keyword} many",
        "{keyword} few",
        "{keyword} several",
        "{keyword} bunch",
        "{keyword} group",
        "{keyword} collection",
        "{keyword} set",
        "{keyword} pair",
        "{keyword} stack",
        "{keyword} pile",
        "{keyword} row",
        "{keyword} line",
        "{keyword} circle",
        "{keyword} pattern",
        "{keyword} arranged",
        "{keyword} scattered",
        "{keyword} organized",
        "{keyword} random",
        "{keyword} symmetrical",
        "{keyword} asymmetrical",
    ]


def get_generic_quality_variations() -> List[str]:
    """Generic quality descriptors"""
    return [
        "{keyword} best",
        "{keyword} worst",
        "{keyword} perfect",
        "{keyword} ideal",
        "{keyword} typical",
        "{keyword} standard",
        "{keyword} basic",
        "{keyword} premium",
        "{keyword} luxury",
        "{keyword} cheap",
        "{keyword} expensive",
        "{keyword} rare",
        "{keyword} common",
        "{keyword} unique",
        "{keyword} special",
        "{keyword} ordinary",
        "{keyword} extraordinary",
        "{keyword} exceptional",
        "{keyword} normal",
        "{keyword} average",
        "{keyword} superior",
        "{keyword} inferior",
        "{keyword} excellent",
        "{keyword} good",
        "{keyword} bad",
        "{keyword} mediocre",
        "{keyword} outstanding",
        "{keyword} remarkable",
        "{keyword} notable",
        "{keyword} significant",
        "{keyword} important",
        "{keyword} minor",
        "{keyword} major",
        "{keyword} primary",
        "{keyword} secondary",
        "{keyword} main",
        "{keyword} central",
        "{keyword} featured",
        "{keyword} highlighted",
        "{keyword} emphasized",
        "{keyword} focused",
        "{keyword} prominent",
        "{keyword} subtle",
        "{keyword} obvious",
        "{keyword} hidden",
        "{keyword} visible",
        "{keyword} clear",
        "{keyword} unclear",
        "{keyword} distinct",
        "{keyword} vague",
        "{keyword} precise",
        "{keyword} accurate",
        "{keyword} exact",
        "{keyword} approximate",
        "{keyword} rough",
        "{keyword} smooth"
    ]


def get_search_variations() -> List[str]:
    """
    Get the list of search variations.

    Returns:
        List of search variations
    """
    return (
            get_basic_variations() +
            get_quality_variations() +
            get_style_variations() +
            get_time_period_variations() +
            get_emotional_aesthetic_variations() +
            get_meme_culture_variations() +
            get_professional_variations() +
            get_camera_technique_variations() +
            get_focus_sharpness_variations() +
            get_color_variations() +
            get_lighting_variations() +
            get_location_variations() +
            get_background_variations() +
            get_size_format_variations() +
            get_texture_material_variations() +
            get_condition_age_variations() +
            get_quantity_arrangement_variations() +
            get_generic_quality_variations()
    )


def get_engines() -> List[Dict[str, Any]]:
    """
    Get the list of engines with their configurations.

    Returns:
        List of dictionaries containing engine configurations
    """
    return [
        {
            'name': 'google',
            'offset_range': (0, 20),
            'variation_step': 20
        },
        {
            'name': 'bing',
            'offset_range': (0, 30),
            'variation_step': 10
        },
        {
            'name': 'baidu',
            'offset_range': (10, 50),
            'variation_step': 15
        }
    ]


@dataclass
class DatasetGenerationConfig:
    """
    Configuration for dataset generation.

    This class holds all configuration options for the dataset generation process,
    including paths, limits, and feature flags.

    Attributes:
        config_path: Path to the configuration file
        max_images: Maximum number of images to download per keyword
        output_dir: Custom output directory (None uses dataset_name from config)
        integrity: Whether to perform image integrity checks
        max_retries: Maximum number of retry attempts for failed downloads
        continue_from_last: Whether to continue from previous run
        cache_file: Path to cache file for progress tracking
        keyword_generation: Mode for keyword generation
        ai_model: AI model to use for keyword generation
        generate_labels: Whether to generate label files for images
        dataset_name: Name of the dataset (loaded from config file)
        search_variations: List of search variation templates for image searches
    """
    config_path: str
    max_images: int = 10
    output_dir: Optional[str] = None
    integrity: bool = True
    max_retries: int = 5
    continue_from_last: bool = False
    cache_file: str = DEFAULT_CACHE_FILE
    keyword_generation: KEYWORD_MODE = "auto"
    ai_model: AI_MODELS = "gpt4-mini"
    generate_labels: bool = True
    dataset_name: str = ""
    search_variations: list = None
