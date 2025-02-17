import time
import uuid
from time import sleep

from fastapi import HTTPException
from pydantic import StrictStr, StrictInt
from rq import Queue
from redis import Redis
from rq.job import Job, JobStatus, Callback
from typing_extensions import List, Dict

from models.chunk_type import ChunkType
from models.data_chunk import DataChunk
from models.task import Task
from models.tasks_put_request import TasksPutRequest
from models.task_events_inner import TaskEventsInner
from models.task_action import TaskAction

redis_conn = Redis(host='localhost', port=6379, db=0)
queue = Queue(connection=redis_conn)
print("Redis Connected")

tasks: Dict[str, Task] = {}


def list_tasks() -> List[Task]:
    return list(tasks.values())

def long_task(data: List[DataChunk]):
    sleep(3)
    data.append(DataChunk(id = StrictStr("output"), type = ChunkType("output")))
    return data

def job_done(job, connection, result, *args, **kwargs):
    task = tasks.get(job.id)
    task.events.append(TaskEventsInner(
        status='finish',
        message='yehaa'
    ))
    print('yeahh', args)
    print('yeahh', job)
    print('yeahh', kwargs)
    print('yeahh', job.data)

def job_failed(args):
    print('Arrrgh', args)

def action(taskId: str, action: TaskAction) -> Task:
    task = get(taskId)
    if action == "commit":
        input_data = [chunk for chunk in task.data if chunk.type == "input"]
        job = Job.create(
            func = long_task,
            id = taskId,
            connection = redis_conn,
            kwargs = { "data": input_data },
            on_success = Callback(job_done),
            # on_failure = Callback(job_failed),
            timeout = 5
        )
        queue.enqueue_job(job)
        task.events.append(TaskEventsInner(
            status = StrictStr('commit'),
            timestamp = StrictInt(time.time())
        ))
    if action == "abort":
        job = get_job(taskId)
        if job.get_status() != JobStatus.QUEUED:
            job.cancel()
            job.delete()
            task.events.append(TaskEventsInner(
                status = StrictStr('abort'),
                timestamp = StrictInt(time.time())
            ))
    return task

def get_job(task_id: str) -> Job:
    job = Job.fetch(task_id, connection=redis_conn)
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
    tasks[task.id] = task
    return get(task.id)

def get_status(task: Task) -> StrictStr:
    task.events.sort(key=lambda event: event.timestamp, reverse=True)
    return task.events[0].status

def get(task_id: str) -> Task:
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    status = get_status(tasks[task_id])
    if status == "commit": # aber momentan macht keiner start
        job = get_job(task_id)
        tasks[task_id].events.append(TaskEventsInner(
            status = StrictStr("start"), # TODO ping ot so
            message = job.get_status(),
            timestamp = StrictInt(time.time())
        ))
    return tasks.get(task_id)


