from unittest.mock import Mock, patch
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from src.database.connection import MongoDBConnection


class TestMongoDBConnection:
    """Tests para MongoDBConnection"""

    @patch('src.database.connection.MongoClient')
    def test_connect_success(self, mock_client):
        """Test conexión exitosa"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {'ok': 1}

        conn = MongoDBConnection("mongodb://localhost:27017", "test_db")
        result = conn.connect()

        assert result is True
        assert conn._connected is True

    @patch('src.database.connection.MongoClient')
    def test_connect_failure(self, mock_client):
        """Test fallo de conexión"""
        mock_client.side_effect = ConnectionFailure("Connection failed")

        conn = MongoDBConnection("mongodb://localhost:27017", "test_db")
        result = conn.connect()

        assert result is False
        assert conn._connected is False

    @patch('src.database.connection.MongoClient')
    def test_connect_timeout(self, mock_client):
        """Test timeout de conexión"""
        mock_client.side_effect = ServerSelectionTimeoutError("Timeout")

        conn = MongoDBConnection("mongodb://localhost:27017", "test_db")
        result = conn.connect()

        assert result is False
        assert conn._connected is False

    def test_get_collection_without_connection(self):
        """Test obtener colección sin conexión"""
        conn = MongoDBConnection("mongodb://localhost:27017", "test_db")

        collection = conn.get_collection("test_collection")

        assert collection is None

    @patch('src.database.connection.MongoClient')
    def test_get_collection_with_connection(self, mock_client):
        """Test obtener colección con conexión"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {'ok': 1}

        mock_database = Mock()
        mock_client_instance.__getitem__.return_value = mock_database

        conn = MongoDBConnection("mongodb://localhost:27017", "test_db")
        conn.connect()

        collection = conn.get_collection("test_collection")

        assert collection is not None
        mock_database.__getitem__.assert_called_with("test_collection")

    @patch('src.database.connection.MongoClient')
    def test_context_manager(self, mock_client):
        """Test uso como context manager"""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.admin.command.return_value = {'ok': 1}

        with MongoDBConnection("mongodb://localhost:27017", "test_db") as conn:
            assert conn._connected is True

        mock_client_instance.close.assert_called_once()

    def test_disconnect(self):
        """Test desconexión"""
        conn = MongoDBConnection("mongodb://localhost:27017", "test_db")
        conn.client = Mock()
        conn._connected = True

        conn.disconnect()

        assert conn._connected is False
        conn.client.close.assert_called_once()
