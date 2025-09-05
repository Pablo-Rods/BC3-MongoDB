# BC3 Parser - Constructor de Árboles Jerárquicos

Un parser especializado para archivos BC3 (Base de Costos de la Construcción) desarrollado en Python, enfocado en la **construcción y almacenamiento de estructuras jerárquicas** de presupuestos de construcción con integración completa a MongoDB.

## 🌳 Características Principales

- **Constructor de Árboles Jerárquicos**: Construcción automática de estructuras de árbol desde descomposiciones BC3
- **Validación de Integridad**: Detección de referencias circulares, nodos huérfanos e inconsistencias
- **Almacenamiento Optimizado**: Guardado eficiente de estructuras completas en MongoDB
- **Parser Completo BC3**: Soporte para todos los tipos de registro (~C, ~D, ~M, ~T, ~X)
- **Detección Automática de Jerarquía**: Análisis inteligente por códigos y descomposiciones
- **Exportación JSON**: Capacidad de exportar árboles completos a formato JSON
- **Cálculo de Importes**: Propagación automática de costos a través del árbol
- **Gestión de Mediciones**: Asociación y cálculo de mediciones por concepto

## 🏗️ Arquitectura del Sistema

### Modelos de Datos

| Modelo           | Descripción                                 | Uso Principal                        |
| ---------------- | ------------------------------------------- | ------------------------------------ |
| `Concepto`       | Partidas, capítulos y materiales (~C)       | Nodos básicos del árbol              |
| `NodoConcepto`   | Nodo enriquecido con relaciones jerárquicas | Elemento del árbol con padre/hijos   |
| `ArbolConceptos` | Estructura completa del árbol               | Contenedor principal del presupuesto |
| `Descomposicion` | Relaciones padre-hijo (~D)                  | Definición de estructura             |
| `Medicion`       | Líneas de medición (~M)                     | Cantidades y cálculos                |

### Componentes Clave

- **ArbolConstructor**: Construye la estructura jerárquica completa
- **ArbolValidator**: Valida integridad y detecta problemas
- **BC3ArbolRepository**: Gestión especializada de persistencia
- **BC3ArbolOnlyReader**: Reader optimizado solo para árboles

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

### Uso Básico - Solo Árbol

```python
from main import BC3ArbolOnlyReader

# Crear instancia del reader especializado
reader = BC3ArbolOnlyReader()

# Importar archivo BC3 y construir árbol
success = reader.importar_solo_arbol(
    './data/presupuesto.bc3',
    exportar_arbol_json=True,
    validar_arbol=True,
    sobrescribir=False
)

if success:
    print("Árbol importado exitosamente")
```

### Construcción Manual del Árbol

```python
from parsers.bc3_parser import BC3Parser
from parsers.arbol_constructor import ArbolConstructor
from utils.arbol_validator import ArbolValidator

# Parsear archivo BC3
parser = BC3Parser()
datos = parser.parse_file('./data/presupuesto.bc3')

# Construir árbol
constructor = ArbolConstructor()
arbol = constructor.construir_arbol(
    datos['conceptos'],
    datos['descomposiciones'],
    datos['mediciones']
)

# Validar integridad
resultado = ArbolValidator.validar_arbol(arbol)
print(f"Árbol válido: {resultado['valido']}")
```

### Consultas del Árbol

```python
from database.connection import MongoDBConnection
from database.repository_arbol import BC3ArbolRepository

with MongoDBConnection() as conn:
    repo = BC3ArbolRepository(conn)

    # Obtener estructura completa
    estructura = repo.obtener_arbol_completo("presupuesto.bc3")

    # Obtener nodos raíz
    raices = repo.obtener_nodos_raiz("presupuesto.bc3")

    # Obtener hijos directos
    hijos = repo.obtener_hijos_directos("CAP01", "presupuesto.bc3")

    # Obtener ruta hasta raíz
    ruta = repo.obtener_ruta_hasta_raiz("PART_001", "presupuesto.bc3")
```

## 📊 Estructura del Árbol

### NodoConcepto

