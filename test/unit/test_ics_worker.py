import os
import unittest
import warnings

from ics import isaac_sas
from ics_components.ics_components.models.response import Response
from ics_components.ics_components.models.task_instructions import TaskInstructions
from ics.worker import train, code



class IssacSaS(unittest.TestCase):
    def test_train_and_predict(self):
        warnings.simplefilter('error')

        instructions_train = TaskInstructions(
            itemPrompt = 'insert a number!',
            itemTargets = ['one', 'two', 'three'],
            randomSeed = 8
        )

        data = [
            Response(
                setId = 'a',
                id = 'var1',
                status = 'VALUE_CHANGED',
                value = 'one',
                code = 1
            ),
            Response(
                setId = 'a',
                id = 'var1',
                status = 'VALUE_CHANGED',
                value = 'two',
                code = 1
            ),
            Response(
                setId = 'a',
                id = 'var1',
                status = 'VALUE_CHANGED',
                value = 'four',
                code = 0
            ),
            Response(
                setId = 'a',
                id = 'var1',
                status = 'VALUE_CHANGED',
                value = 'five',
                code = 0
            )
        ]

        result = train(instructions_train, data)

        path_exists = os.path.exists(isaac_sas.get_data_path('onnx_models', "test.onnx"))
        bow_path_exists = os.path.exists(isaac_sas.get_data_path('bow_models', "test.json"))
        metrics_path_exists = os.path.exists(isaac_sas.get_data_path("model_metrics", "test.json"))

        assert path_exists
        assert bow_path_exists
        assert metrics_path_exists

        data = [
            Response(
                setId = 'a',
                id = 'var1',
                status = 'VALUE_CHANGED',
                value = 'one',
                code = 1
            ),
            Response(
                setId = 'ignore me',
                id = 'var2',
                status = 'VALUE_CHANGED',
                value = 2
            )
        ]
        result = code('test', data)

        assert len(result) == 2
        assert result[0].codingProbabilities[0] > result[0].codingProbabilities[1]


if __name__ == '__main__':
    unittest.main()
