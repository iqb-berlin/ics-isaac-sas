from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import isaac_sas.core

from apis.default_api import router as DefaultApiRouter
from apis.native_api import router as NativeApiRouter
from pathlib import Path

mod_path = Path(__file__).parent
isaac_sas.core.prepare(mod_path)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins = ['*'],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
    expose_headers = ["*"]
)

app.include_router(DefaultApiRouter)
app.include_router(NativeApiRouter)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_text = ''
    for error in exc.errors():
        error_text += error["msg"] + ': ' + error["loc"][-1] + '\n'

    return JSONResponse(
        status_code = 422,
        content = {
            "type": 'invalid-data',
            "message": error_text
        }
    )


