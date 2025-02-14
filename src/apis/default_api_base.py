# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from openapi_server.models.response import Response
from openapi_server.models.service_info import ServiceInfo
from openapi_server.models.task import Task
from openapi_server.models.tasks_put_request import TasksPutRequest
from openapi_server.models.tasks_task_id_data_put200_response import TasksTaskIdDataPut200Response
from openapi_server.models.tasks_task_id_patch_request import TasksTaskIdPatchRequest


class BaseDefaultApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseDefaultApi.subclasses = BaseDefaultApi.subclasses + (cls,)
    def info_get(
        self,
    ) -> ServiceInfo:
        ...


    def tasks_get(
        self,
    ) -> List[Task]:
        ...


    def tasks_put(
        self,
        tasks_put_request: TasksPutRequest,
    ) -> Task:
        ...


    def tasks_task_id_data_chunk_id_delete(
        self,
        task_id: str,
        chunk_id: str,
    ) -> None:
        ...


    def tasks_task_id_data_chunk_id_get(
        self,
        task_id: str,
        chunk_id: str,
    ) -> List[Response]:
        ...


    def tasks_task_id_data_put(
        self,
        task_id: str,
        response: List[Response],
    ) -> TasksTaskIdDataPut200Response:
        ...


    def tasks_task_id_delete(
        self,
        task_id: str,
    ) -> None:
        ...


    def tasks_task_id_get(
        self,
        task_id: str,
    ) -> Task:
        ...


    def tasks_task_id_instructions_patch(
        self,
        task_id: str,
    ) -> None:
        ...


    def tasks_task_id_patch(
        self,
        task_id: str,
        tasks_task_id_patch_request: TasksTaskIdPatchRequest,
    ) -> Task:
        ...
