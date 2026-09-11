from dataclasses import dataclass
from http import HTTPStatus
from typing import Any


@dataclass
class ResultDTO:
    data: Any
    status_code: int

    @classmethod
    def ok(cls, data: Any) -> "ResultDTO":
        return cls(data=data, status_code=HTTPStatus.OK)

    @classmethod
    def created(cls, data: Any) -> "ResultDTO":
        return cls(data=data, status_code=HTTPStatus.CREATED)

    @classmethod
    def bad_request(cls, error: str) -> "ResultDTO":
        return cls(data={"error": error}, status_code=HTTPStatus.BAD_REQUEST)

    @classmethod
    def unauthorized(cls, error: str) -> "ResultDTO":
        return cls(data={"error": error}, status_code=HTTPStatus.UNAUTHORIZED)

    @classmethod
    def conflict(cls, error: str) -> "ResultDTO":
        return cls(data={"error": error}, status_code=HTTPStatus.CONFLICT)