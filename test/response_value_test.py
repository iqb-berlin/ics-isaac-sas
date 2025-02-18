from models.response import Response
from models.response_value import ResponseValue
input_str = '{ "setId": "set1", "id": "a", "value": "a", "status": "VALUE_CHANGED" }'
rv = Response.from_json(input_str)
print(rv)
