from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from os import getenv


app = FastAPI(
    title="Predictive Services Fire Weather Index Calculator",
    description="API for the PSU FWI Calculator",
    version="0.0.0"
)

origins = getenv('ORIGINS')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get('/')
async def health():
    return {'message': 'Hello world'}
