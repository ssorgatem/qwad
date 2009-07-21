# -*- coding: utf-8 -*-

"""
Module implementing MWQwad.
"""
from wii_signer import wiiw
from PyQt4.QtGui import QMainWindow,QFileDialog,QMessageBox
from PyQt4.QtCore import pyqtSignature,QString
import os

from Ui_VenPri import Ui_Qwad

class MWQwad(QMainWindow, Ui_Qwad):
    """
    Class documentation goes here.
    """
    def __init__(self, parent = None):
        """
        Constructor
        """
        QMainWindow.__init__(self, parent)
        self.setupUi(self)

    def ErrorDiag(self):
                    QMessageBox.critical(None,
                self.trUtf8("Error"),
                self.trUtf8("""An error has ocurred. Probably missing arguments.
Please, see the output of stderr for more help (run Qwad from command line)"""),
                QMessageBox.StandardButtons(\
                    QMessageBox.Ok),
                QMessageBox.Ok)

    @pyqtSignature("")
    def on_BotonRutaWad_clicked(self):
        """
        Get path to WAD file
        """
        WadPath = QFileDialog.getOpenFileName(\
            None,
            self.trUtf8("Selecciona el archivo WAD"),
            QString(),
            self.trUtf8("*.wad; *.WAD"),
            None)
        if WadPath != "" :
            self.MuestraRutaWad.setText(WadPath)

    @pyqtSignature("")
    def on_BotonRutaExtraer_clicked(self):
        """
        WAD contents output path
        """
        OutputDir = QFileDialog.getExistingDirectory(\
            None,
            self.trUtf8("Selecciona dónde guardar el contenido del WAD"),
            QString(),
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
        if OutputDir != "":
            self.MuestraRutaExtraer.setText(OutputDir)

    @pyqtSignature("")
    def on_Desempaqueta_clicked(self):
        """
        Unpack wad
        """
        OLDDIR = os.getcwd()
        try:
            if self.MuestraRutaExtraer.text() != "":
                os.chdir(str(self.MuestraRutaExtraer.text()))
            wiiw.extract(self.MuestraRutaWad.text())
            if os.getcwd() != OLDDIR:
                os.chdir(OLDDIR)
        except Exception, e:
            self.ErrorDiag()
            print e

    @pyqtSignature("")
    def on_BotonRutaEmpaquetado_clicked(self):
        """
        Select where to save the newly created WAD
        """
        NewWadPath = QFileDialog.getSaveFileName(\
            None,
            self.trUtf8("Selecciona dónde guardar el nuevo WAD"),
            QString("output.wad"),
            self.trUtf8("*.wad; *.WAD"),
            None)
        if NewWadPath != "":
            self.MuestraRutaEmpaquetado.setText(NewWadPath)

    @pyqtSignature("")
    def on_BotonRutaDesempaquetado_clicked(self):
        """
        Get path off folder to pack.
        """
        Dir2Wad = QFileDialog.getExistingDirectory(\
            None,
            self.trUtf8("Selecciona el directorio a partir del cual crear un WAD"),
            QString(),
            QFileDialog.Options(QFileDialog.ShowDirsOnly))
        if Dir2Wad != "":
            self.MuestraRutaDesempaquetado.setText(Dir2Wad)

    @pyqtSignature("")
    def on_Empaqueta_clicked(self):
        """
        Create WAD
        """
        try:
            if self.updateTMD.checkState() == 2:
                print "updating TMD"
                wiiw.update(str(self.MuestraRutaDesempaquetado.text()))
            else:
                print "not updating TMD"
            wiiw.packdir(str(self.MuestraRutaDesempaquetado.text()),str(self.MuestraRutaEmpaquetado.text()))
        except Exception, e:
            self.ErrorDiag()
            print e

    @pyqtSignature("")
    def on_actionAcerca_de_Qwad_triggered(self):
        """
        About Qwad
        """
        from AboutQwad import AboutQwad
        Pop = AboutQwad()
        Pop.exec_()

    @pyqtSignature("")
    def on_actionAbout_Qt_triggered(self):
        """
        About Qt
        """
        QMessageBox.aboutQt(None,
            self.trUtf8("About Qt"))

    @pyqtSignature("")
    def on_actionAbout_Wii_Signer_triggered(self):
        """
        About Wii Signer
        """
        from AboutWiiSigner import AboutWiiSigner
        Pop = AboutWiiSigner()
        Pop.exec_()
