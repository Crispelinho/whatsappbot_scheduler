# notifications_scheduler/tests.py
from django.test import TestCase
import constants.xpaths as xpaths

class TestXPaths(TestCase):

    def test_build_xpath_button_single_label(self):
        xpath = xpaths.build_xpath_button(["Adjuntar"])
        self.assertIn("//div[@role='button'", xpath)
        self.assertIn("contains(@aria-label, 'Adjuntar')", xpath)

    def test_build_xpath_button_multiple_labels(self):
        labels = ["Enviar", "Send", "Envoyer"]
        xpath = xpaths.build_xpath_button(labels)
        for lbl in labels:
            self.assertIn(f"contains(@aria-label, '{lbl}')", xpath)
        self.assertIn(" or ", xpath)

    def test_attach_button_constant(self):
        """Verifica que ATTACH_BUTTON use los labels definidos"""
        for lbl in xpaths.ATTACH_LABELS:
            self.assertIn(lbl, xpaths.ATTACH_BUTTON)

    def test_send_button_constant(self):
        """Verifica que SEND_BUTTON use los labels definidos"""
        for lbl in xpaths.SEND_LABELS:
            self.assertIn(lbl, xpaths.SEND_BUTTON)
