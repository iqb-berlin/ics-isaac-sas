import os
import unittest
import warnings

from sympy.testing import pytest


from isaac_sas import core
from models.response import Response
from models.code import Code
from models.train import Train
from worker.iscs_worker import code, train



class IssacSaS(unittest.TestCase):
    def test_train_and_predict(self):
        warnings.simplefilter('error')

        instructions_train = Train(
            itemPrompt = 'insert a number!',
            itemTargets = ['one', 'two', 'three'],
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

        instructions_code = Code(
            model = 'test'
        )

        result = train(instructions_code, data)

        path_exists = os.path.exists(core.get_data_path('onnx_models', "test.onnx"))
        bow_path_exists = os.path.exists(core.get_data_path('bow_models', "test.json"))
        metrics_path_exists = os.path.exists(core.get_data_path("model_metrics", "test.json"))

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
        result = code(instructions, data)

        assert len(result) == 2
        assert result[0].codingProbabilities[0] > result[0].codingProbabilities[1]


if __name__ == '__main__':
    unittest.main()
