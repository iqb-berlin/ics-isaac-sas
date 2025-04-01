import json
from time import sleep
from typing import List

from pydantic import StrictStr, StrictInt, BaseModel

from features.data import ShortAnswerInstance
from isaac_sas import core
from isaac_sas.models import LanguageDataRequest
from models.code import Code
from models.response import Response
from models.train import Train
from worker.common import print_in_worker


class ResponseRow(BaseModel):
    response: Response
    rowToCodeId: int | None

def is_codable(response: Response) -> bool:
    # TODO filter specific var
    # TODO filter status
    return isinstance(response.value, str)

def analyze_responses(responses: List[Response]) -> List[ResponseRow]:
    rows : List[ResponseRow] = []
    rows_to_code_counter = 0
    for (i, response) in enumerate(responses):
        rows.append(
            ResponseRow(
                response = response,
                rowToCodeId = rows_to_code_counter if is_codable(response) else None
            )
        )
        if is_codable(response):
            rows_to_code_counter += 1
    return rows

def filter_uncodable_rows(responseRow: ResponseRow) -> bool:
    return responseRow.rowToCodeId is not None

def filter_responses(responses: List[Response]) -> List[Response]:
    return list(filter(is_codable, responses))


defaultLabels = [
    "False",
    "True"
]

def label_to_code(label: str) -> StrictInt:
    if label not in defaultLabels:
        raise ValueError(f"Label {label} is not supported.")
    return defaultLabels.index(label)

def code_to_label(code: int) -> str:
    if code > len(defaultLabels) or code < 0:
        raise ValueError(f"Code {code} is not supported.")
    return defaultLabels[code]


def code(instructions: Code, input_data: List[Response]) -> List[Response]:
    def convert_to_sai(row: ResponseRow) -> ShortAnswerInstance:
        return ShortAnswerInstance(
            taskId = 'test',
            itemId = 'test',
            itemPrompt = '',
            itemTargets = [],
            learnerId = row.response.set_id,
            answer = row.response.value if isinstance(row.response.value, str) else '',
        )

    response_rows = analyze_responses(input_data)

    ldr = LanguageDataRequest(
        instances = list(map(convert_to_sai, list(filter(filter_uncodable_rows, response_rows)))),
        modelId = 'test' # TODO
    )

    result = core.predict_from_answers(ldr)

    output: List[Response] = []
    for row in response_rows:
        response = row.response
        if row.rowToCodeId is not None:
            class_probabilities = result.predictions[row.rowToCodeId].classProbabilities
            response.status = "CODING_SEMI_COMPLETE"
            response.codingProbabilities = { label_to_code(k): v for k, v in class_probabilities.items() }
            response.code = None
            response.score = None
        output.append(response)
    return output



def train(instructions: Train, input_data: List[Response]) -> str:
    unique_codes = { obj.code for obj in input_data }
    if len(unique_codes) != 2:
        print_in_worker(unique_codes)
        raise Exception('Insufficient training data: exactly two different codes must be given')

    def convert(response: Response) -> ShortAnswerInstance:
        return ShortAnswerInstance(
            taskId = 'test',
            itemId = 'test',
            itemPrompt = instructions.item_prompt,
            itemTargets = instructions.item_targets,
            learnerId = response.set_id,
            answer = response.value if isinstance(response.value, str) else '',
            label = code_to_label(response.code)  # TODO make get labels from instructions
        )

    """
    [
    ShortAnswerInstance(taskId='test', itemId='test', itemPrompt='four', itemTargets=['four'], learnerId='auto', answer='four', label='True'), 
    ShortAnswerInstance(taskId='test', itemId='test', itemPrompt='four', itemTargets=['four'], learnerId='auto', answer='three', label='False'),
    ShortAnswerInstance(taskId='test', itemId='test', itemPrompt='four', itemTargets=['four'], learnerId='auto', answer='Four', label='True'),
    ShortAnswerInstance(taskId='test', itemId='test', itemPrompt='four', itemTargets=['four'], learnerId='auto', answer='for', label='True')
    ]
    """

    responses = filter_responses(input_data)

    if len(responses) < 2:
        raise Exception('Number of samples to small')

    mapped = list(map(convert, responses))
    print_in_worker(mapped)

    ldr = LanguageDataRequest(
        instances = mapped,
        modelId = 'test' # instructions.modelId,
    )

    metrics = core.train_from_answers(ldr)
    return json.dumps(metrics)
