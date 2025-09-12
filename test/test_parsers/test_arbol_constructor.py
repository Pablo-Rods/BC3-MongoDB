import pytest
from src.parsers.arbol_constructor import ArbolConstructor


class TestArbolConstructor:
    """Tests para ArbolConstructor"""

    @pytest.fixture
    def constructor(self):
        return ArbolConstructor()

    def test_crear_nodos(self, constructor, concepto_basico, concepto_partida):
        """Test creación de nodos"""
        conceptos = [concepto_basico, concepto_partida]

        constructor._crear_nodos(conceptos)

        assert len(constructor.arbol.nodos) == 2
        assert "CAP01" in constructor.arbol.nodos
        assert "PART01" in constructor.arbol.nodos

    def test_procesar_descomposiciones(
        self,
        constructor,
        concepto_basico,
        concepto_partida,
        descomposicion_basica
    ):
        """Test procesamiento de descomposiciones"""
        # Crear nodos primero
        conceptos = [concepto_basico, concepto_partida]
        constructor._crear_nodos(conceptos)

        # Procesar descomposiciones
        descomposiciones = [descomposicion_basica]
        constructor._procesar_descomposiciones(descomposiciones)

        assert "CAP01" in constructor.relaciones_padre_hijo
        assert "PART01" in constructor.relaciones_padre_hijo["CAP01"]

    def test_asociar_mediciones_con_padre_valido(
        self,
        constructor,
        concepto_basico,
        concepto_partida,
        medicion_basica
    ):
        """Test asociación de mediciones con padre válido"""
        # Preparar árbol
        conceptos = [concepto_basico, concepto_partida]
        constructor._crear_nodos(conceptos)

        # Establecer relación padre-hijo
        constructor.arbol.nodos["PART01"].codigo_padre = "CAP01"

        # Asociar mediciones
        mediciones = [medicion_basica]
        stats = constructor._asociar_mediciones(mediciones)

        assert stats['mediciones_asociadas'] == 1
        assert constructor.arbol.nodos["PART01"].numero_mediciones == 1

    def test_asociar_mediciones_con_padre_invalido(
        self,
        constructor,
        concepto_basico,
        concepto_partida,
        medicion_basica
    ):
        """Test rechazo de mediciones con padre inválido"""
        # Preparar árbol
        conceptos = [concepto_basico, concepto_partida]
        constructor._crear_nodos(conceptos)

        # NO establecer relación padre-hijo correcta
        constructor.arbol.nodos["PART01"].codigo_padre = "OTRO_PADRE"

        # Asociar mediciones
        mediciones = [medicion_basica]
        stats = constructor._asociar_mediciones(mediciones)

        assert stats['mediciones_rechazadas_padre'] == 1
        assert constructor.arbol.nodos["PART01"].numero_mediciones == 0

    def test_detectar_nivel_por_codigo(self, constructor):
        """Test detección de nivel por código"""
        assert constructor._detectar_nivel_por_codigo("Cap1.1.1") == 2
        assert constructor._detectar_nivel_por_codigo("Cap###") == 3
        assert constructor._detectar_nivel_por_codigo("Cap1") == 1

    def test_construir_arbol_completo(
        self,
        constructor,
        concepto_basico,
        concepto_partida,
        descomposicion_basica,
        medicion_basica
    ):
        """Test construcción completa del árbol"""
        conceptos = [concepto_basico, concepto_partida]
        descomposiciones = [descomposicion_basica]
        mediciones = [medicion_basica]

        arbol = constructor.construir_arbol(
            conceptos, descomposiciones, mediciones)

        assert len(arbol.nodos) == 2
        assert len(arbol.nodos_raiz) >= 1
        assert arbol.total_nodos == 2

        # Verificar relación establecida
        nodo_hijo = arbol.nodos["PART01"]
        assert nodo_hijo.codigo_padre == "CAP01"
        assert nodo_hijo.nivel_jerarquico == 1

    def test_obtener_estadisticas_construccion(
        self,
        constructor,
        concepto_basico,
        concepto_partida
    ):
        """Test obtención de estadísticas"""
        conceptos = [concepto_basico, concepto_partida]
        constructor._crear_nodos(conceptos)

        stats = constructor.obtener_estadisticas_construccion()

        assert stats['total_nodos'] == 2
        assert 'nodos_raiz' in stats
        assert 'relaciones_padre_hijo' in stats
