from src.controllers import upload_controller, get_controller

from fastapi import FastAPI


app = FastAPI(title="API Importador BC3", version="1.0.0")

app.include_router(
    upload_controller.router,
    prefix="/upload"
)

app.include_router(
    get_controller.router,
    prefix="/get"
)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)
