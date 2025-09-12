from decimal import Decimal
from src.models.concepto import Concepto


class TestConcepto:
    """Tests para el modelo Concepto"""

    def test_crear_concepto_basico(self):
        """Test creación básica de concepto"""
        concepto = Concepto(
            codigo="TEST01",
            unidad="m2",
            resumen="Concepto de prueba",
            precio=Decimal("100.50"),
            archivo_origen="test.bc3"
        )

        assert concepto.codigo == "TEST01"
        assert concepto.unidad == "m2"
        assert concepto.resumen == "Concepto de prueba"
        assert concepto.precio == Decimal("100.50")
        assert concepto.archivo_origen == "test.bc3"

    def test_determinar_tipo_capitulo(self):
        """Test determinación de tipo capítulo"""
        concepto = Concepto(
            codigo="CAP01",
            tipo="0",
            archivo_origen="test.bc3"
        )

        concepto.determinar_tipo()

        assert concepto.es_capitulo is True
        assert concepto.es_partida is False

    def test_determinar_tipo_partida(self):
        """Test determinación de tipo partida"""
        concepto = Concepto(
            codigo="PART01",
            tipo="2",
            archivo_origen="test.bc3"
        )

        concepto.determinar_tipo()

        assert concepto.es_capitulo is False
        assert concepto.es_partida is True

    def test_determinar_tipo_con_simbolo_porcentaje(self):
        """Test tipo especial con símbolo %"""
        concepto = Concepto(
            codigo="CAP01",
            tipo="%",
            archivo_origen="test.bc3"
        )

        concepto.determinar_tipo()

        assert concepto.es_capitulo is True

    def test_nivel_por_codigo_con_hashtags(self):
        """Test cálculo de nivel por hashtags"""
        concepto = Concepto(
            codigo="CAP##",
            archivo_origen="test.bc3"
        )

        concepto.determinar_tipo()

        assert concepto.nivel == 3  # 2 hashtags + 1

    def test_to_mongo_conversion(self):
        """Test conversión a formato MongoDB"""
        concepto = Concepto(
            codigo="TEST01",
            precio=Decimal("100.50"),
            archivo_origen="test.bc3"
        )

        mongo_doc = concepto.to_mongo()

        assert mongo_doc['codigo'] == "TEST01"
        assert mongo_doc['precio'] == 100.50  # Convertido a float
        assert 'fecha_importacion' in mongo_doc

    def test_from_mongo_conversion(self):
        """Test conversión desde formato MongoDB"""
        mongo_data = {
            '_id': 'test_id',
            'codigo': 'TEST01',
            'precio': 100.50,
            'archivo_origen': 'test.bc3'
        }

        concepto = Concepto.from_mongo(mongo_data)

        assert concepto.id == 'test_id'
        assert concepto.codigo == 'TEST01'
        assert concepto.precio == 100.50
