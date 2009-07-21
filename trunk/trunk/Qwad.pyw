#!/usr/bin/env python
#-*- coding: utf-8 -*-
import sys
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QTranslator, QString, QLocale
from GUI.VenPri import MWQwad

if __name__ == "__main__":
    translator = QTranslator()
    translator.load(QString("i18n/Qwad_%1").arg(QLocale.system().name()))
    qttranslator = QTranslator()
    qttranslator.load(QString("qt_%1").arg(QLocale.system().name()))
    Vapp = QApplication(sys.argv)
    Vapp.installTranslator(translator)
    Vapp.installTranslator(qttranslator)
    VentanaP = MWQwad()
    VentanaP.show()
    sys.exit(Vapp.exec_())
#TODO: NT Port
