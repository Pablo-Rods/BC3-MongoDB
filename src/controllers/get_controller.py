from src.services.get_service import GetService
from fastapi import APIRouter, HTTPException


router = APIRouter()
service = GetService()


@router.get(
    "/project/{project_name}",
    summary="Analiza si existe un proyecto"
)
async def check_project(project_name: str):
    response = service.get_by_project(project_name)

    if not response or response is None:
        raise HTTPException(
            status_code=404,
            detail=f"El proyecto {project_name} no tiene un" +
            "presupuesto asociado"
        )

    else:
        return True


@router.get(
    "/project/presupuesto/{project_name}",
    summary="Obtiene el presupuesto de un proyecto"
)
async def get_project(project_name: str):
    response = service.get_by_project(project_name)

    if not response or response is None:
        raise HTTPException(
            status_code=404,
            detail=f"El proyecto {project_name} no tiene un" +
            "presupuesto asociado"
        )

    else:
        return response
