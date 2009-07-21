# -*- coding: utf-8 -*-

"""
Module implementing AboutWiiSigner.
"""
from PyQt4.QtGui import QDialog
from PyQt4.QtCore import pyqtSignature

from Ui_AboutWiiSigner import Ui_Dialog

class AboutWiiSigner(QDialog, Ui_Dialog):
    """
    Show WiiBrew's page about Wii Signer, as it's the only documentation i've found about it.
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
