from src.utils.arbol_validator import ArbolValidator
from src.models.arbol_conceptos import ArbolConceptos, NodoConcepto
from src.models.concepto import Concepto


class TestArbolValidator:
    """Tests para ArbolValidator"""

    def test_validar_arbol_valido(self, arbol_simple):
        """Test validación de árbol válido"""
        resultado = ArbolValidator.validar_arbol(arbol_simple)

        assert resultado['valido'] is True
        assert len(resultado['errores']) == 0

    def test_detectar_referencias_circulares(self):
        """Test detección de referencias circulares"""
        # Crear árbol con referencia circular
        arbol = ArbolConceptos(archivo_origen="test.bc3")

        concepto_a = Concepto(codigo="A", archivo_origen="test.bc3")
        concepto_b = Concepto(codigo="B", archivo_origen="test.bc3")

        nodo_a = NodoConcepto(concepto=concepto_a, archivo_origen="test.bc3")
        nodo_b = NodoConcepto(concepto=concepto_b, archivo_origen="test.bc3")

        # Crear referencia circular: A -> B -> A
        nodo_a.agregar_hijo("B")
        nodo_b.codigo_padre = "A"
        nodo_b.agregar_hijo("A")
        nodo_a.codigo_padre = "B"

        arbol.agregar_nodo(nodo_a)
        arbol.agregar_nodo(nodo_b)

        circulares = ArbolValidator._detectar_referencias_circulares(arbol)

        assert len(circulares) > 0

    def test_detectar_huerfanos(self):
        """Test detección de nodos huérfanos"""
        arbol = ArbolConceptos(archivo_origen="test.bc3")

        # Crear concepto huérfano (sin padre ni hijos)
        concepto_huerfano = Concepto(
            codigo="HUERFANO", archivo_origen="test.bc3")
        nodo_huerfano = NodoConcepto(
            concepto=concepto_huerfano, archivo_origen="test.bc3")

        arbol.agregar_nodo(nodo_huerfano)

        huerfanos = ArbolValidator._detectar_huerfanos(arbol)

        assert "HUERFANO" in huerfanos

    def test_verificar_consistencia_niveles(self):
        """Test verificación de consistencia de niveles"""
        arbol = ArbolConceptos(archivo_origen="test.bc3")

        concepto_padre = Concepto(codigo="PADRE", archivo_origen="test.bc3")
        concepto_hijo = Concepto(codigo="HIJO", archivo_origen="test.bc3")

        nodo_padre = NodoConcepto(
            concepto=concepto_padre,
            nivel_jerarquico=0,
            archivo_origen="test.bc3"
        )
        nodo_hijo = NodoConcepto(
            concepto=concepto_hijo,
            codigo_padre="PADRE",
            nivel_jerarquico=5,  # Nivel inconsistente (debería ser 1)
            archivo_origen="test.bc3"
        )

        arbol.agregar_nodo(nodo_padre)
        arbol.agregar_nodo(nodo_hijo)

        inconsistencias = ArbolValidator._verificar_consistencia_niveles(arbol)

        assert len(inconsistencias) > 0
        assert "HIJO" in inconsistencias[0]
