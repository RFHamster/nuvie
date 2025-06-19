from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import patient, login, user

from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.SERVICE_NAME,
    version='1.0.0',
    docs_url='/docs',
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


app.include_router(
    patient.router, prefix='/api/v1/patients', tags=['Pacientes']
)

app.include_router(login.router, prefix='/api/v1/login', tags=['Login'])


@app.get('/health')
async def health_check():
    return {'status': 'healthy', 'service': settings.SERVICE_NAME}


@app.middleware('http')
async def log_requests(request, call_next):
    import time

    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    print(
        f'📝 {request.method} {request.url} - {response.status_code} - {process_time:.4f}s'
    )

    return response


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'main:app', host='0.0.0.0', port=8000, reload=True, log_level='info'
    )
