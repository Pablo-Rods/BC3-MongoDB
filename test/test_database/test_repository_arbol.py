import pytest
from unittest.mock import Mock
from datetime import datetime
from src.database.repository_arbol import BC3ArbolRepository
from src.database.connection import MongoDBConnection


class TestBC3ArbolRepository:
    """Tests para BC3ArbolRepository"""

    @pytest.fixture
    def mock_connection(self):
        mock_conn = Mock(spec=MongoDBConnection)
        mock_conn._is_connected.return_value = True
        return mock_conn

    @pytest.fixture
    def repository(self, mock_connection):
        return BC3ArbolRepository(mock_connection)

    def test_save_arbol_completo_success(
        self,
        repository,
        arbol_simple,
        mock_connection
    ):
        """Test guardado exitoso de árbol completo"""
        # Mock collections
        mock_arbol_collection = Mock()
        mock_nodos_collection = Mock()

        def get_collection_side_effect(name):
            if name == "arbol_conceptos":
                return mock_arbol_collection
            elif name == "nodos_arbol":
                return mock_nodos_collection
            return Mock()

        mock_connection.get_collection.side_effect = get_collection_side_effect

        # Mock successful operations
        mock_arbol_collection.update_one.return_value = Mock(
            upserted_id="test_id", modified_count=0)
        mock_nodos_collection.update_one.return_value = Mock(
            upserted_id="node_id", modified_count=0)
        mock_nodos_collection.create_index.return_value = None
        mock_arbol_collection.create_index.return_value = None

        resultado = repository.save_arbol_completo(arbol_simple)

        assert resultado['arbol_guardado'] is True
        assert resultado['nodos_guardados'] == 2  # Dos nodos en arbol_simple
        assert resultado['total_nodos'] == 2

    def test_save_arbol_completo_no_connection(self, repository, arbol_simple):
        """Test guardado sin conexión"""
        repository.connection._is_connected.return_value = False

        resultado = repository.save_arbol_completo(arbol_simple)

        assert 'error' in resultado
        assert resultado['error'] == 'No hay conexión'

    def test_obtener_arbol_completo(self, repository, mock_connection):
        """Test obtención de árbol completo"""
        mock_collection = Mock()
        mock_connection.get_collection.return_value = mock_collection

        expected_arbol = {
            'archivo_origen': 'test.bc3',
            'metadata': {'total_nodos': 5},
            'estructura_json': {}
        }
        mock_collection.find_one.return_value = expected_arbol

        resultado = repository.obtener_arbol_completo("test.bc3")

        assert resultado == expected_arbol
        mock_collection.find_one.assert_called_with(
            {'tipo': 'estructura_completa', 'archivo_origen': 'test.bc3'},
            sort=[('fecha_creacion', -1)]
        )

    def test_obtener_nodo(self, repository, mock_connection):
        """Test obtención de nodo específico"""
        mock_collection = Mock()
        mock_connection.get_collection.return_value = mock_collection

        expected_nodo = {
            'codigo': 'CAP01',
            'archivo_origen': 'test.bc3',
            'concepto': {'codigo': 'CAP01', 'resumen': 'Test'}
        }
        mock_collection.find_one.return_value = expected_nodo

        resultado = repository.obtener_nodo("CAP01", "test.bc3")

        assert resultado == expected_nodo
        mock_collection.find_one.assert_called_with({
            'codigo': 'CAP01',
            'archivo_origen': 'test.bc3'
        })

    def test_obtener_hijos_directos(self, repository, mock_connection):
        """Test obtención de hijos directos"""
        mock_collection = Mock()
        mock_connection.get_collection.return_value = mock_collection

        expected_hijos = [
            {'codigo': 'HIJO1', 'estructura': {'codigo_padre': 'PADRE'}},
            {'codigo': 'HIJO2', 'estructura': {'codigo_padre': 'PADRE'}}
        ]
        mock_cursor = Mock()
        mock_cursor.sort.return_value = expected_hijos
        mock_collection.find.return_value = mock_cursor

        resultado = repository.obtener_hijos_directos("PADRE", "test.bc3")

        assert resultado == expected_hijos
        mock_collection.find.assert_called_with({
            'estructura.codigo_padre': 'PADRE',
            'archivo_origen': 'test.bc3'
        })

    def test_obtener_nodos_raiz(self, repository, mock_connection):
        """Test obtención de nodos raíz"""
        mock_collection = Mock()
        mock_connection.get_collection.return_value = mock_collection

        expected_raices = [
            {'codigo': 'RAIZ1', 'estructura': {'es_raiz': True}},
            {'codigo': 'RAIZ2', 'estructura': {'es_raiz': True}}
        ]
        mock_cursor = Mock()
        mock_cursor.sort.return_value = expected_raices
        mock_collection.find.return_value = mock_cursor

        resultado = repository.obtener_nodos_raiz("test.bc3")

        assert resultado == expected_raices
        mock_collection.find.assert_called_with({
            'estructura.es_raiz': True,
            'archivo_origen': 'test.bc3'
        })

    def test_verificar_estructura_existente_existe(
        self,
        repository,
        mock_connection
    ):
        """Test verificación de estructura existente - existe"""
        mock_collection = Mock()
        mock_connection.get_collection.return_value = mock_collection

        estructura_existente = {
            'archivo_origen': 'test.bc3',
            'fecha_creacion': datetime.now(),
            'metadata': {
                'total_nodos': 150,
                'niveles_maximos': 4,
                'nodos_raiz': ['CAP01']
            }
        }
        mock_collection.find_one.return_value = estructura_existente

        resultado = repository.verificar_estructura_existente("test.bc3")

        assert resultado['existe'] is True
        assert resultado['total_nodos'] == 150

    def test_verificar_estructura_existente_no_existe(
        self,
        repository,
        mock_connection
    ):
        """Test verificación de estructura existente - no existe"""
        mock_collection = Mock()
        mock_connection.get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = None

        resultado = repository.verificar_estructura_existente("test.bc3")

        assert resultado['existe'] is False

    def test_eliminar_estructura_arbol(self, repository, mock_connection):
        """Test eliminación de estructura de árbol"""
        mock_collection = Mock()
        mock_connection.get_collection.return_value = mock_collection
        mock_collection.delete_many.return_value = Mock(deleted_count=1)

        resultado = repository.eliminar_estructura_arbol("test.bc3")

        assert resultado is True
        mock_collection.delete_many.assert_called_with(
            {'archivo_origen': 'test.bc3'})

    def test_calcular_estadisticas_arbol(self, repository, mock_connection):
        """Test cálculo de estadísticas del árbol"""
        mock_collection = Mock()
        mock_connection.get_collection.return_value = mock_collection

        expected_stats = {
            'total_nodos': 150,
            'nodos_raiz': 3,
            'nodos_hoja': 80,
            'total_mediciones': 200,
            'nivel_maximo': 4
        }
        mock_collection.aggregate.return_value = [expected_stats]

        resultado = repository.calcular_estadisticas_arbol("test.bc3")

        assert resultado['total_nodos'] == 150
        assert resultado['nodos_raiz'] == 3