Cada nodo del árbol contiene:

```python
{
    "concepto": {                    # Datos del concepto (~C)
        "codigo": "CAP01",
        "resumen": "Movimiento de tierras",
        "precio": 1500.00,
        "tipo": "0"
    },
    "estructura": {                  # Relaciones jerárquicas
        "codigo_padre": None,        # null para raíces
        "codigos_hijos": ["SUBCAP01", "SUBCAP02"],
        "nivel_jerarquico": 0,
        "ruta_completa": [],
        "es_raiz": True,
        "es_hoja": False
    },
    "mediciones": [...],             # Mediciones asociadas
    "estadisticas": {               # Datos calculados
        "numero_hijos": 2,
        "numero_mediciones": 0,
        "importe_propio": 1500.00,
        "importe_total_arbol": 25000.00
    }
}
```

### ArbolConceptos

La estructura completa incluye:

```python
{
    "metadata": {
        "total_nodos": 150,
        "niveles_maximos": 4,
        "importe_total_presupuesto": 150000.00
    },
    "arbol": [                      # Estructura anidada desde raíces
        {
            "codigo": "CAP01",
            "resumen": "Movimiento de tierras",
            "hijos": [
                {
                    "codigo": "SUBCAP01",
                    "hijos": [...]
                }
            ]
        }
    ]
}
```

## 🗄️ Base de Datos

### Colecciones MongoDB

#### Estructura del Árbol

- **arbol_conceptos**: Estructuras completas de árboles
- **nodos_arbol**: Nodos individuales para consultas rápidas

#### Datos Planos (Opcionales)

- **conceptos**: Partidas, capítulos y materiales originales
- **descomposiciones**: Relaciones padre-hijo originales
- **mediciones**: Líneas de medición originales
- **metadata**: Información de archivos BC3

### Índices Optimizados

```javascript
// Índices para estructura del árbol
{ "archivo_origen": 1, "tipo": 1 }

// Índices para nodos individuales
{ "codigo": 1, "archivo_origen": 1 }  // único
{ "estructura.codigo_padre": 1 }
{ "estructura.nivel_jerarquico": 1 }
{ "estructura.es_raiz": 1 }
{ "concepto.tipo": 1 }
```

## 🔧 Configuración Avanzada

### Constructor de Árboles

```python
class Settings:
    # Detección automática de jerarquía
    DETECTAR_JERARQUIA_AUTOMATICA: bool = True
    VALIDAR_ARBOL_AUTOMATICO: bool = True
    CALCULAR_IMPORTES_ARBOL: bool = True

    # Límites del árbol
    MAX_NIVELES_ARBOL: int = 10

    # Tipos de concepto para jerarquía
    TIPOS_CAPITULO: list = ['0', '1']  # Capítulos
    TIPOS_PARTIDA: list = ['2', '3']   # Partidas
    TIPOS_MATERIAL: list = ['4', '5']  # Materiales
```

### Validación del Árbol

```python
# Validación automática
resultado = ArbolValidator.validar_arbol(arbol)

print(f"Válido: {resultado['valido']}")
print(f"Errores: {len(resultado['errores'])}")
print(f"Advertencias: {len(resultado['advertencias'])}")

# Tipos de validación:
# - Referencias circulares
# - Nodos huérfanos
# - Inconsistencias de nivel
# - Integridad referencial
```

## 🧪 Ejemplos de Consulta

### Obtener Estructura Jerárquica

```python
# Obtener árbol completo con jerarquía
estructura = repo.obtener_estructura_completa("presupuesto.bc3")

# Navegar por niveles
nodos_nivel_0 = repo.obtener_nodos_por_nivel(0, "presupuesto.bc3")
nodos_nivel_1 = repo.obtener_nodos_por_nivel(1, "presupuesto.bc3")

# Buscar por tipo
capitulos = repo.buscar_nodos_por_tipo("0", "presupuesto.bc3")
partidas = repo.buscar_nodos_por_tipo("2", "presupuesto.bc3")
```

### Consultas Avanzadas

