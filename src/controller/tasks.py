import json
import os
import time
import uuid

from fastapi import HTTPException
from pydantic import StrictStr, StrictInt
from rq import Queue
from redis import Redis, StrictRedis
from rq.job import Job, JobStatus, Callback
from typing_extensions import List

from models.chunk_type import ChunkType
from models.data_chunk import DataChunk
from models.response import Response
from models.task import Task
from models.tasks_put_request import TasksPutRequest
from models.task_events_inner import TaskEventsInner
from models.task_action import TaskAction
from models.tasks_task_id_data_put200_response import TasksTaskIdDataPut200Response
from tasks import tasks

redis_host = os.getenv('REDIS_HOST') or 'localhost'
redis_queue = Redis(host=redis_host, port=6379, db=0)
redis_store = StrictRedis(host=redis_host, port=6379, db=0, decode_responses=True)
queue = Queue(connection=redis_queue)
print("Redis Connected")

def list_tasks() -> List[Task]:
    tasks = [get for value in redis_store.keys('task:*')]
    print(tasks)
    return list()

def run_task(task: Task) -> None:
    task.events.append(TaskEventsInner(
        status='start',
        timestamp = int(time.time())
    ))
    store(task)

    input_data = [chunk for chunk in task.data if chunk.type == "input"]

    output = tasks.example(input_data)

    chunk = store_data(ChunkType('output'), output)
    task.data.append(chunk)
    task.events.append(TaskEventsInner(
        status='finish',
        timestamp = int(time.time())
    ))
    store(task)

def job_failed(args):
    print('Arrrgh', args)

def action(task_id: str, action: TaskAction) -> Task:
    task = get(task_id)
    if action == "commit":
        if get_status(task) != 'create':
            raise HTTPException(status_code = 400, detail = 'Task already commited')
        job = Job.create(
            func = run_task,
            id = task_id,
            connection = redis_queue,
            kwargs = { "task": task },
            on_failure = Callback(job_failed),
            timeout = 5
        )
        queue.enqueue_job(job)
        task.events.append(TaskEventsInner(
            status = StrictStr('commit'),
            timestamp = StrictInt(time.time())
        ))
        store(task)
    if action == "abort":
        if get_status(task) != 'commit':
            raise HTTPException(status_code = 400, detail = 'Task not commited')
        job = get_job(task_id)
        if job.get_status() != JobStatus.QUEUED:
            job.cancel()
            job.delete()
        task.events.append(TaskEventsInner(
            status = StrictStr('abort'),
            timestamp = StrictInt(time.time())
        ))
        store(task)
    return task

def get_job(task_id: str) -> Job:
    job = Job.fetch(task_id, connection=redis_queue)
    if not job:
        raise HTTPException(status_code=500, detail="Task is there but Job not found!")
    return job

def create(create_task: TasksPutRequest) -> Task:
    task = Task(
        id = StrictStr(uuid.uuid4()),
        type = create_task.type,
        events = [
            TaskEventsInner(
                status = StrictStr('create'),
                timestamp = StrictInt(time.time())
            )
        ],
        data = list(),
        instructions = create_task.instructions
    )
    store(task)
    return task

def get_status(task: Task) -> StrictStr:
    task.events.sort(key=lambda event: event.timestamp, reverse=True)
    return task.events[0].status

def get(task_id: str) -> Task:
    task_str = redis_store.get('task:' + task_id)
    if not task_str:
        raise HTTPException(status_code=404, detail="Task not found!")
    task = Task.from_json(task_str)
    store(task)
    return task

def store(task: Task) -> None:
    redis_store.set('task:' + task.id, task.to_json())

def add_data(task_id: str, data: List[Response]) -> TasksTaskIdDataPut200Response:
    chunk = store_data(ChunkType('input'), data)
    task = get(task_id)
    task.data.append(chunk)
    store(task)
    return TasksTaskIdDataPut200Response(id = chunk)

def store_data(type: ChunkType, data: List[Response]) -> DataChunk:
    chunk = DataChunk(
        type = type,
        id = StrictStr(uuid.uuid4()),
    )
    data_as_json = json.dumps([row.to_dict() for row in data])
    redis_store.set('data:' + chunk.type + ':' + chunk.id, data_as_json)
    return chunk

def delete_data(task_id: str, chunk_id: str) -> None:
    task = get(task_id)
    chunk_info = None
    for chunk in task.data:
        if chunk.id == chunk_id:
            task.data.remove(chunk)
            chunk_info = chunk
            break
    if chunk_info is DataChunk:
        raise HTTPException(status_code=404, detail="Chunk " + chunk_id + "not found in task " + task_id + "!")
    redis_store.delete('data:' + chunk_info.type + ':' + chunk_info.id)
    store(task)

def get_data(task_id, chunk_id) -> str:
    task = get(task_id)
    chunk_info = None
    for chunk in task.data:
        if chunk.id == chunk_id:
            chunk_info = chunk
            break
    if chunk_info is DataChunk:
        raise HTTPException(status_code=404, detail="Chunk " + chunk_id + "not found in task " + task_id + "!")
    chunk_content = redis_store.get('data:' + chunk_info.type + ':' + chunk_info.id)
    if not chunk_content:
        raise HTTPException(status_code=404, detail="Chunk Content not found!")
    return json.loads(chunk_content)

def delete(task_id):
    task = get(task_id)
    keys_to_delete = ['task:' + task_id]
    for chunk in task.data:
        keys_to_delete.append('data:' + chunk.type + ':' + chunk.id)
    redis_store.delete(*keys_to_delete)

def update_instructions(task_id: str, instructions: any) -> None:
    # TODO verify instructions
    task = get(task_id)
    task.instructions = instructions
    store(task)
