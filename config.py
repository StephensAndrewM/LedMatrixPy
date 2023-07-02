import json
from os import path
from typing import Dict, List, TypedDict

SlideConfig = TypedDict('SlideConfig', {
    "type": str,
    "options": Dict[str, str]
})

Config = TypedDict('Config', {
    "slide_advance": int,
    "transition_millis": int,
    "static_slide": SlideConfig,
    "rotating_slides": List[SlideConfig],
})


def load_config() -> Config:
    script_dir = path.dirname(path.realpath(__file__))
    config_file = path.join(script_dir, "config.json")
    with open(config_file) as f:
        config = json.load(f)  # type: ignore

        # Verify a few required properties are present.
        assert "static_slide" in config
        assert "rotating_slides" in config
        assert len(config["rotating_slides"]) > 0

        return config
