from time import sleep
from typing import List

from pydantic import StrictStr, StrictInt

from features.data import ShortAnswerInstance
from isaac_sas import core
from isaac_sas.instructions_train import InstructionsTrain
from isaac_sas.models import LanguageDataRequest
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



def train(instructions: InstructionsTrain, training_input: List[Response]) -> List[Response]:

    def convert(response: Response) -> ShortAnswerInstance:
        return ShortAnswerInstance(
            taskId = 'test',
            itemId = 'test',
            itemPrompt = instructions.item_promt,
            itemTargets = instructions.item_targets,
            learnerId = response.set_id,
            answer = response.value if isinstance(response.value, str) else '',
            label = response.code
        )

    def filter_response(response: Response)-> bool:
        return isinstance(response.value, str)

    filtered = list(filter(filter_response, training_input))
    mapped = map(convert, filtered)
    ldr = LanguageDataRequest(
        instances = list(mapped),
        modelId = 'test'
    )
    metrics = core.trainFromAnswers(ldr)
    print(metrics)
    return []
