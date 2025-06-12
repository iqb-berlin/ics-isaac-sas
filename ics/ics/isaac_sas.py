import json
import os
import shutil

from builtins import str, list, max, Exception, print, zip, open

import time
from typing import Literal, Final, Callable

import numpy as np
import onnxruntime as rt
import pandas as pd

from fastapi import HTTPException
from pandas.core.frame import DataFrame
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import cohen_kappa_score
from sklearn.model_selection import StratifiedKFold

from lib.feature_extraction.feature_groups import BOWGroupExtractor, SIMGroupExtractor
from ics.models import LanguageDataRequest, PredictFromLanguageDataResponse, SinglePrediction


# TODO remove this cache and become stateless
inf_sessions = {} # Inference session object for predictions. # TODO get rid of this (or move to redis)
features = {} # in-memory feature data # TODO get rid of this (or move to redis)
bow_models = {} # TODO get rid of this (or move to redis)

# TODO handle this better
defaultLabels : Final = [
    "False",
    "True"
]

def get_data_path(datadir: Literal['onnx_models', 'bow_models', 'model_metrics', 'instructions'], file_name: str = '') -> str:
    path_from_env = os.environ.get('IS_DATA_DIR')
    if not path_from_env:
        raise Exception("Env IS_DATA_DIR not set")
    if not os.path.exists(path_from_env):
        raise Exception("Datadir " + path_from_env + " does not exist")
    return os.path.join(path_from_env, datadir, file_name)

def load_bow_model(model_id: str) -> BOWGroupExtractor :
    bow_path = get_data_path('bow_models', model_id + ".json")
    if not os.path.exists(bow_path):
        raise Exception(f"Bow model not found: {model_id}")
    with open(bow_path) as bowf:
        state_dict = json.load(bowf)
        # Instances list is passed empty here because bag of words setup has
        # already been done.
        model = BOWGroupExtractor([])
        model.bag = state_dict["bag"]
        return model

def load_onnx_model(model_id: str) -> rt.InferenceSession:
    onnx_path = get_data_path('onnx_models', model_id + ".onnx")
    if not os.path.exists(onnx_path):
        raise Exception(f"ONNX model not found: {model_id}")
    return rt.InferenceSession(
        get_data_path('onnx_models', onnx_path)
    )

def fetch_stored_models() -> list[str]:
    models = []
    for model_file in os.listdir(get_data_path('onnx_models')):
        if model_file.startswith("."):
            continue
        models.append(model_file.removesuffix('.onnx'))
    return models

