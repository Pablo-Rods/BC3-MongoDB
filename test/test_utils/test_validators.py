from decimal import Decimal
from src.utils.validators import BC3Validator


class TestBC3Validator:
    """Tests para BC3Validator"""

    def test_validar_codigo_valido(self):
        """Test validación de código válido"""
        assert BC3Validator.validar_codigo("CAP01") is True
        assert BC3Validator.validar_codigo("PART_123") is True

    def test_validar_codigo_invalido(self):
        """Test validación de código inválido"""
        assert BC3Validator.validar_codigo("") is False
        assert BC3Validator.validar_codigo(None) is False
        assert BC3Validator.validar_codigo("   ") is False
        assert BC3Validator.validar_codigo("X" * 25) is False  # Muy largo

    def test_validar_precio_valido(self):
        """Test validación de precio válido"""
        assert BC3Validator.validar_precio(None) is True  # Opcional
        assert BC3Validator.validar_precio(Decimal("100.50")) is True
        assert BC3Validator.validar_precio("50.25") is True
        assert BC3Validator.validar_precio(0) is True

    def test_validar_precio_invalido(self):
        """Test validación de precio inválido"""
        assert BC3Validator.validar_precio(Decimal("-10.00")) is False
        assert BC3Validator.validar_precio("abc") is False

    def test_validar_unidad_valida(self):
        """Test validación de unidad válida"""
        assert BC3Validator.validar_unidad(None) is True  # Opcional
        assert BC3Validator.validar_unidad("") is True    # Opcional
        assert BC3Validator.validar_unidad("m2") is True
        assert BC3Validator.validar_unidad("kg") is True
        assert BC3Validator.validar_unidad("UD") is True  # Case insensitive

    def test_validar_unidad_invalida(self):
        """Test validación de unidad inválida"""
        assert BC3Validator.validar_unidad("xyz") is False

    def test_validar_tipo_concepto_valido(self):
        """Test validación de tipo de concepto válido"""
        assert BC3Validator.validar_tipo_concepto(None) is True  # Opcional
        assert BC3Validator.validar_tipo_concepto("") is True    # Opcional
        assert BC3Validator.validar_tipo_concepto("0") is True
        assert BC3Validator.validar_tipo_concepto("5") is True

    def test_validar_tipo_concepto_invalido(self):
        """Test validación de tipo de concepto inválido"""
        assert BC3Validator.validar_tipo_concepto("6") is False
        assert BC3Validator.validar_tipo_concepto("-1") is False
        assert BC3Validator.validar_tipo_concepto("abc") is False
