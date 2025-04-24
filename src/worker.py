import json, re
import src.isaac_sas as isaac_sas
from typing import List
from pydantic import StrictInt, BaseModel
from lib.feature_extraction.data import ShortAnswerInstance
from src.models import LanguageDataRequest
from lib.ics_components.src.models.response import Response
from lib.ics_components.src.models.task_instructions import TaskInstructions

class ResponseRow(BaseModel):
    response: Response
    rowToCodeId: int | None

def is_suitable_for_code(response: Response) -> bool:
    # TODO filter specific var
    # TODO filter status
    return isinstance(response.value, str)

def is_suitable_for_train(response: Response) -> bool:
    # TODO filter specific var
    # TODO filter status
    return (isinstance(response.value, str)
        and response.code is not None
    )

def mark_unsuitable_rows(responses: List[Response]) -> List[ResponseRow]:
    rows : List[ResponseRow] = []
    rows_to_code_counter = 0
    for (i, response) in enumerate(responses):
        rows.append(
            ResponseRow(
                response = response,
                rowToCodeId = rows_to_code_counter if is_suitable_for_code(response) else None
            )
        )
        if is_suitable_for_code(response):
            rows_to_code_counter += 1
    return rows

def filter_marked_rows(response_rows: List[ResponseRow]) -> List[ResponseRow]:
    return list(filter(lambda response_row: response_row.rowToCodeId is not None, response_rows))

def label_to_code(label: str) -> StrictInt:
    if label not in isaac_sas.defaultLabels:
        raise ValueError(f"Label {label} is not supported.")
    return isaac_sas.defaultLabels.index(label)

def code_to_label(code: int) -> str:
    if code > len(isaac_sas.defaultLabels) or code < 0:
        raise ValueError(f"Code {code} is not supported.")
    return isaac_sas.defaultLabels[code]

def code(model_id: str, input_data: List[Response]) -> List[Response]:
    instructions = restore_instructions(model_id)
    def convert_to_sai(row: ResponseRow) -> ShortAnswerInstance:
        return ShortAnswerInstance(
            taskId = 'test',
            itemId = 'test',
            itemPrompt = instructions.item_prompt,
            itemTargets = instructions.item_targets,
            learnerId = row.response.set_id,
            answer = row.response.value if isinstance(row.response.value, str) else '',
            label = None
        )

    response_rows = mark_unsuitable_rows(input_data)

    ldr = LanguageDataRequest(
        instances = list(map(convert_to_sai, filter_marked_rows(response_rows))),
        modelId = model_id
    )

    result = isaac_sas.predict_from_answers(ldr)

    output: List[Response] = []
    for row in response_rows:
        response = row.response
        if row.rowToCodeId is not None:
            class_probabilities = result.predictions[row.rowToCodeId].classProbabilities
            response.status = "CODING_SEMI_COMPLETE"
            response.coding_probabilities = { label_to_code(k): v for k, v in class_probabilities.items() }
            response.code = None
            response.score = None
        output.append(response)

    print(output)
    return output

def train(task_label: str, instructions: TaskInstructions, input_data: List[Response]) -> str:
    def convert(response: Response) -> ShortAnswerInstance:
        return ShortAnswerInstance(
            taskId = 'test', # TODO
            itemId = 'test', # TODO
            itemPrompt = instructions.item_prompt,
            itemTargets = instructions.item_targets,
            learnerId = response.set_id,
            answer = response.value if isinstance(response.value, str) else '',
            label = code_to_label(response.code)  # TODO make get labels from instructions
        )

    responses = list(filter(is_suitable_for_train, input_data))

    if len(responses) < 2:
        raise Exception(f'Number of suitable samples to small: {len(responses)}.')

    unique_codes = { obj.code for obj in responses }
    if len(unique_codes) != len(isaac_sas.defaultLabels):
        raise Exception(f'Insufficient training data: {len(unique_codes)} are found, but it has to be exactly {len(isaac_sas.defaultLabels)}.')

    mapped = list(map(convert, responses))

    model_id = re.sub(r'[^A-Za-z0-9]', '-', task_label)
    while isaac_sas.model_exists(model_id):
        model_id = model_id + '_'

    ldr = LanguageDataRequest(
        instances = mapped,
        modelId = model_id
    )

    metrics = isaac_sas.train_from_answers(ldr, random_seed = instructions.random_seed)

    store_instructions(model_id, instructions)

    return f"Model trained: {model_id}.\n Metrics:\n" + json.dumps(metrics, indent = 2)

def coder_exists(coder_id: str) -> bool:
    return isaac_sas.model_exists(coder_id) or isaac_sas.file_exists('instructions', coder_id + '.json')

def delete_coder(coder_id: str) -> None:
    isaac_sas.delete_file('instructions', coder_id + '.json')
    return isaac_sas.delete_model(coder_id)

# issac-sas actually uses the instructions not only in the training, but also in the coding process
# so it must be part of the coder, as well es the mode, itself
# we store it as file, because the instance of them stored in redis is bound to a task, not a coder
# this might change later
def store_instructions(coder_id: str, instructions: TaskInstructions):
    path = isaac_sas.get_data_path('instructions', coder_id + '.json')
    with open(path, "w") as outfile:
        outfile.write(instructions.model_dump_json(by_alias = True))
        outfile.close()

def restore_instructions(coder_id: str) -> TaskInstructions:
    path = isaac_sas.get_data_path('instructions', coder_id + '.json')
    with open(path, "r") as infile:
        return TaskInstructions.model_validate_json(infile.read())