def train_from_answers(
    req: LanguageDataRequest,
    random_seed: int | None = 2,
    message_callback: Callable[[str, bool], None] | None = None
):
    model_id = req.modelId
    # All feature extractor objects that should be used, are defined here.
    ft_extractors = [SIMGroupExtractor()]

    data_frame = pd.DataFrame()

    # Note that the BOW feature extractor is set up later because it needs a new
    # setup for every new train-test split.
    for ft_extractor in ft_extractors:
        data_frame = pd.concat([data_frame, ft_extractor.extract(req.instances)], axis=1)

    labels = pd.DataFrame([instance.label for instance in req.instances], columns=["labels"])

    best_metrics = init_best_metrics(model_id)
    best_model = None

    n_splits = (10 if data_frame.shape[0] > 1000 else 5) if data_frame.shape[0] > 50 else 2

    if random_seed:
        message_callback('No real randomizer used', True)

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state = random_seed)
    split_nr = 0
    for train_ids, test_ids in skf.split(data_frame, labels):
        split_nr += 1

        # The right indices must be found to extract the BOW features for the correct instances.
        train_instances = [req.instances[idx] for idx in train_ids]
        bow_extractor = BOWGroupExtractor(train_instances)

        x = pd.concat([data_frame, bow_extractor.extract(req.instances)], axis=1)

        # NOTE: If categorical features are included, One-hot should be included here as well.

        start = time.time()

        clf = RandomForestClassifier()

        x_train = x.iloc[train_ids]
        y_train = labels.iloc[train_ids]
        x_test = x.iloc[test_ids]
        y_test = labels.iloc[test_ids]

        y_train_label_count = len(y_train.groupby('labels').nunique().values.tolist())
        y_test_label_count = len(y_test.groupby('labels').nunique().values.tolist())

        if y_train_label_count != len(defaultLabels) or y_test_label_count != len(defaultLabels):
            continue

        y_train_raveled = np.ravel(y_train)
        clf.fit(x_train, y_train_raveled)
        y_pred = clf.predict(x_test)

        end = time.time()

        # Problem: random selected sample may contain pny true or false!
        metrics = classification_report(
            y_test, y_pred, output_dict=True, target_names=["False", "True"] # TODO allow more categories
        )

        accuracy = accuracy_score(y_test, y_pred)
        f1 = metrics["macro avg"]["f1-score"]
        cohens_kappa = cohen_kappa_score(y_test, y_pred)

        # Add accuracy and cohens kappa to the metrics dictionary.
        metrics["accuracy"] = accuracy
        metrics["cohens_kappa"] = cohens_kappa

        best_list = best_metrics[model_id]

        best_acc = best_list["accuracy"]
        best_f1 = best_list["f1"]
        best_ck = best_list["cohens_kappa"]

        for best, current in zip((best_acc, best_f1, best_ck), (accuracy, f1, cohens_kappa)):
            if current > best["value"]:
                best["value"] = current
                best["metrics"] = metrics
                best["model_type"] = clf.__class__.__name__
                bow_models[model_id] = bow_extractor
                bow_path = get_data_path('bow_models', model_id + ".json")
                with open(bow_path, "w") as bowf:
                    json.dump(bow_extractor.__dict__, bowf)

        best_list["train_time"] = end - start

        # TODO: How to determine which model should be stored
        # (accuracy, f1, cohens kappa)?
        if not best_model or accuracy > best_acc["value"]:
            best_model = clf
            model_columns = list(x.columns)
            num_features = clf.n_features_in_

        if message_callback:
            message_callback(f'{split_nr}/{n_splits}', False)

    if best_model is None:
        raise Exception("Could not create a model (dataset too small?)")

    # Write best results metrics to file
    file_name = get_data_path('model_metrics', model_id + ".json")
    with open(file_name, "w") as score_file:
        json.dump(best_metrics, score_file, indent=4)

    # Store all models (no double storing if same model).
    store_as_onnx(best_model, model_id, model_columns, num_features)

    return best_metrics

def init_best_metrics(model_id):
    # Initialize the best training acc, f1, cohens kappa and their models.
    metrics_out = {
        model_id: {
            "accuracy": {
                "value": 0.0,
                "metrics": None,
                "model_type": None,
            },
            "f1": {
                "value": 0.0,
                "metrics": None,
                "model_type": None,
            },
            "cohens_kappa": {
                "value": 0.0,
                "metrics": None,
                "model_type": None,
            },
        }
    }

    return metrics_out


def store_as_onnx(model, model_id, model_columns, num_features):
    initial_type = [("float_input", FloatTensorType([None, num_features]))]
    clf_onnx = convert_sklearn(model, initial_types=initial_type)

    # Manually pass the model columns to the converted model using the
    # metadata_props attribute.
    new_meta = clf_onnx.metadata_props.add()
    new_meta.key = "model_columns"
    # The metadata lists must be converted to a string because the
    # metadata_props attribute only allows sending strings.
    new_meta.value = " ".join(model_columns)

    with open(get_data_path('onnx_models', model_id + '.onnx'), "wb") as onnx_file:
        onnx_file.write(clf_onnx.SerializeToString())

    # Store an inference session for this model to be used during prediction.
    inf_sessions[model_id] = rt.InferenceSession(get_data_path('onnx_models', model_id + '.onnx'))

def load_model(model_id: str) -> None:
    if model_id not in [remove_suffix(model, ".onnx") for model in os.listdir(get_data_path('onnx_models'))]:
        raise HTTPException(
            status_code=422,
            detail='Model with model ID "{}" could not be'
                   " found in the ONNX model directory."
                   " Please train first.".format(model_id),
        )
    if model_id not in [remove_suffix(model, ".json") for model in os.listdir(get_data_path('bow_models'))]:
        raise HTTPException(
            status_code=422,
            detail='BOW Model with model ID "{}" could not be'
                   " found in the Bag of words model directory."
                   " Please check that the model was trained with training"
                   " instances (not with CAS).".format(model_id),
        )

