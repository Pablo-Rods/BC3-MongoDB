from src.services.upload_service import UploadService
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

import tempfile
import os

router = APIRouter()
service = UploadService()


@router.post(
    "/{filename}",
    summary="Sube un .bc3",
    description="Sube un .bc3 asociado al proyecto con el nombre dado"
)
async def importar_bc3(
    filename: str,
    file: UploadFile = File(...),
    exportar_arbol_json: bool = Form(False),
    validar_arbol: bool = Form(True),
    sobrescribir: bool = Form(True),
):
    """Importar archivo BC3 y guardar estructura de árbol"""

    if not file.filename.lower().endswith('.bc3'):
        raise HTTPException(status_code=400, detail="Archivo debe ser .bc3")

    temp_filepath = None
    try:
        # Crear archivo temporal
        content = await file.read()
        with (
            tempfile.NamedTemporaryFile(delete=False, suffix='.bc3')
            as temp_file
        ):
            temp_file.write(content)
            temp_filepath = temp_file.name

        # Procesar archivo
        resultado = service.importar_solo_arbol(
            filepath=temp_filepath,
            archivo_name=filename,
            exportar_arbol_json=exportar_arbol_json,
            validar_arbol=validar_arbol,
            sobrescribir=sobrescribir
        )

        if resultado:
            return {
                "message": "Archivo procesado exitosamente",
                "archivo": file.filename,
                "size": len(content)
            }
        else:
            raise HTTPException(status_code=400, detail=resultado["error"])

    finally:
        # Limpiar archivo temporal
        if temp_filepath and os.path.exists(temp_filepath):
            os.unlink(temp_filepath)
