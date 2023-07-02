import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

from show import Show


class ControllerRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self) -> None:
        if self.path == "/start":
            logging.info("Starting show")
            self.server.show.start()  # type: ignore
        elif self.path == "/stop":
            logging.info("Stopping show")
            self.server.show.stop()  # type: ignore
        elif self.path == "/freeze":
            logging.info("Freezing show")
            self.server.show.freeze()  # type: ignore
        elif self.path == "/unfreeze":
            logging.info("Unfreezing show")
            self.server.show.unfreeze()  # type: ignore
        elif self.path == "/shutdown":
            logging.info("Shutting down show")
            self.server.show.stop()  # type: ignore
            self.server.stopped = True  # type: ignore
        else:
            logging.warning("Unknown controller endpoint %s", self.path)
            self.send_response(200)

    def do_GET(self) -> None:
        self.send_response(405)


class ControllerServer(HTTPServer):
    show: Show
    stopped: bool

    def __init__(self, show: Show) -> None:
        super(ControllerServer, self).__init__(
            ("localhost", 5000), ControllerRequestHandler
        )
        self.show = show
        self.stopped = False

    def serve_forever(self, poll_interval: float = 0.5) -> None:
        while not self.stopped:
            self.handle_request()


class Controller:
    server: ControllerServer

    def __init__(self, show: Show) -> None:
        self.server = ControllerServer(show)

    def run_until_shutdown(self) -> None:
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.server_close()
