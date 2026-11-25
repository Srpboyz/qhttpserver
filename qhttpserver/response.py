from http import HTTPStatus as StatusCode
from typing import Callable
import json as serializer

from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtNetwork import QTcpSocket
from .request import HttpRequest


class HttpResponse:
    def __init__(
        self,
        status: StatusCode = StatusCode.OK,
        headers: dict | None = None,
        body: bytes | str | None = None,
        json: dict | list | None = None,
    ):
        self.status = status
        self.headers = headers or {}

        if json is not None:
            self.body = serializer.dumps(json).encode()
        elif isinstance(body, str):
            self.body = body.encode()
        elif body is None:
            self.body = b""
        else:
            self.body = body


class AsyncHttpResponse(QObject):
    finished = pyqtSignal((QTcpSocket, HttpRequest, HttpResponse))
    error_occured = pyqtSignal(Exception)

    def __init__(self, request: HttpRequest, func: Callable, *args, **kwargs) -> None:
        super().__init__()

        if not isinstance(request, HttpRequest):
            raise TypeError(f"Expected type HttpRequest not `{type(request)}`")

        self.request = request
        self.func = func
        self.extra_args = args
        self.extra_kwargs = kwargs
        self._client = None

    def wait_for_signal(self, *args) -> None:
        sender = self.sender()
        try:
            response = self.func(
                self.request, sender, *args, *self.extra_args, **self.extra_kwargs
            )
        except Exception as e:
            return self.error_occured.emit(e)

        if not isinstance(response, HttpResponse):
            return self.error_occured.emit(
                TypeError(f"Expected type `HttpResponse` not `{type(response)}`"),
            )

        self.finished.emit(self._client, self.request, response)

    def _set_client(self, client: QTcpSocket):
        self._client = client
        client.disconnected.connect(self.deleteLater)


def convert_response_to_http(response: HttpResponse) -> bytes:
    status = response.status
    headers = "\r\n".join(f"{key}: {value}" for key, value in response.headers.items())
    if len(headers):
        headers += "\r\n"
    body = response.body.encode() if isinstance(response.body, str) else response.body
    return f"HTTP/1.1 {status} {status.phrase}\r\n{headers}\r\n".encode() + body
