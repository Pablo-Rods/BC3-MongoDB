import pytest
from unittest.mock import Mock, patch
from src.services.get_service import GetService


class TestGetService:
    """Tests para GetService"""

    @pytest.fixture
    def service(self):
        return GetService()

    def test_get_by_project_exists(self, service):
        """Test obtener proyecto existente"""
        expected_result = {
            'archivo_origen': 'test_project',
            'metadata': {'total_nodos': 100}
        }

        with (patch('src.services.get_service.MongoDBConnection')
              as mock_conn_class):
            mock_conn = Mock()
            mock_collection = Mock()
            mock_collection.find_one.return_value = expected_result
            mock_conn.get_collection.return_value = mock_collection
            mock_conn_class.return_value.__enter__.return_value = mock_conn

            resultado = service.get_by_project("test_project")

            assert resultado == expected_result
            mock_collection.find_one.assert_called_with({
                "archivo_origen": "test_project"
            })

    def test_get_by_project_not_exists(self, service):
        """Test obtener proyecto inexistente"""
        with (patch('src.services.get_service.MongoDBConnection')
              as mock_conn_class):
            mock_conn = Mock()
            mock_collection = Mock()
            mock_collection.find_one.return_value = None
            mock_conn.get_collection.return_value = mock_collection
            mock_conn_class.return_value.__enter__.return_value = mock_conn

            resultado = service.get_by_project("nonexistent_project")

            assert resultado is None

    def test_get_by_project_connection_error(self, service):
        """Test error de conexión"""
        with (patch('src.services.get_service.MongoDBConnection')
              as mock_conn_class):
            mock_conn = Mock()
            mock_conn.get_collection.return_value = None  # Error de conexión
            mock_conn_class.return_value.__enter__.return_value = mock_conn

            resultado = service.get_by_project("test_project")

            assert resultado is None
