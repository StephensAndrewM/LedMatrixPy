import argparse
import logging

from deps import Dependencies
from timeslide import TimeSlide

parser = argparse.ArgumentParser(description='Run an LED Matrix slideshow.')
parser.add_argument('--generate_images', action='store_true', help='Generates slide images instead of running as slideshow.')
parser.add_argument('--debug_log', action='store_true', help='Prints debug-level logging information.')

# Size of the matrix display.
SCREEN_WIDTH=128
SCREEN_HEIGHT=32

def main():
    args = parser.parse_args()
    
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    if args.debug_log:
        logging.setLevel(logging.DEBUG)

    if args.generate_images:
        generate_images()
    else:
        run_slideshow()

def generate_images():
    deps = Dependencies()
    slide = TimeSlide(deps)
    print(slide.draw())

def run_slideshow():
    pass

if __name__ == "__main__":
    main()