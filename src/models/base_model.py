from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class BC3BaseModel(BaseModel):
    """
    Modelo base para todos los registros de un BC3
    Esto es reutilizable
    """

    id: Optional[str] = Field(
        None,
        description="ID único del documento"
    )

    archivo_origen: Optional[str] = Field(
        None,
        description="Nombre del archivo BC3"
    )

    fecha_importacion: datetime = Field(
        default_factory=datetime.now
    )

    version_bc3: Optional[str] = Field(
        None,
        description="Versión del formato BC3"
    )

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_mongo(self) -> Dict[str, Any]:
        """Convierte los distintos modelos a json para MongoDB"""
        data = self.dict(exclude_none=True)
        if 'id' in data:
            data['_id'] = data.pop('id')

        return data

    @classmethod
    def from_mongo(
        cls,
        data: Dict[str, Any]
    ):
        """Convierte un json de Mongo a una instancia"""
        if '_id' in data:
            data['id'] = str(data.pop('_id'))

        return cls(**data)
