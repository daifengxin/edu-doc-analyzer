from typing import Any, Union, TypeVar, Generic

from pydantic import BaseModel

DataModelType = TypeVar("DataModelType")


class DocanalyzerResponse(BaseModel, Generic[DataModelType]):
    code: int
    message: str
    data: DataModelType


def response_formatter(data: Union[DocanalyzerResponse, Any] = None):
    if isinstance(data, DocanalyzerResponse):
        return data
    else:
        return DocanalyzerResponse(code=200, message="Success", data=data if data is not None else {})


def error_response(code: int, message: str):
    return DocanalyzerResponse(code=code, message=message, data={}).model_dump()
