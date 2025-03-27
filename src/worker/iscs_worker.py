from time import sleep
from typing import List

from pydantic import StrictStr, StrictInt

from features.data import ShortAnswerInstance
from isaac_sas import core
from isaac_sas.models import LanguageDataRequest
from models.response import Response
from models.train import Train



def example(input: List[Response]) -> List[Response]:
    sleep(3)
    output: List[Response] = []
    row = Response(
        setId = StrictStr("output_set"),
        id = StrictStr("output"),
        status = StrictStr("CODING_COMPLETE"),
        value = "output",
        code = StrictInt(10),
        score = StrictInt(10)
    )
    output.append(row)
    return output



def train(instructions: Train, training_input: List[Response]) -> List[Response]:

    def convert(response: Response) -> ShortAnswerInstance:
        return ShortAnswerInstance(
            taskId = 'test',
            itemId = 'test',
            itemPrompt = instructions.item_prompt,
            itemTargets = instructions.item_targets,
            learnerId = response.set_id,
            answer = response.value if isinstance(response.value, str) else '',
            label = 'True' if response.code == 1 else 'False'  # TODO make get labels from instructions
        )

    def filter_response(response: Response)-> bool:
        return isinstance(response.value, str)

    # TODO filter specific var
    # TODO filter status

    filtered = list(filter(filter_response, training_input))

    if len(filtered) < 2:
        raise Exception('Number of samples to small')

    mapped = list(map(convert, filtered))

    unique_labels = { obj.label for obj in mapped }
    if len(unique_labels) < 2:
        raise Exception('Insufficient training data: two different codes must be given')

    ldr = LanguageDataRequest(
        instances = mapped,
        modelId = 'test' # TODO
    )
    metrics = core.trainFromAnswers(ldr)
    print(metrics)
    return []
