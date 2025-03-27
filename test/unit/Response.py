from models.response import Response
import warnings

warnings.filterwarnings( action='error', message='')

def test(input: str) -> str:
    output = Response.from_json(input).to_json()
    print('in  : ' + input)
    print('out : ' + output)
    assert input == output


test('{"setId": "user1", "id": "var1", "status": "VALUE_CHANGED", "value": "string"}')
test('{"setId": "user1", "id": "var1", "status": "VALUE_CHANGED", "value": ["string", "array"]}')
test('{"setId": "user1", "id": "var1", "status": "VALUE_CHANGED", "value": null}')
test('{"setId": "user1", "id": "var1", "status": "VALUE_CHANGED", "value": 1}')
test('{"setId": "user1", "id": "var1", "status": "VALUE_CHANGED", "value": [1, 2]}')


