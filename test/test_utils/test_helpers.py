from decimal import Decimal
import json
import tempfile
import os
from src.utils.helpers import BC3Helpers


class TestBC3Helpers:
    """Tests para BC3Helpers"""

    def test_generar_id_unico(self):
        """Test generación de ID único"""
        id1 = BC3Helpers.generar_id_unico("COD01", "archivo1.bc3")
        id2 = BC3Helpers.generar_id_unico("COD01", "archivo2.bc3")
        id3 = BC3Helpers.generar_id_unico("COD02", "archivo1.bc3")

        assert id1 != id2  # Diferentes archivos
        assert id1 != id3  # Diferentes códigos
        assert len(id1) == 32  # MD5 hash length

    def test_limpiar_texto_rtf(self):
        """Test limpieza de texto RTF"""
        texto_rtf = ("{\\rtf1\\ansi\\deff0 {\\fonttbl " +
                     "{\\f0 Times New Roman;}}Texto limpio}")

        texto_limpio = BC3Helpers.limpiar_texto_rtf(texto_rtf)

        assert "Texto limpio" in texto_limpio
        assert "{\\rtf" not in texto_limpio
        assert "\\fonttbl" not in texto_limpio

    def test_limpiar_texto_rtf_vacio(self):
        """Test limpieza de texto RTF vacío"""
        resultado = BC3Helpers.limpiar_texto_rtf("")
        assert resultado == ""

    def test_formatear_importe(self):
        """Test formateo de importe"""
        importe = Decimal("1234567.89")

        formateado = BC3Helpers.formatear_importe(importe)

        assert "1.234.567,89" in formateado

    def test_exportar_a_json(self):
        """Test exportación a JSON"""
        data = {
            "test": "value",
            "number": 123,
            "decimal": Decimal("456.78")
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False) as f:
            temp_path = f.name

        try:
            BC3Helpers.exportar_a_json(data, temp_path)

            # Verificar que el archivo se creó y contiene datos válidos
            assert os.path.exists(temp_path)

            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            assert loaded_data["test"] == "value"
            assert loaded_data["number"] == 123

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_calcular_estadisticas(self, concepto_basico, concepto_partida):
        """Test cálculo de estadísticas"""
        # Configurar conceptos para test
        concepto_basico.determinar_tipo()  # Es capítulo
        concepto_partida.determinar_tipo()  # Es partida

        data = {
            'conceptos': [concepto_basico, concepto_partida],
            'descomposiciones': [],
            'mediciones': [],
            'textos': []
        }

        stats = BC3Helpers.calcular_estadisticas(data)

        assert stats['total_conceptos'] == 2
        assert stats['capitulos'] == 1
        assert stats['partidas'] == 1
        assert stats['importe_total'] > 0
