# BC3 Parser

Un parser robusto para archivos BC3 (Base de Costos de la Construcción) desarrollado en Python, con integración completa a MongoDB para almacenamiento y consulta de datos de presupuestos de construcción.

## 🏗️ Características

- **Parser completo BC3**: Soporte para todos los tipos de registro (~C, ~D, ~M, ~T, ~X)
- **Integración MongoDB**: Almacenamiento estructurado con índices optimizados
- **Modelos Pydantic**: Validación de datos y serialización robusta
- **Gestión de encoding**: Detección automática de codificación de archivos
- **Procesamiento por lotes**: Inserción eficiente de grandes volúmenes de datos
- **Logging completo**: Seguimiento detallado del proceso de importación
- **Exportación JSON**: Capacidad de exportar datos parseados

## 📋 Tipos de Registro Soportados

| Tipo | Descripción                                 | Modelo           |
| ---- | ------------------------------------------- | ---------------- |
| ~C   | Conceptos (partidas, capítulos, materiales) | `Concepto`       |
| ~D   | Descomposiciones (componentes de conceptos) | `Descomposicion` |
| ~M   | Mediciones (líneas de medición)             | `Medicion`       |
| ~T   | Textos descriptivos                         | `Texto`          |
| ~X   | Textos de pliego de condiciones             | `TextoPliego`    |

## 🚀 Instalación

### Requisitos

- Python 3.8+
- MongoDB 4.0+

### Dependencias

```bash
pip install -r requirements.txt
```

### Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=bc3_database
BC3_ENCODING=cp1252
```

## 💻 Uso

### Uso Básico

```python
from main import BC3Reader

# Crear instancia del reader
reader = BC3Reader()

# Importar archivo BC3
success = reader.importar_archivo('./data/presupuesto.bc3')

if success:
    print("Importación completada exitosamente")
```

### Uso Avanzado

```python
from database.connection import MongoDBConnection
from database.repository import BC3Repository
from parsers.bc3_parser import BC3Parser

# Parser personalizado
parser = BC3Parser(encoding='latin-1')
datos = parser.parse_file('./data/presupuesto.bc3')

# Conexión a base de datos
with MongoDBConnection() as conn:
    repo = BC3Repository(conn)
    resultado = repo.save_all(datos)

    print(f"Conceptos insertados: {resultado['conceptos_insertados']}")
```

## 📊 Estructura de Datos

### Concepto

Representa partidas, capítulos y materiales del presupuesto:

```python
{
    "codigo": "OUM1234",
    "unidad": "m2",
    "resumen": "Excavación en terreno de cualquier naturaleza",
    "precio": 15.50,
    "tipo": "2",
    "es_partida": True,
    "nivel": 1
}
```

### Descomposición

Define los componentes que forman un concepto:

```python
{
    "codigo_padre": "OUM1234",
    "componentes": [
        {
            "codigo_componente": "MO001",
            "factor": 0.5,
            "rendimiento": 1.0
        }
    ],
    "numero_componetes": 3,
    "importe_total": 45.75
}
```

### Medición

Contiene las líneas de medición para cada concepto:

```python
{
    "codigo_padre": "OUM1234",
    "codigo_hijo": "MO001",
    "lineas_medición": [
        {
            "tipo_linea": 1,
            "comentario": "Zona A",
            "unidades": 2,
            "longitud": 10.0,
            "anchura": 5.0,
            "parcial": 100.0
        }
    ],
    "total_medicion": 100.0
}
```

## 🗄️ Base de Datos

### Colecciones MongoDB

- **conceptos**: Partidas, capítulos y materiales
- **descomposiciones**: Componentes de cada concepto
- **mediciones**: Líneas de medición
- **textos**: Descripciones detalladas
- **metadata**: Información del archivo BC3

### Índices Creados Automáticamente

```javascript
// Conceptos
{ "codigo": 1 }
{ "tipo": 1 }
{ "archivo_origen": 1 }

// Descomposiciones
{ "codigo_padre": 1 }
{ "codigo_padre": 1, "archivo_origen": 1 }

// Mediciones
{ "codigo_padre": 1 }
{ "codigo_hijo": 1 }
{ "codigo_padre": 1, "codigo_hijo": 1 }
```

## 🔧 Configuración

La configuración se gestiona a través del archivo `config/settings.py`:

```python
class Settings:
    # Database
    MONGO_URI: str
    MONGO_DATABASE: str

    # BC3 Processing
    DEFAULT_ENCODING: str = "cp1252"
    FIELD_SEPARATOR: str = "|"
    RECORD_SEPARATOR: str = "~"

    # Collections
    CONCEPTOS_COLLECTION: str = "conceptos"
    DESCOMPOSICIONES_COLLECTION: str = "descomposiciones"
    # ...

    # Batch Processing
    BATCH_SIZE: int = 100
    MAX_RETIES: int = 3
```

## 🧪 Ejemplos de Consulta

### Buscar un Concepto

```python
from database.connection import MongoDBConnection
from database.repository import BC3Repository

with MongoDBConnection() as conn:
    repo = BC3Repository(conn)

    # Buscar por código
    concepto = repo.buscar_concepto("OUM1234")

    # Buscar descomposición
    descomp = repo.buscar_descomposicion("OUM1234")
```

### Consultas MongoDB Directas

```javascript
// Encontrar todos los capítulos
db.conceptos.find({ tipo: { $in: ["0", "1"] } });

// Conceptos sin precio
db.conceptos.find({ precio: null });

// Mediciones de un concepto específico
db.mediciones.find({ codigo_padre: "OUM1234" });
```

## 📁 Estructura del Proyecto

```
bc3-parser/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuración de la aplicación
├── database/
│   ├── __init__.py
│   ├── connection.py        # Gestión de conexión MongoDB
│   └── repository.py        # Operaciones de base de datos
├── models/
│   ├── __init__.py
│   ├── base_model.py        # Modelo base Pydantic
│   ├── concepto.py          # Modelo para conceptos
│   ├── descomposicion.py    # Modelo para descomposiciones
│   ├── medicion.py          # Modelo para mediciones
│   └── texto.py             # Modelo para textos
├── parsers/
│   ├── __init__.py
│   ├── bc3_parser.py        # Parser principal BC3
│   └── record_parsers.py    # Parsers por tipo de registro
├── utils/
│   ├── __init__.py
│   ├── helpers.py           # Funciones auxiliares
│   └── validators.py        # Validadores de datos
├── data/                    # Archivos BC3 de ejemplo (git ignored)
├── main.py                  # Punto de entrada principal
├── requirements.txt
├── .gitignore
└── README.md
```

## 🚦 Logging

El sistema incluye logging completo con diferentes niveles:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bc3_import.log'),
        logging.StreamHandler()
    ]
)
```

## ⚠️ Consideraciones

### Encoding de Archivos

Los archivos BC3 suelen usar codificación `cp1252` o `latin-1`. El parser incluye detección automática de encoding.

### Rendimiento

- Procesamiento por lotes para grandes archivos
- Índices optimizados para consultas frecuentes
- Gestión de memoria eficiente

### Validación

- Validación de datos con Pydantic
- Verificación de integridad referencial
- Manejo robusto de errores
