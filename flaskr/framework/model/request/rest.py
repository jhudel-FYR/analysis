import json

from flask import current_app, Response


def json_response(status: int, data: str) -> Response:
    return current_app.response_class(
        response=data,
        status=status,
        mimetype='application/json'
    )


def bad_request(message: str) -> Response:
    return json_response(400, json.dumps(dict(message=message)))


def not_found() -> Response:
    return json_response(404, '')


def response(data: object) -> Response:
    return json_response(200, data)


def success() -> Response:
    return json_response(200, json.dumps(dict(message='success')))


def error() -> Response:
    message = "A server error has occured, please check the logs"
    return json_response(503, json.dumps(dict(message=message)))
