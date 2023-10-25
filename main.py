import argparse
import logging
import subprocess
import time
from time import sleep

import requests
from PIL import ImageDraw  # type: ignore

from abstractslide import AbstractSlide
from christmasslide import ChristmasSlide
from config import SlideConfig, load_config
from controller import Controller
from deps import Dependencies
from display import Display, MatrixDisplay
from drawing import create_slide
from forecastslide import ForecastSlide
from nycsubwayslide import NycSubwaySlide
from imagewriter import write_grid_to_file
from show import Show
from timeandtemperatureslide import TimeAndTemperatureSlide

parser = argparse.ArgumentParser(description='Run an LED Matrix show.')
parser.add_argument('--generate_images', action='store_true',
                    help='Generates slide images instead of running interactively.')
parser.add_argument('--debug_log', action='store_true',
                    help='Prints debug-level logging information.')
parser.add_argument('--fake_display', action='store_true',
                    help='Uses a no-op display instead of expecting hardware.')


def main() -> None:
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    if args.debug_log:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.generate_images:
        generate_images()
    else:
        run_show(args.fake_display)


def generate_images() -> None:
    config = load_config()
    deps = Dependencies()
    static_slide = create_slide_from_config(config["static_slide"], deps)
    rotating_slides = [create_slide_from_config(
        slide_config, deps) for slide_config in config["rotating_slides"]]
    deps.get_requester().start()
    sleep(5)
    for slide in [static_slide, *rotating_slides]:
        img = create_slide(slide.get_type())
        slide.draw(img)
        filename = type(slide).__name__
        write_grid_to_file(filename, img)
    deps.get_requester().stop()


def run_show(fake_display: bool) -> None:
    config = load_config()
    deps = Dependencies()
    static_slide = create_slide_from_config(config["static_slide"], deps)
    rotating_slides = [create_slide_from_config(
        slide_config, deps) for slide_config in config["rotating_slides"]]
    display = Display() if fake_display else MatrixDisplay()
    show = Show(config, display, deps.get_requester(),
                static_slide, rotating_slides)

    # Run startup tasks.
    wait_for_network()
    sync_system_time()

    # Signal the show it's ready to start, hand control to controller.
    show.startup_complete()
    controller = Controller(show)
    controller.run_until_shutdown()


def create_slide_from_config(slide_config: SlideConfig, deps: Dependencies) -> AbstractSlide:
    type = slide_config.get("type", "")
    options = slide_config.get("options", {})

    if type == "TimeAndTemperatureSlide":
        return TimeAndTemperatureSlide(deps, options)
    if type == "ForecastSlide":
        return ForecastSlide(deps, options)
    elif type == "ChristmasSlide":
        return ChristmasSlide(deps)
    elif type == "NycSubwaySlide":
        return NycSubwaySlide(deps, options)
    else:
        raise AssertionError("Unknown slide type %s", slide_config["type"])


def wait_for_network() -> None:
    attempts = 1
    while True:
        try:
            response = requests.get(
                "http://clients3.google.com/generate_204")
            if response.status_code == 204:
                logging.info(
                    "Internet connection present after %d checks", attempts)
                return
        except Exception as e:
            logging.debug("Exception while checking for connection: %s", e)
        finally:
            attempts += 1
            time.sleep(5)


def sync_system_time() -> None:
    p = subprocess.run(["/usr/sbin/ntpdate", "-s", "time.google.com"])
    if p.returncode != 0:
        logging.warning(
            "Failed NTP time synchronization with exit code %d", p.returncode)


if __name__ == "__main__":
    main()
