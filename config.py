import json
from os import path
from typing import Dict, List, TypedDict

_SlideConfig = TypedDict('_SlideConfig', {
    "type": str,
    "options": Dict[str, str]
})

Config = TypedDict('Config', {
    "slide_advance": int,
    "slides": List[_SlideConfig]
})


def load_config() -> Config:
    script_dir = path.dirname(path.realpath(__file__))
    config_file = path.join(script_dir, "config.json")
    with open(config_file) as f:
        return json.load(f)  # type: ignore
