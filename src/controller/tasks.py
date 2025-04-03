import json
import os
import time
import uuid

from fastapi import HTTPException
from pydantic import StrictStr, StrictInt
from rq import Queue, Worker
from redis import Redis, StrictRedis
from rq.job import Job, JobStatus, Callback
from typing_extensions import List

from models.chunk_type import ChunkType
from models.data_chunk import DataChunk
from models.response import Response
from models.task import Task
from models.task_event_type import TaskEventType
from models.task_instructions import TaskInstructions
from models.task_seed import TaskSeed
from models.task_event import TaskEvent
from models.task_action import TaskAction
from models.task_type import TaskType

from models.task_update import TaskUpdate
from worker import ics_worker as worker
from worker.common import print_in_worker

redis_host = os.getenv('REDIS_HOST') or 'localhost'
redis_queue = Redis(host=redis_host, port=6379, db=0)
redis_store = StrictRedis(host=redis_host, port=6379, db=0, decode_responses=True)
queue = Queue(connection=redis_queue)
print("Redis Connected")

def list_tasks() -> List[Task]:
    task_keys = redis_store.keys('task:*')
    task_list = []
    for task_key in task_keys:
        task_list.append(get(task_key.removeprefix('task:')))
    return list(task_list)


def get(task_id: str) -> Task:
    task_str = redis_store.get('task:' + task_id)
    if not task_str:
        raise HTTPException(status_code=404, detail="Task not found!")
    try:
        task = Task.model_validate_json(task_str, by_name = True)
        return task
    except Exception as e:
        return Task(
            id = task_id,
            label = '<ERROR>',
            type = TaskType('unknown'),
            events = [
                TaskEvent(
                    status = TaskEventType('fail'),
                    message = str(e),
                    timestamp = 0
                )
            ],
            data = []
        )

def run_task(task: Task) -> None:
    current_worker = Worker.all(connection=redis_queue)[0]
    print_in_worker(f"run_task in {current_worker.name}")
    task.events.append(TaskEvent(
        status = TaskEventType('start'),
        timestamp = int(time.time()),
        message = f"run_task in {current_worker.name}"
    ))
    store(task)

    input_chunks = [chunk for chunk in task.data if chunk.type == "input"]
    input_data = [var for input_chunk in input_chunks for var in get_data(task.id, input_chunk.id)]

    if task.type == 'train':
        if not isinstance(task.instructions, TaskInstructions):
            raise Exception("Instructions has wrong type: " + task.instructions.__class__.__name__)
        message = worker.train(task.instructions, input_data)
    else:
        print_in_worker(task.instructions)
        if  not type(task.instructions) is str:
            raise Exception("Instructions has wrong type: " + type(task.instructions))
        output = worker.code(task.instructions, input_data)
        chunk = store_data(ChunkType('output'), output)
        task.data.append(chunk)
        message = ''

    task.events.append(TaskEvent(
        status = TaskEventType('finish'),
        timestamp = int(time.time()),
        message = message
    ))
    store(task)

def job_failed(job: Job, redis: Redis, errorClass, error: Exception, trace):
    print_in_worker('job_failed')
    task = get(job.id)
    task.events.append(TaskEvent(
        status = TaskEventType('fail'),
        timestamp = int(time.time()),
        message = str(error)
    ))
    store(task)

def action(task_id: str, action: TaskAction) -> Task:
    task = get(task_id)
    if action == "commit":
        if get_status(task) != 'start':
            raise HTTPException(status_code = 400, detail = 'Task already running!')
        task.events.append(TaskEvent(
            status = StrictStr('commit'),
            timestamp = StrictInt(time.time())
        ))
        store(task)
        job = Job.create(
            func = run_task,
            id = task_id,
            connection = redis_queue,
            kwargs = { "task": task },
            on_failure = Callback(job_failed),
            timeout = 5
        )
        queue.enqueue_job(job)

    if action == "abort":
        status = get_status(task)
        if status != 'commit' and status != 'start':
            raise HTTPException(status_code = 400, detail = 'Task not commited')
        job = get_job(task_id)
        if job.get_status() != JobStatus.QUEUED:
            job.cancel()
            job.delete()
        task.events.append(TaskEvent(
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

def create(create_task: TaskSeed) -> Task:
    task = Task(
        id = StrictStr(uuid.uuid4()),
        label = create_task.label,
        type = create_task.type,
        events = [
            TaskEvent(
                status = StrictStr('create'),
                timestamp = StrictInt(time.time())
            )
        ],
        data = list()
    )
    store(task)
    return task

def get_status(task: Task) -> StrictStr:
    task.events.sort(key=lambda event: event.timestamp, reverse=True)
    return task.events[0].status

def store(task: Task) -> None:
    redis_store.set('task:' + task.id, task.model_dump_json())

def add_data(task_id: str, data: List[Response]) -> DataChunk:
    chunk = store_data(ChunkType('input'), data)
    task = get(task_id)
    task.data.append(chunk)
    store(task)
    return chunk

def store_data(chunk_type: ChunkType, data: List[Response]) -> DataChunk:
    chunk = DataChunk(
        type = chunk_type,
        id = StrictStr(uuid.uuid4()),
    )
    data_as_json = json.dumps(data)
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

def get_data(task_id: str, chunk_id: str) -> list[Response]:
    task = get(task_id)
    chunk_info = None
    for chunk in task.data:
        if chunk.id == chunk_id:
            chunk_info = chunk
            break
    if chunk_info is DataChunk:
        raise HTTPException(status_code=404, detail="Chunk " + chunk_id + "not found in task " + task_id + "!")
    chunk_content_str = redis_store.get('data:' + chunk_info.type + ':' + chunk_info.id)
    if not chunk_content_str:
        raise HTTPException(status_code=404, detail="Chunk Content not found!")
    chunk_content_json = json.loads(chunk_content_str)
    chunk_content = list(map(lambda row: Response.model_validate(row), chunk_content_json))
    return chunk_content

def delete(task_id: str) -> None:
    task = get(task_id)
    keys_to_delete = ['task:' + task_id]
    for chunk in task.data:
        keys_to_delete.append('data:' + chunk.type + ':' + chunk.id)
    redis_store.delete(*keys_to_delete)

def update_instructions(task_id: str, instructions: TaskInstructions | str | None) -> Task:
    # TODO verify if it's the correct type of instructions
    task = get(task_id)
    task.instructions = instructions
    store(task)
    return task

def update(task_id: str, task_update: TaskUpdate) -> Task:
    task = get(task_id)
    if task_update.instructions:
        if type(task_update.instructions) is str:
            if not worker.coder_exists(str(task_update.instructions)):
                raise HTTPException(status_code = 404, detail = f"Model not found: {task_update.instructions}")
        task.instructions = task_update.instructions
    if task_update.label:
        task.label = task_update.label
    if task_update.type:
        task.type = task_update.type
    store(task)
    return task
