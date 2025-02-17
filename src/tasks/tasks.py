from time import sleep
from typing import List

from pydantic import StrictStr, StrictInt

from models.response_value import ResponseValue
from models.response import Response


def example(input: List[Response]) -> List[Response]:
    sleep(3)
    output: List[Response] = []
    row = Response(
        setId = StrictStr("output_set"),
        id = StrictStr("output"),
        status = StrictStr("CODING_COMPLETE"),
        value = ResponseValue("output"),
        code = StrictInt(10),
        score = StrictInt(10)
    )
    output.append(row)
    return output
