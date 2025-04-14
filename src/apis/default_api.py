from typing import List
from fastapi import APIRouter, Body, Path
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

import controller.tasks
from controller import info, tasks, coders
from models.coder import Coder
from models.response import Response
from models.service_info import ServiceInfo
from models.task import Task
from models.task_action import TaskAction
from models.task_seed import TaskSeed
from models.data_chunk import DataChunk
from models.task_update import TaskUpdate

router = APIRouter()

@router.delete(
    "/coders/{coder_id}",
    responses={
        200: {"description": "OK"},
    },
    tags=["default"],
    summary="delete coder",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def coders_coder_id_delete(
        coder_id: str = Path(..., description=""),
) -> None:
    coders.delete(coder_id)


@router.get(
    "/coders",
    responses={
        200: {"model": List[str], "description": "OK"},
    },
    tags=["default"],
    summary="list as available coders",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def coders_get(
) -> List[Coder]:
    return coders.list()

@router.get(
    "/info",
    responses={
        200: {"model": ServiceInfo, "description": "OK"},
    },
    tags=["default"],
    summary="return conding service identification",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def info_get(
) -> ServiceInfo:
    return info.get_info()


@router.get(
    "/tasks",
    responses={
        200: {"model": List[Task], "description": "OK"},
    },
    tags=["default"],
    summary="get list of all tasks",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def tasks_get(
) -> List[Task]:
    return tasks.list_tasks()


@router.put(
    "/tasks",
    responses={
        200: {"model": Task, "description": "OK"},
    },
    tags=["default"],
    summary="add a task",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def tasks_put(
    task_seed: TaskSeed = Body(None, description=""),
) -> Task:
    return tasks.create(task_seed)


@router.delete(
    "/tasks/{task_id}/data/{chunk_id}",
    responses={
        200: {"description": "OK"},
    },
    tags=["default"],
    summary="delete a chunk of data from a specific task",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def tasks_task_id_data_chunk_id_delete(
    task_id: str = Path(..., description=""),
    chunk_id: str = Path(..., description=""),
) -> None:
    return controller.tasks.delete_data(task_id, chunk_id)

@router.post(
    "/tasks/{task_id}/{action}",
    responses={
        200: {"model": Task, "description": "OK"},
    },
    tags=["default"],
    summary="perform action on task",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def tasks_task_id_action_post(
    action: TaskAction = Path(..., description="action name, usually &#x60;abort&#x60; or &#x60;commit&#x60;"),
    task_id: str = Path(..., description=""),
) -> Task:
    return controller.tasks.action(task_id, action)


@router.delete(
    "/tasks/{task_id}/data/{chunk_id}",
    responses={
        200: {"description": "OK"},
    },
    tags=["default"],
    summary="delete a chunk of data from a specific task",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def tasks_task_id_data_chunk_id_delete(
    task_id: str = Path(..., description=""),
    chunk_id: str = Path(..., description=""),
) -> None:
    return controller.tasks.delete_data(task_id, chunk_id)


@router.get(
    "/tasks/{task_id}/data/{chunk_id}",
    responses={
        200: {"model": List[Response], "description": "OK"},
    },
    tags=["default"],
    summary="retrieve a chunk of data from a specific task",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def tasks_task_id_data_chunk_id_get(
    task_id: str = Path(..., description=""),
    chunk_id: str = Path(..., description=""),
) -> list[Response]:
    return controller.tasks.get_data(task_id, chunk_id)


@router.put(
    "/tasks/{task_id}/data",
    responses={
        200: {"model": DataChunk, "description": "OK"},
    },
    tags=["default"],
    summary="add a chunk of data for a specific task",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def tasks_task_id_data_put(
    task_id: str = Path(..., description=""),
    responses = Body(List[Response], description=""),
) -> DataChunk:
    # the automatic validation of List[Response] does not work, so we do it ourselves
    validated_responses: List[Response] = []
    for row in responses:
        try:
            response = Response.model_validate(row)
        except ValidationError as e:
            print(e.errors())
            raise RequestValidationError(errors = e.errors())
        validated_responses.append(response)
    print(validated_responses[0])
    print(type(validated_responses[0]))
    return tasks.add_data(task_id, validated_responses)


@router.delete(
    "/tasks/{task_id}",
    responses={
        200: {"description": "OK"},
    },
    tags=["default"],
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def tasks_task_id_delete(
    task_id: str = Path(..., description=""),
) -> None:
    return tasks.delete(task_id)


@router.get(
    "/tasks/{task_id}",
    responses={
        200: {"model": Task, "description": "OK"},
    },
    tags=["default"],
    summary="get specific task",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def tasks_task_id_get(
    task_id: str = Path(..., description=""),
) -> Task:
    return tasks.get(task_id)


@router.patch(
    "/tasks/{task_id}",
    responses={
        200: {"model": Task, "description": "OK"},
    },
    tags=["default"],
    summary="update instructions or other fields",
    response_model_by_alias=True,
    response_model_exclude_none = True,
)
async def tasks_task_id_patch(
    task_id: str = Path(..., description=""),
    task_update: TaskUpdate = Body(None, description=""),
) -> Task:
    return tasks.update(task_id, task_update)
