from src.models.descomposicion import Descomposicion, ComponenteDescomposicion
from src.models.arbol_conceptos import ArbolConceptos, NodoConcepto
from src.models.medicion import Medicion, LineaMedicion
from src.models.concepto import Concepto
from src.models.texto import Texto

from unittest.mock import Mock
from decimal import Decimal

import pytest
import tempfile
import os


from src.database.connection import MongoDBConnection


@pytest.fixture
def concepto_basico():
    """Fixture para un concepto básico"""
    return Concepto(
        codigo="CAP01",
        unidad="ud",
        resumen="Capítulo de prueba",
        precio=Decimal("1500.50"),
        tipo="0",
        archivo_origen="test.bc3"
    )


@pytest.fixture
def concepto_partida():
    """Fixture para una partida"""
    return Concepto(
        codigo="PART01",
        unidad="m2",
        resumen="Partida de excavación",
        precio=Decimal("25.75"),
        tipo="2",
        archivo_origen="test.bc3"
    )


@pytest.fixture
def descomposicion_basica():
    """Fixture para una descomposición básica"""
    componente = ComponenteDescomposicion(
        codigo_componente="PART01",
        factor=Decimal("1.0"),
        rendimiento=Decimal("100.0"),
        archivo_origen="test.bc3"
    )

    return Descomposicion(
        codigo_padre="CAP01",
        componentes=[componente],
        archivo_origen="test.bc3"
    )


@pytest.fixture
def linea_medicion_basica():
    """Fixture para una línea de medición"""
    return LineaMedicion(
        tipo_linea=1,
        comentario="Medición de prueba",
        unidades=Decimal("2.0"),
        longitud=Decimal("10.0"),
        latitud=Decimal("5.0"),
        altura=Decimal("3.0"),
        archivo_origen="test.bc3"
    )


@pytest.fixture
def medicion_basica(linea_medicion_basica):
    """Fixture para una medición básica"""
    return Medicion(
        codigo_padre="CAP01",
        codigo_hijo="PART01",
        medicion_total=Decimal("300.0"),
        lineas_medición=[linea_medicion_basica],
        archivo_origen="test.bc3"
    )


@pytest.fixture
def texto_basico():
    """Fixture para un texto básico"""
    return Texto(
        codigo="CAP01",
        texto="Descripción detallada del capítulo",
        archivo_origen="test.bc3"
    )


@pytest.fixture
def nodo_raiz(concepto_basico):
    """Fixture para un nodo raíz"""
    return NodoConcepto(
        concepto=concepto_basico,
        codigo_padre=None,
        nivel_jerarquico=0,
        ruta_completa=[],
        archivo_origen="test.bc3"
    )


@pytest.fixture
def arbol_simple(concepto_basico, concepto_partida):
    """Fixture para un árbol simple"""
    arbol = ArbolConceptos(archivo_origen="test.bc3")

    # Crear nodos
    nodo_raiz = NodoConcepto(
        concepto=concepto_basico,
        codigo_padre=None,
        nivel_jerarquico=0,
        ruta_completa=[],
        archivo_origen="test.bc3"
    )

    nodo_hijo = NodoConcepto(
        concepto=concepto_partida,
        codigo_padre="CAP01",
        nivel_jerarquico=1,
        ruta_completa=["CAP01"],
        archivo_origen="test.bc3"
    )

    # Agregar al árbol
    arbol.agregar_nodo(nodo_raiz)
    arbol.agregar_nodo(nodo_hijo)

    # Establecer relación
    arbol.establecer_relacion_padre_hijo("CAP01", "PART01")

    return arbol


@pytest.fixture
def mock_mongo_connection():
    """Mock de conexión MongoDB"""
    mock_conn = Mock(spec=MongoDBConnection)
    mock_conn._is_connected.return_value = True
    mock_conn.get_collection.return_value = Mock()
    return mock_conn


@pytest.fixture
def sample_bc3_content():
    """Contenido de ejemplo de archivo BC3"""
    return """~V|FIEBDC-3/2004|ANSI|FIEBDC-3|
~K|GENERADOR|v1.0|01/01/2024|
~C|CAP01|ud|Movimiento de tierras|1500.50|01/01/2024|0|
~C|PART01|m2|Excavación en zanja|25.75|01/01/2024|2|
~C|MAT01|ud|Arena de río|15.25|01/01/2024|4|
~D|CAP01|PART01\\1.00\\100.00\\|
~D|PART01|MAT01\\2.50\\80.00\\|
~M|CAP01\\PART01||300.00|1\\Medición capítulo\\\\2.0\\10.0\\5.0\\3.0\\|
~T|CAP01|Descripción detallada del movimiento de tierras|
"""


@pytest.fixture
def temp_bc3_file(sample_bc3_content):
    """Archivo temporal BC3 para tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bc3',
                                     delete=False, encoding='utf-8') as f:
        f.write(sample_bc3_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)
