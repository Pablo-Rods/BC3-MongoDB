from src.models.arbol_conceptos import ArbolConceptos, NodoConcepto


class TestNodoConcepto:
    """Tests para NodoConcepto"""

    def test_crear_nodo_basico(self, concepto_basico):
        """Test creación básica de nodo"""
        nodo = NodoConcepto(
            concepto=concepto_basico,
            archivo_origen="test.bc3"
        )

        assert nodo.concepto.codigo == "CAP01"
        assert nodo.codigo_padre is None
        assert nodo.nivel_jerarquico == 0
        assert nodo.es_raiz() is True
        assert nodo.es_hoja() is True

    def test_agregar_hijo(self, concepto_basico):
        """Test agregar hijo al nodo"""
        nodo = NodoConcepto(
            concepto=concepto_basico,
            archivo_origen="test.bc3"
        )

        nodo.agregar_hijo("HIJO01")

        assert "HIJO01" in nodo.codigos_hijos
        assert nodo.numero_hijos == 1
        assert nodo.tiene_hijos is True
        assert nodo.es_hoja() is False

    def test_calcular_propiedades(self, concepto_basico, medicion_basica):
        """Test cálculo de propiedades del nodo"""
        nodo = NodoConcepto(
            concepto=concepto_basico,
            archivo_origen="test.bc3"
        )

        nodo.agregar_hijo("HIJO01")
        nodo.agregar_medicion(medicion_basica)

        assert nodo.numero_hijos == 1
        assert nodo.numero_mediciones == 1
        assert nodo.importe_propio == concepto_basico.precio
        assert nodo.medicion_total == medicion_basica.medicion_total

    def test_get_path_string(self, concepto_basico):
        """Test obtención de ruta como string"""
        nodo = NodoConcepto(
            concepto=concepto_basico,
            ruta_completa=["RAIZ", "NIVEL1"],
            archivo_origen="test.bc3"
        )

        ruta = nodo.get_path_string()

        assert ruta == "RAIZ > NIVEL1 > CAP01"


class TestArbolConceptos:
    """Tests para ArbolConceptos"""

    def test_crear_arbol_vacio(self):
        """Test creación de árbol vacío"""
        arbol = ArbolConceptos(archivo_origen="test.bc3")

        assert len(arbol.nodos) == 0
        assert len(arbol.nodos_raiz) == 0
        assert arbol.total_nodos == 0
        assert arbol.archivo_origen == "test.bc3"

    def test_agregar_nodo_raiz(self, nodo_raiz):
        """Test agregar nodo raíz"""
        arbol = ArbolConceptos(archivo_origen="test.bc3")

        arbol.agregar_nodo(nodo_raiz)

        assert len(arbol.nodos) == 1
        assert nodo_raiz.concepto.codigo in arbol.nodos_raiz
        assert arbol.total_nodos == 1

    def test_establecer_relacion_padre_hijo(self, arbol_simple):
        """Test establecer relación padre-hijo"""
        # El arbol_simple ya tiene la relación establecida
        nodo_padre = arbol_simple.nodos["CAP01"]
        nodo_hijo = arbol_simple.nodos["PART01"]

        assert "PART01" in nodo_padre.codigos_hijos
        assert nodo_hijo.codigo_padre == "CAP01"
        assert nodo_hijo.nivel_jerarquico == 1

    def test_evitar_relacion_circular(self, arbol_simple):
        """Test prevención de relaciones circulares"""
        # Intentar crear una relación circular
        resultado = arbol_simple.establecer_relacion_padre_hijo(
            "PART01", "CAP01")

        assert resultado is False  # Debe fallar

    def test_obtener_hijos_directos(self, arbol_simple):
        """Test obtener hijos directos"""
        hijos = arbol_simple.obtener_hijos_directos("CAP01")

        assert len(hijos) == 1
        assert hijos[0].concepto.codigo == "PART01"

    def test_obtener_ruta_hasta_raiz(self, arbol_simple):
        """Test obtener ruta hasta raíz"""
        ruta = arbol_simple.obtener_ruta_hasta_raiz("PART01")

        assert len(ruta) == 2
        assert ruta[0].concepto.codigo == "CAP01"  # Raíz primero
        assert ruta[1].concepto.codigo == "PART01"  # Hoja después

    def test_calcular_importes_arbol(self, arbol_simple):
        """Test cálculo de importes del árbol"""
        arbol_simple.calcular_importes_arbol()

        nodo_raiz = arbol_simple.nodos["CAP01"]
        nodo_hijo = arbol_simple.nodos["PART01"]

        assert nodo_hijo.importe_total_arbol == nodo_hijo.importe_propio
        assert nodo_raiz.importe_total_arbol >= nodo_raiz.importe_propio

    def test_obtener_estructura_json(self, arbol_simple):
        """Test obtener estructura JSON"""
        estructura = arbol_simple.obtener_estructura_json()

        assert 'metadata' in estructura
        assert 'arbol' in estructura
        assert estructura['metadata']['total_nodos'] == 2
        assert len(estructura['arbol']) == 1  # Una raíz
