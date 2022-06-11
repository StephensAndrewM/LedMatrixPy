import argparse
import logging
from time import sleep
from typing import List

from abstractslide import AbstractSlide
from config import Config, load_config
from deps import Dependencies
from display import Display
from imagewriter import write_grid_to_file
from slideshow import Slideshow
from timeslide import TimeSlide

parser = argparse.ArgumentParser(description='Run an LED Matrix slideshow.')
parser.add_argument('--generate_images', action='store_true',
                    help='Generates slide images instead of running as slideshow.')
parser.add_argument('--debug_log', action='store_true',
                    help='Prints debug-level logging information.')

# Size of the matrix display.
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 32


def main() -> None:
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    if args.debug_log:
        logging.StreamHandler().setLevel(logging.DEBUG)

    if args.generate_images:
        generate_images()
    else:
        run_slideshow()


def generate_images() -> None:
    deps = Dependencies()
    slide = TimeSlide(deps)
    write_grid_to_file("TimeSlide", slide.draw())


def run_slideshow() -> None:
    config = load_config()
    deps = Dependencies()
    slides = create_slides_from_config(config, deps)
    display = Display()
    slideshow = Slideshow(config, display, deps.get_requester(), slides)

    # Run forever
    sleep(1000)


def create_slides_from_config(config: Config, deps: Dependencies) -> List[AbstractSlide]:
    slides: List[AbstractSlide] = []
    for slide_config in config["slides"]:
        if slide_config["type"] == "TimeSlide":
            slides.append(TimeSlide(deps))
        else:
            logging.warning("Unknown slide type %s", slide_config["type"])
    return slides


if __name__ == "__main__":
    main()
