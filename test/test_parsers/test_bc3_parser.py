import pytest
from unittest.mock import patch, mock_open
from src.parsers.bc3_parser import BC3Parser


class TestBC3Parser:
    """Tests para BC3Parser"""

    @pytest.fixture
    def parser(self):
        return BC3Parser()

    def test_extract_metadata(self, parser, sample_bc3_content):
        """Test extracción de metadata"""
        metadata = parser._BC3Parser__extract_metadata(
            "test.bc3", sample_bc3_content)

        assert metadata['archivo'] == "test.bc3"
        assert metadata['version_bc3'] == "FIEBDC-3/2004"
        assert metadata['programa_origen'] == "GENERADOR"

    def test_split_records(self, parser, sample_bc3_content):
        """Test división en registros"""
        records = parser._BC3Parser__split_records(sample_bc3_content)

        # Debe tener varios registros
        assert len(records) > 0
        # Todos los registros deben empezar con ~
        for record in records:
            if record.strip():
                assert record.strip().startswith('~')

    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('pathlib.Path.stat')
    def test_read_file_success(
        self,
        mock_stat,
        mock_exists,
        mock_file,
        parser,
        sample_bc3_content
    ):
        """Test lectura exitosa de archivo"""
        mock_file.return_value.read.return_value = sample_bc3_content
        mock_stat.return_value.st_size = len(sample_bc3_content)

        content = parser._BC3Parser__read_file("test.bc3")

        assert content == sample_bc3_content

    @patch('pathlib.Path.exists', return_value=False)
    def test_read_file_not_found(self, mock_exists, parser):
        """Test lectura de archivo no encontrado"""
        with pytest.raises(FileNotFoundError):
            parser._BC3Parser__read_file("nonexistent.bc3")

    def test_parse_file_integration(self, parser, temp_bc3_file):
        """Test integración completa de parsing"""
        resultado = parser.parse_file(temp_bc3_file)

        assert 'conceptos' in resultado
        assert 'descomposiciones' in resultado
        assert 'mediciones' in resultado
        assert 'textos' in resultado
        assert 'metadata' in resultado

        assert len(resultado['conceptos']) > 0
        assert len(resultado['descomposiciones']) > 0