def predict_from_answers(
    req: LanguageDataRequest,
    message_callback: Callable[[str, bool], None] | None
) -> PredictFromLanguageDataResponse:
    model_id = req.modelId

    bow_extractor = load_bow_model(model_id)
    onnx_inf_session = load_onnx_model(model_id)
    ft_extractors = [SIMGroupExtractor(), bow_extractor]

    report_steps = 20 - 2 * len(str(abs(len(req.instances))))

    predictions = []
    for instance in req.instances:
        data = pd.DataFrame()
        for ft_extractor in ft_extractors:
            data = pd.concat([data, ft_extractor.extract([instance])], axis=1)
        predictions.append(do_prediction(data, onnx_inf_session))

        if message_callback and (len(predictions) % report_steps == 0):
            message_callback(f'{len(predictions)}/{len(req.instances)}', False)

    return PredictFromLanguageDataResponse(predictions = predictions)

def do_prediction(data: DataFrame, session: rt.InferenceSession) -> SinglePrediction:
    query = pd.get_dummies(data)
    # The columns in string format are retrieved from the model and converted
    # back to a list.
    model_columns = (
        session.get_modelmeta().custom_metadata_map["model_columns"].split(" ")
    )

    # https://github.com/amirziai/sklearnflask/issues/3
    # Thanks to @lorenzori
    query = query.reindex(columns=model_columns, fill_value=0)
    input_name = session.get_inputs()[0].name
    # The predict_proba function is used because get_outputs() is indexed at 1.
    # If it is indexed at 0, the predict method is used.
    label_name = session.get_outputs()[1].name
    # Prediction takes place here.
    pred = session.run([label_name], {input_name: query.to_numpy(dtype=np.float32)})[0]

    # The Prediction dictionary is stored in a list by ONNX so it can be
    # retrieved by indexing.
    probs = pred[0]

    # prediction is the class with max probability
    return SinglePrediction(
        prediction = max(probs, key=lambda k: probs[k]),
        classProbabilities = probs
    )

def wipe_models():
    try:
        shutil.rmtree(get_data_path('onnx_models'))
        os.makedirs(get_data_path('onnx_models'))
        return "ONNX Models wiped"

    except Exception as e:
        print(str(e))
        raise HTTPException(
            status_code=400,
            detail="Could not remove and recreate the onnx_models directory",
        )

def delete_file(type: Literal['onnx_models', 'bow_models', 'model_metrics', 'instructions'], file_name: str = '') -> None:
    file_path = get_data_path(type, file_name)
    os.remove(file_path)

def delete_model(model_id: str) -> None:
    delete_file('onnx_models', f"{model_id}.onnx")

def file_exists(type: Literal['onnx_models', 'bow_models', 'model_metrics', 'instructions'], file_name: str) -> bool:
    return os.path.exists(get_data_path(type, file_name))

def model_exists(model_id: str) -> bool:
    return file_exists('onnx_models', f"{model_id}.onnx")

def remove_suffix(line: str, suffix: str) -> str:
    if line.endswith(suffix):
        return line[:-len(suffix):]
    else:
        return line


# prepare cache TODO the remove cache and become stateless

# Store all model objects and inference session objects in memory for
# quick access.
for model_file in os.listdir(get_data_path('onnx_models')):
    if model_file.startswith("."):
        continue
    model_id = remove_suffix(model_file, ".onnx")
    if model_id not in inf_sessions:
        inf_sessions[model_id] = load_onnx_model(model_id)

# For prediction from ShortAnswerInstances the BOW model belonging to the ML model
# must be loaded for feature extraction.
for bow_file in os.listdir(get_data_path('bow_models')):
    # Ignore hidden files like .keep
    if bow_file.startswith("."):
        continue
    model_id = remove_suffix(bow_file, ".json")
    if model_id not in bow_models:
        bow_models[model_id] = load_bow_model(model_id)
