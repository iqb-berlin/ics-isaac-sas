import json
import os

import pytest
import isaac_sas

from fastapi.testclient import TestClient
from main import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def mock_instances():
    instance1 = {
        "taskId": "0",
        "itemId": "0",
        "itemPrompt": "mock_prompt",
        "itemTargets": ["one", "two", "three"],
        "learnerId": "0",
        "answer": "two",
        "label": "True"
    }
    instance2 = {
        "taskId": "1",
        "itemId": "1",
        "itemPrompt": "mock_prompt2",
        "itemTargets": ["four", "five", "six"],
        "learnerId": "1",
        "answer": "two",
        "label": "True"
    }
    instance3 = {
        "taskId": "2",
        "itemId": "2",
        "itemPrompt": "mock_prompt3",
        "itemTargets": ["four", "five", "six"],
        "learnerId": "2",
        "answer": "five",
        "label": "False"
    }
    instance4 = {
        "taskId": "2",
        "itemId": "2",
        "itemPrompt": "mock_prompt3",
        "itemTargets": ["four", "five", "six"],
        "learnerId": "2",
        "answer": "five",
        "label": "False"
    }
    instances = [instance1, instance2, instance3, instance4]

    for _ in range(10):
        instances.append(instance1)
        instances.append(instance2)
        instances.append(instance3)
        instances.append(instance4)

    # The dicionaries are used to set up ShortAnswerInstance objects.
    return instances


@pytest.fixture()
def predict_instances():
    instance1 = {
        "taskId": "0",
        "itemId": "0",
        "itemPrompt": "mock_prompt",
        "itemTargets": ["one", "two", "three"],
        "learnerId": "0",
        "answer": "two",
    }
    instance2 = {
        "taskId": "1",
        "itemId": "1",
        "itemPrompt": "mock_prompt2",
        "itemTargets": ["two", "three", "four"],
        "learnerId": "1",
        "answer": "two",
    }
    instance3 = {
        "taskId": "2",
        "itemId": "2",
        "itemPrompt": "mock_prompt3",
        "itemTargets": ["four", "five", "six"],
        "learnerId": "2",
        "answer": "five",
    }

    return [instance1, instance2, instance3]


def test_train_from_answers(client, mock_instances):
    """
    Test the /trainFromAnswers endpoint.

    :param client: A client for testing.
    :param mock_instances: Mock short answer instances
    """

    instance_dict = {
        "instances": mock_instances,
        "modelId": "random_data",
    }
    response = client.post("/trainFromAnswers", json=instance_dict)

    # Store states to check whether the file and session object were created.
    path_exists = os.path.exists(core.get_data_path('onnx_models', "random_data.onnx"))
    bow_path_exists = os.path.exists(core.get_data_path('bow_models', "random_data.json"))
    metrics_path_exists = os.path.exists(core.get_data_path("model_metrics", "random_data.json"))
    session_stored = "random_data" in core.inf_sessions

    # Delete all files that have been created during training.
    if session_stored:
        del core.inf_sessions["random_data"]
    if path_exists:
        os.remove(core.get_data_path('onnx_models', "random_data.onnx"))
    if bow_path_exists:
        os.remove(core.get_data_path('bow_models', "random_data.json"))
    if metrics_path_exists:
        os.remove(core.get_data_path("model_metrics", "random_data.json"))

    # The assertions are made after the clean-up process on the basis of the
    # stored states. This ensures that cleaning is done in any case.

    if response.status_code >= 400:
        print('Error returned:')
        print(response.text)

    assert response.status_code == 200
    assert path_exists
    assert bow_path_exists
    assert metrics_path_exists
    assert session_stored


def test_predict_from_answers(client, predict_instances):
    """
    Test the /predictFromAnswers endpoint.

    :param client: A client for testing.
    :param mock_instances: Mock short answer instances that do not have labels
    """
    pred_instance_dict = {
        "instances": predict_instances,
        "modelId": "test_pred_data",
    }

    pred_response = client.post("/predictFromAnswers", json=pred_instance_dict)

    if pred_response.status_code >= 400:
        print('Error returned:')
        print(pred_response.text)

    assert pred_response.status_code == 200

    response_dict = json.loads(pred_response.content.decode("utf-8"))
    assert response_dict["predictions"][0]["prediction"] == '1'
    assert response_dict["predictions"][1]["prediction"] == '1'
    assert response_dict["predictions"][2]["prediction"] == '2'


def test_fetch_stored_models(client):
    response = client.get("/fetchStoredModels")
    assert response.status_code == 200

    response_dict = json.loads(response.content.decode("utf-8"))["modelIds"]

    assert list(core.inf_sessions.keys()) == response_dict
