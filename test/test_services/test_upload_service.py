import pytest
from unittest.mock import Mock, patch
from src.services.upload_service import UploadService


class TestUploadService:
    """Tests para UploadService"""

    @pytest.fixture
    def service(self):
        return UploadService(
            mongo_uri="mongodb://localhost:27017",
            database="test_db"
        )

    @patch('src.services.upload_service.Path.exists')
    def test_importar_solo_arbol_archivo_no_existe(self, mock_exists, service):
        """Test importación con archivo inexistente"""
        mock_exists.return_value = False

        resultado = service.importar_solo_arbol(
            "nonexistent.bc3",
            "test_project",
            validar_arbol=False
        )

        assert resultado is False

    @patch('src.services.upload_service.MongoDBConnection')
    @patch('src.services.upload_service.Path.exists')
    def test_importar_solo_arbol_sobrescribir_false_existe(
            self,
            mock_exists,
            mock_conn_class,
            service
    ):
        """Test importación sin sobrescribir cuando ya existe"""
        mock_exists.return_value = True

        # Mock connection and repository
        mock_conn = Mock()
        mock_conn_class.return_value.__enter__.return_value = mock_conn

        mock_repo = Mock()
        mock_repo.verificar_arbol_existente.return_value = {'existe': True}

        with patch('src.services.upload_service.BC3ArbolRepository',
                   return_value=mock_repo):
            resultado = service.importar_solo_arbol(
                "test.bc3",
                "existing_project",
                sobrescribir=False
            )

        assert resultado is False

    @patch('src.services.upload_service.MongoDBConnection')
    @patch('src.services.upload_service.BC3ArbolRepository')
    @patch('src.services.upload_service.ArbolValidator')
    @patch('src.services.upload_service.Path.exists')
    def test_importar_solo_arbol_success(
        self,
        mock_exists,
        mock_validator,
        mock_repo_class,
        mock_conn_class,
        service,
        temp_bc3_file
    ):
        """Test importación exitosa"""
        mock_exists.return_value = True

        # Mock parser results
        service.parser.parse_file = Mock(return_value={
            'conceptos': [Mock()],
            'descomposiciones': [Mock()],
            'mediciones': [Mock()],
            'textos': [Mock()],
            'metadata': {'archivo': 'test.bc3'}
        })

        # Mock constructor results
        mock_arbol = Mock()
        service.arbol_constructor.construir_arbol = Mock(
            return_value=mock_arbol)
        service.arbol_constructor.obtener_estadisticas_construccion = Mock(
            return_value={'total_nodos': 2})

        # Mock validator
        mock_validator.validar_arbol.return_value = {
            'valido': True, 'errores': [], 'advertencias': []}

        # Mock connection and repository
        mock_conn = Mock()
        mock_conn.connect.return_value = True
        mock_conn_class.return_value = mock_conn

        mock_repo = Mock()
        mock_repo.verificar_arbol_existente.return_value = {'existe': False}
        mock_repo.save_solo_estructura_arbol.return_value = {
            'total_nodos': 2,
            'nodos_raiz': 1,
            'niveles_maximos': 2,
            'importe_total': 1000.0
        }
        mock_repo.calcular_estadisticas_arbol.return_value = {
            'total_nodos': 2,
            'nodos_raiz': 1,
            'nivel_maximo': 1,
            'total_mediciones': 5,
            'importe_total': 1000.0
        }
        mock_repo_class.return_value = mock_repo

        resultado = service.importar_solo_arbol(
            temp_bc3_file,
            "test_project",
            exportar_arbol_json=False,
            validar_arbol=True,
            sobrescribir=True
        )

        assert resultado is True
        service.parser.parse_file.assert_called_once()
        mock_repo.save_solo_estructura_arbol.assert_called_once()

    def test_listar_arboles_disponibles_vacio(self, service):
        """Test listar árboles cuando no hay ninguno"""
        with (patch('src.services.upload_service.MongoDBConnection')
              as mock_conn_class):
            mock_conn = Mock()
            mock_collection = Mock()
            mock_collection.find.return_value.sort.return_value = []
            mock_conn.get_collection.return_value = mock_collection
            mock_conn_class.return_value.__enter__.return_value = mock_conn

            resultado = service.listar_arboles_disponibles()

            assert resultado == []

    def test_eliminar_arbol_success(self, service):
        """Test eliminación exitosa de árbol"""
        with (patch('src.services.upload_service.MongoDBConnection')
              as mock_conn_class):
            with (patch('src.services.upload_service.BC3ArbolRepository')
                  as mock_repo_class):
                mock_conn = Mock()
                mock_conn_class.return_value.__enter__.return_value = mock_conn

                mock_repo = Mock()
                mock_repo.eliminar_arbol.return_value = True
                mock_repo_class.return_value = mock_repo

                resultado = service.eliminar_arbol("test_project")

                assert resultado is True
                mock_repo.eliminar_arbol.assert_called_with("test_project")

    def test_obtener_estadisticas_archivo(self, service, temp_bc3_file):
        """Test obtención de estadísticas de archivo"""
        # Mock parser and constructor
        service.parser.parse_file = Mock(return_value={
            'conceptos': [Mock()],
            'descomposiciones': [Mock()],
            'mediciones': [Mock()],
            'textos': [Mock()]
        })

        mock_arbol = Mock()
        service.arbol_constructor.construir_arbol = Mock(
            return_value=mock_arbol)
        service.arbol_constructor.obtener_estadisticas_construccion = Mock(
            return_value={'total_nodos': 5})

        with patch('src.services.upload_service.BC3Helpers') as mock_helpers:
            with (patch('src.services.upload_service.ArbolValidator')
                  as mock_validator):
                mock_helpers.calcular_estadisticas.return_value = {
                    'total_conceptos': 5}
                mock_validator.validar_arbol.return_value = {'valido': True}

                resultado = service.obtener_estadisticas_archivo(temp_bc3_file)

                assert 'archivo' in resultado
                assert 'parseo' in resultado
                assert 'arbol' in resultado
                assert 'validacion' in resultado