```python
# Obtener todos los descendientes de un capítulo
descendientes = repo.obtener_todos_descendientes("CAP01", "presupuesto.bc3")

# Obtener ruta completa hasta raíz
ruta = repo.obtener_ruta_hasta_raiz("PART_001", "presupuesto.bc3")

# Nodos con mediciones
con_mediciones = repo.obtener_nodos_con_mediciones("presupuesto.bc3")

# Estadísticas del árbol
stats = repo.calcular_estadisticas_arbol("presupuesto.bc3")
```

## 📁 Estructura del Proyecto

```
bc3-parser/
├── config/
│   └── settings.py              # Configuración completa
├── database/
│   ├── connection.py            # Gestión MongoDB
│   ├── repository.py            # Operaciones básicas
│   └── repository_arbol.py      # Operaciones de árbol
├── models/
│   ├── base_model.py            # Modelo base Pydantic
│   ├── concepto.py              # Modelo concepto
│   ├── arbol_conceptos.py       # Modelos de árbol
│   ├── descomposicion.py        # Modelo descomposición
│   ├── medicion.py              # Modelo medición
│   └── texto.py                 # Modelo texto
├── parsers/
│   ├── bc3_parser.py            # Parser principal BC3
│   ├── record_parsers.py        # Parsers por registro
│   └── arbol_constructor.py     # Constructor de árboles
├── utils/
│   ├── helpers.py               # Funciones auxiliares
│   ├── validators.py            # Validadores de datos
│   └── arbol_validator.py       # Validador de árboles
├── main.py                      # Reader especializado en árboles
└── README.md
```

## 🚦 Logging y Monitoreo

```python
# Configuración de logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bc3_import.log'),
        logging.StreamHandler()
    ]
)

# Logs específicos del proceso:
# - Parseo de archivo BC3
# - Construcción del árbol
# - Detección de jerarquía
# - Validación de integridad
# - Guardado en MongoDB
```

## ⚠️ Consideraciones Importantes

### Construcción del Árbol

- **Detección Automática**: El sistema detecta jerarquías por descomposiciones y códigos
- **Validación Estricta**: Se validan referencias circulares y consistencia
- **Cálculo de Importes**: Los importes se propagan automáticamente en el árbol
- **Optimización**: Almacenamiento eficiente para consultas rápidas

### Rendimiento

- **Construcción por Lotes**: Procesamiento eficiente de archivos grandes
- **Índices Especializados**: Optimización para consultas jerárquicas
- **Almacenamiento Dual**: Estructura completa + nodos individuales
- **Validación Opcional**: Puede desactivarse para mejorar rendimiento

### Limitaciones

- **Archivos Muy Grandes**: > 100MB pueden requerir ajustes de memoria
- **Jerarquías Complejas**: Máximo 10 niveles por defecto
- **Referencias Circulares**: Se detectan y rechazan automáticamente

## 🔄 Flujo de Procesamiento

1. **Parseo BC3** → Extracción de registros (~C, ~D, ~M)
2. **Creación de Nodos** → Conversión de conceptos a nodos
3. **Detección de Jerarquía** → Análisis de descomposiciones y códigos
4. **Construcción del Árbol** → Establecimiento de relaciones padre-hijo
5. **Validación** → Verificación de integridad y consistencia
6. **Cálculo de Importes** → Propagación de costos en el árbol
7. **Persistencia** → Guardado optimizado en MongoDB
8. **Indexación** → Creación de índices para consultas rápidas

## 📈 Estadísticas y Métricas

El sistema proporciona estadísticas detalladas:

```python
{
    "parseo": {
        "conceptos_parseados": 150,
        "descomposiciones_parseadas": 45,
        "mediciones_parseadas": 200
    },
    "construccion": {
        "total_nodos": 150,
        "nodos_raiz": 3,
        "niveles_maximos": 4,
        "relaciones_establecidas": 147,
        "nodos_con_mediciones": 80
    },
    "validacion": {
        "valido": True,
        "referencias_circulares": 0,
        "huerfanos": 2,
        "inconsistencias_nivel": 0
    }
}
```
