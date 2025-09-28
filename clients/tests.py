# clients/tests.py

from django.test import TestCase
from .utils import (
    EmptyPhoneStrategy,
    StartsPlusStrategy,
    NotNumericStrategy,
    SpecialCharsStrategy,
    InternacionalNumberStrategy,
    TooLongStrategy,
    MoreThanOneNumbers,
    ValidPhoneStrategy,
    TooShortStrategy,
    FallbackStrategy,
    get_strategy_and_correction,
    get_area_code_for_number,
    split_and_clean_phones,
    create_results_corrected,
)

class PhoneStrategyTests(TestCase):

    # --- Estrategias individuales ---

    def test_empty_phone_strategy(self):
        strategy = EmptyPhoneStrategy()
        self.assertTrue(strategy.applies("", ""))
        self.assertEqual(strategy.correct("", ""), [("Ingrese un número válido.", "", "")])

    def test_valid_phone_strategy(self):
        strategy = ValidPhoneStrategy()
        phone = "3012345678"
        self.assertTrue(strategy.applies(phone, "57"))
        result = strategy.correct(phone, "57")
        self.assertEqual(result[0][1], "57")
        self.assertEqual(result[0][2], "3012345678")

    def test_starts_plus_strategy(self):
        strategy = StartsPlusStrategy()
        phone = "+573012345678"
        self.assertTrue(strategy.applies(phone, ""))
        result = strategy.correct(phone, "")
        self.assertIn("Quite el símbolo", result[0][0])

    def test_not_numeric_strategy(self):
        strategy = NotNumericStrategy()
        phone = "abc123"
        self.assertTrue(strategy.applies(phone, ""))
        result = strategy.correct(phone, "")
        self.assertEqual(result, [("No es numérico, se deja vacío.", "", "")])

    def test_special_chars_strategy(self):
        strategy = SpecialCharsStrategy()
        phone = "301-234-5678"
        self.assertTrue(strategy.applies(phone, ""))
        result = strategy.correct(phone, "")
        self.assertIn("Elimine caracteres", result[0][0])

    def test_internacional_number_strategy_valid(self):
        strategy = InternacionalNumberStrategy()
        phone = "+573012345678"
        self.assertTrue(strategy.applies(phone, ""))
        result = strategy.correct(phone, "")
        self.assertEqual(result[0][1], "57")
        self.assertEqual(result[0][2], "3012345678")

    def test_internacional_number_strategy_invalid(self):
        strategy = InternacionalNumberStrategy()
        phone = "+999123"
        self.assertFalse(strategy.applies(phone, ""))

    def test_too_long_strategy(self):
        strategy = TooLongStrategy()
        phone = "571234567890"
        self.assertTrue(strategy.applies(phone, ""))
        result = strategy.correct(phone, "")
        self.assertIn("Recortado", result[0][0])

    def test_more_than_one_numbers(self):
        strategy = MoreThanOneNumbers()
        phone = "3012345678;3023456789"
        self.assertTrue(strategy.applies(phone, ""))
        result = strategy.correct(phone, "")
        self.assertEqual(len(result), 2)
        for r in result:
            self.assertIn("Número separado", r[0])

    def test_too_short_strategy(self):
        strategy = TooShortStrategy()
        phone = "12345"
        self.assertTrue(strategy.applies(phone, ""))
        result = strategy.correct(phone, "")
        self.assertIn("Menos de 10 dígitos", result[0][0])

    def test_fallback_strategy(self):
        strategy = FallbackStrategy()
        self.assertTrue(strategy.applies("algo", ""))
        self.assertEqual(strategy.correct("algo", "57"), [("Revise el número.", "57", "")])

    # --- Funciones auxiliares ---

    def test_get_area_code_for_number(self):
        self.assertEqual(get_area_code_for_number("3012345678"), "57")
        self.assertEqual(get_area_code_for_number("571234567890"), "57")
        self.assertEqual(get_area_code_for_number(""), "")

    def test_split_and_clean_phones(self):
        raw = "3012345678; 3023456789 | 3034567890"
        n1, n2, n3 = split_and_clean_phones(raw)
        self.assertEqual(n1, "3012345678")
        self.assertEqual(n2, "3023456789")
        self.assertEqual(n3, "3034567890")

    def test_create_results_corrected(self):
        phone = "3012345678"
        result = create_results_corrected(phone)
        self.assertIn("Número válido", result[0])

    # --- Flujo completo ---

    def test_get_strategy_and_correction_flow(self):
        test_cases = [
            ("", "Ingrese un número válido."),
            ("3012345678", "Número válido"),
            ("+573012345678", "Quite el símbolo"),
            ("abc123", "No es numérico"),
            ("301-234-5678", "Elimine caracteres"),
            ("571234567890", "Recortado"),
            ("12345", "Menos de 10 dígitos"),
        ]
        for phone, expected in test_cases:
            result = get_strategy_and_correction(phone, "")
            self.assertIn(expected, result[0][0])