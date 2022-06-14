from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from slideshow import Slideshow


class ControllerRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/start":
            logging.info("Starting slideshow")
            self.server.slideshow.start()
        elif self.path == "/stop":
            logging.info("Stopping slideshow")
            self.server.slideshow.stop()
        elif self.path == "/freeze":
            logging.info("Freezing slideshow")
            self.server.slideshow.freeze()
        elif self.path == "/unfreeze":
            logging.info("Unfreezing slideshow")
            self.server.slideshow.unfreeze()
        elif self.path == "/shutdown":
            logging.info("Shutting down slideshow")
            self.server.slideshow.stop()
            self.server.stopped = True
        else:
            logging.warning("Unknown controller endpoint %s", self.path)
            self.send_response(200)

    def do_GET(self):
        self.send_response(405)


class ControllerServer(HTTPServer):
    slideshow: Slideshow
    stopped: bool

    def __init__(self, slideshow):
        super(("localhost", 5000), ControllerRequestHandler)
        self.slideshow = slideshow
        self.stopped = False

    def serve_forever(self):
        while not self.stopped:
            self.handle_request()


class Controller:
    server: ControllerServer

    def __init__(self, slideshow) -> None:
        self.server = ControllerServer(slideshow)

    def run_until_shutdown(self) -> None:
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.server_close()
