from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import isaac_sas.core


from apis.default_api import router as DefaultApiRouter
from apis.native_api import router as NativeApiRouter
from pathlib import Path

mod_path = Path(__file__).parent
isaac_sas.core.prepare(mod_path)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(DefaultApiRouter)
app.include_router(NativeApiRouter)




