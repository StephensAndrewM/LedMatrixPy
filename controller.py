import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

from slideshow import Slideshow


class ControllerRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self) -> None:
        if self.path == "/start":
            logging.info("Starting slideshow")
            self.server.slideshow.start()  # type: ignore
        elif self.path == "/stop":
            logging.info("Stopping slideshow")
            self.server.slideshow.stop()  # type: ignore
        elif self.path == "/freeze":
            logging.info("Freezing slideshow")
            self.server.slideshow.freeze()  # type: ignore
        elif self.path == "/unfreeze":
            logging.info("Unfreezing slideshow")
            self.server.slideshow.unfreeze()  # type: ignore
        elif self.path == "/shutdown":
            logging.info("Shutting down slideshow")
            self.server.slideshow.stop()  # type: ignore
            self.server.stopped = True  # type: ignore
        else:
            logging.warning("Unknown controller endpoint %s", self.path)
            self.send_response(200)

    def do_GET(self) -> None:
        self.send_response(405)


class ControllerServer(HTTPServer):
    slideshow: Slideshow
    stopped: bool

    def __init__(self, slideshow: Slideshow) -> None:
        super(ControllerServer, self).__init__(
            ("localhost", 5000), ControllerRequestHandler
        )
        self.slideshow = slideshow
        self.stopped = False

    def serve_forever(self, poll_interval: float = 0.5) -> None:
        while not self.stopped:
            self.handle_request()


class Controller:
    server: ControllerServer

    def __init__(self, slideshow: Slideshow) -> None:
        self.server = ControllerServer(slideshow)

    def run_until_shutdown(self) -> None:
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.server_close()
