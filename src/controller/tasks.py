import json
import os
import sys
import time
import uuid

from fastapi import HTTPException
from pydantic import StrictStr, StrictInt
from rq import Queue
from redis import Redis, StrictRedis
from rq.job import Job, JobStatus, Callback
from typing_extensions import List

from models.chunk_type import ChunkType
from models.code import Code
from models.data_chunk import DataChunk
from models.response import Response
from models.task import Task
from models.task_instructions import TaskInstructions
from models.task_seed import TaskSeed
from models.task_events_inner import TaskEventsInner
from models.task_action import TaskAction
from models.train import Train
from tasks import tasks

redis_host = os.getenv('REDIS_HOST') or 'localhost'
redis_queue = Redis(host=redis_host, port=6379, db=0)
redis_store = StrictRedis(host=redis_host, port=6379, db=0, decode_responses=True)
queue = Queue(connection=redis_queue)
print("Redis Connected")

def print_in_worker(*args):
    print(args)
    sys.stdout.flush()

def list_tasks() -> List[Task]:
    task_keys = redis_store.keys('task:*')
    task_list = []
    for task_key in task_keys:
        task_list.append(Task.from_json(redis_store.get(task_key)))
    return list(task_list)

def run_task(task: Task) -> None:
    print_in_worker('run_task')
    task.events.append(TaskEventsInner(
        status='start',
        timestamp = int(time.time())
    ))
    store(task)

    input_data = [chunk for chunk in task.data if chunk.type == "input"]

    if task.type == 'train':
        print_in_worker('### TRAIN LIKE A MANIAC ###')
        print_in_worker(task.instructions)
        if not isinstance(task.instructions, Train):
            raise "Instructions has wrong type: " + task.instructions.__class__.__name__
        output = tasks.train(task.instructions, input_data)
    else:
        print_in_worker('### CODE LIKE A MANIAC ###')
        print_in_worker(task.instructions)
        if not isinstance(task.instructions, Code):
            raise "Instructions has wrong type: " + task.instructions.__class__.__name__
        output = tasks.example(input_data)

    chunk = store_data(ChunkType('output'), output)
    task.data.append(chunk)
    task.events.append(TaskEventsInner(
        status = 'finish',
        timestamp = int(time.time())
    ))
    store(task)

def job_failed(job: Job, redis: Redis, errorClass, error: Exception, trace):
    print_in_worker('job_failed')
    task = get(job.id)
    task.events.append(TaskEventsInner(
        status = 'fail',
        timestamp = int(time.time()),
        message = str(error)
    ))
    store(task)

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

def create(create_task: TaskSeed) -> Task:
    task = Task(
        id = StrictStr(uuid.uuid4()),
        label = create_task.label,
        type = create_task.type,
        events = [
            TaskEventsInner(
                status = StrictStr('create'),
                timestamp = StrictInt(time.time())
            )
        ],
        data = list(),
        instructions = TaskInstructions()
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

def add_data(task_id: str, data: List[Response]) -> DataChunk:
    chunk = store_data(ChunkType('input'), data)
    task = get(task_id)
    task.data.append(chunk)
    store(task)
    return chunk

def store_data(chunk_type: ChunkType, data: List[Response]) -> DataChunk:
    for item in data:
        print(type(item))
        print(item)
    chunk = DataChunk(
        type = chunk_type,
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

def update_instructions(task_id: str, instructions: TaskInstructions) -> Task:
    # TODO verify if it's the correct type of instructions
    task = get(task_id)
    task.instructions = instructions
    store(task)
    print('INSTRCUTUIONS SACED')
    print(instructions)
    return task
