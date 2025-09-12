import pytest
from decimal import Decimal
from src.parsers.record_parsers import RecordParser


class TestRecordParser:
    """Tests para RecordParser"""

    @pytest.fixture
    def parser(self):
        return RecordParser()

    def test_parse_concepto_basico(self, parser):
        """Test parsing de concepto básico"""
        record = "~C|CAP01|ud|Capítulo de prueba|1500.50|01/01/2024|0|"

        concepto = parser.parse_concepto(record, "test.bc3")

        assert concepto is not None
        assert concepto.codigo == "CAP01"
        assert concepto.unidad == "ud"
        assert concepto.resumen == "Capítulo de prueba"
        assert concepto.precio == Decimal("1500.50")
        assert concepto.tipo == "0"

    def test_parse_concepto_con_codigo_complejo(self, parser):
        """Test parsing de concepto con código complejo"""
        record = "~C|CAP01#SUBCAP|ud|Subcapítulo|100.00||1|"

        concepto = parser.parse_concepto(record, "test.bc3")

        assert concepto.codigo == "CAP01"  # Debe limpiar el #SUBCAP

    def test_parse_descomposicion_basica(self, parser):
        """Test parsing de descomposición básica"""
        record = "~D|CAP01|PART01\\1.00\\100.00\\PART02\\2.00\\50.00\\|"

        descomposicion = parser.parse_descomposicion(record, "test.bc3")

        assert descomposicion is not None
        assert descomposicion.codigo_padre == "CAP01"
        assert len(descomposicion.componentes) == 2
        assert descomposicion.componentes[0].codigo_componente == "PART01"
        assert descomposicion.componentes[0].factor == Decimal("1.00")

    def test_parse_medicion_con_lineas(self, parser):
        """Test parsing de medición con líneas"""
        record = ("~M|CAP01\\PART01||300.00|1\\Comentario\\\\" +
                  "2.0\\10.0\\5.0\\3.0\\|")

        medicion = parser.parse_medicion(record, "test.bc3")

        assert medicion is not None
        assert medicion.codigo_padre == "CAP01"
        assert medicion.codigo_hijo == "PART01"
        assert medicion.medicion_total == Decimal("300.00")
        assert len(medicion.lineas_medición) == 1

        linea = medicion.lineas_medición[0]
        assert linea.tipo_linea == 1
        assert linea.unidades == Decimal("2.0")
        assert linea.longitud == Decimal("10.0")

    def test_parse_texto_basico(self, parser):
        """Test parsing de texto básico"""
        record = "~T|CAP01|Descripción del capítulo\\nCon salto de línea|"

        texto = parser.parse_texto(record, "test.bc3")

        assert texto is not None
        assert texto.codigo == "CAP01"
        assert "Descripción del capítulo" in texto.texto

    def test_parse_decimal_con_coma(self, parser):
        """Test parsing de decimal con coma europea"""
        valor = parser._RecordParser__parse_decimal("1.500,25")
        assert valor == Decimal("1500.25")

    def test_parse_decimal_invalido(self, parser):
        """Test parsing de decimal inválido"""
        valor = parser._RecordParser__parse_decimal("abc")
        assert valor is None

    def test_clean_field_con_escape(self, parser):
        """Test limpieza de campo con caracteres de escape"""
        campo_limpio = parser._RecordParser__clean_field(
            "Texto\\ncon\\tescapes")
        assert campo_limpio == "Texto\ncon\tescapes"
