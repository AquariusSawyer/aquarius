import re
from functools import partial
import logging

import asyncio
import uvloop
from httptools import HttpParserError, HttpRequestParser

try:
    import ujson as json
except ImportError:
    import json

from inspect import iscoroutinefunction


VERSION = "1.0"

RESPONSE_HERD = (
    "HTTP/1.1 {status}\r\n"
    "Content-Type: {content_type}; charset=utf-8\r\n"
    "Server: {server}\r\n"
    "{cookie}"
    "Content-Length:{length}\r\n\r\n"
)


Logger = logging.getLogger("server")


class ResponseBase:

    def __init__(self, status_code: int=200, body: str=None, body_type=None):

        self.status_code = status_code
        self.body = body
        self.body_type = body_type

        self._cookie = []

    def bytes_response(self):
        body = bytes(self.body, encoding='utf-8')
        nums_body = len(body)

        set_hd = RESPONSE_HERD.format(
            status=self.status_code,
            content_type=self.body_type,
            server="aquarius %s" % VERSION,
            cookie=self.__cookie_set(),
            length=nums_body
        )
        return bytes(set_hd, encoding='utf-8') + body + b'\r\n\r\n'

    def set_cookie(self, key, value, path="/"):
        cookie = 'Set-cookie: %(key)s=%(value)s; path=%(path)s\r\n' % {"key": key, "value": value, "path": path}
        self._cookie.append(cookie)
        return self

    def __cookie_set(self): return "".join(self._cookie)

    def __repr__(self): return "<%s : %s>" % (self.__class__.__name__, str(self.status_code))

    def __str__(self): return self.bytes_response().decode('utf-8')


class HTTPResponse(ResponseBase):
    
    def __call__(self, content):
        self.body = content

        if isinstance(content, (dict, list, tuple)):
            self.body = json.dumps(content)
            self.body_type = 'application/json'

        elif isinstance(content, str):
            self.body = content
            self.body_type = 'text/html'

        return self.bytes_response()


class Request(object):

    __slots__ = ("uri", "version", "method", "headers", "body", "has_token")

    def __init__(self):
        self.uri = ""
        self.version = "1.1"
        self.method = ""
        self.headers = {}
        self.body = []

    @property
    def url(self):
        return self.uri.split("?", 1)[0]

    def __query_string_parameters(self):
        _query_string = {}

        try:
            query_string = self.uri.split("?", 1)[1]
            for string in query_string.split("&"):
                parameters = string.split("=", 1)
                name, value = parameters if len(parameters) == 2 else parameters.append("")
                _query_string.update({name: value})
        finally:
            return _query_string

    @property
    def request_args(self):
        return self.__query_string_parameters()

    def to_response(self, content, status=200):
        Logger.info('\"{method} {uri} HTTP/{version}\" {status}'.format(method=self.method, uri=self.uri, status=status, version=self.version))

        return HTTPResponse(status)(content)


class HttpProtocol(asyncio.Protocol):

    __slots__ = ("_route_", "_loop", "_transport", "_parser", "_request")

    def __init__(self, event_loop=None, route=None):
        self._route = route
        self._loop = event_loop
        self._transport = None
        self._parser = HttpRequestParser(self)
        self._request = Request()

    def connection_made(self, transport):
        self._transport = transport

    def data_received(self, data):
        try:
            self._parser.feed_data(data)
        except HttpParserError:
            pass

    def connection_lost(self, exc):
        self._transport.close()

    def on_url(self, uri):
        self._request.uri = uri.decode()

    def on_header(self, name, value):
        self._request.headers[name] = value

    def on_headers_complete(self):

        self._request.version = self._parser.get_http_version()
        self._request.method = self._parser.get_method().decode()

    def on_body(self, body):
        self._request.body.append(body)

    def on_message_complete(self):
        if self._request.body:
            self._request.body = b"".join(self._request.body)

        self._loop.create_task(
            self.start_response(request=self._request, transport=self._transport)
        )

    async def start_response(self, transport, request):

        view_func = self._route._router.get(request.url, None)

        if view_func is None:
            transport.write(b'HTTP/1.1 404 Not Found\r\nServer: aquarius\r\nContent-Length:9\r\n\r\nNot Found\r\n\r\n')

        else:
            view_obj = view_func.__dict__
            if request.method not in view_obj.get("allowed_method"):
                transport.close()

            if view_obj.get("async"):
                content = await view_func(request)
            else:
                content = view_func(request)

            try:
                transport.write(content)
            except Exception as e:
                transport.close()

        if request.version == "1.0":
            transport.close()


class RouterConfig:

    __slots__ = ["_router"]

    class Settings:
        allowed_method = ["GET", "POST", "PUT", "DELETE"]

    def __init__(self):

        self._router = {}

    def __str__(self):

        router_strings = []

        for path, view in self._router.items():

            view_string = "  "
            view_string += view.__name__
            view_string += "  "
            view_string += "async" if view.async else "sync"
            router_strings.append(path + view_string)

        return "\n".join(router_strings)

    @property
    def allowed_method(self):
        return self.__class__.Settings.allowed_method

    def update(self, path, view):
        self._router[path] = view

    def add(self, path, required_method=None):

        def __router__add(view):

            view.async = iscoroutinefunction(view)
            view.allowed_method = required_method if isinstance(required_method, tuple) else self.allowed_method

            self.update(path, view)

        return __router__add


class Aquarius:

    class Settings:

        router_new = RouterConfig
        protocol = HttpProtocol

    def __init__(self, name=None, protocol=None, router_cls=None):

        self._protocol = protocol if protocol else self.__class__.Settings.protocol
        self._router = router_cls if router_cls else self.__class__.Settings.router_new()

        self._name = name
        self._loop = None

    def run(self, host="0.0.0.0", port=8000):

        if self._name != "__main__":
            return

        Logger.info("aquarius start")

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        loop = asyncio.get_event_loop()

        self._loop = loop

        _protocol = partial(self._protocol, loop, self._router)

        server_coro = loop.create_server(_protocol, host=host, port=port)
        server = loop.run_until_complete(server_coro)
        try:
            loop.run_until_complete(server.wait_closed())
        except KeyboardInterrupt:
            Logger.info("aquarius Byebye")
        finally:
            loop.close()

    @property
    def router(self):
        return self._router


if __name__ == '__main__':

    app = Aquarius(__name__)

    @app.router.add("/test/")
    def index(request):
        return request.to_response("/test")

    app.run()
