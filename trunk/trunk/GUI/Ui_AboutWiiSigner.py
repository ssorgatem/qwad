# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/ssorgatem/Documents/python/Qwad/GUI/AboutWiiSigner.ui'
#
# Created: Mon Jul 20 14:25:52 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setEnabled(True)
        Dialog.resize(584, 467)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/wad.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.AboutWiiSigner = QtWebKit.QWebView(Dialog)
        self.AboutWiiSigner.setGeometry(QtCore.QRect(10, 0, 571, 461))
        self.AboutWiiSigner.setUrl(QtCore.QUrl("http://wiibrew.org/wiki/Wii_Signer"))
        self.AboutWiiSigner.setObjectName("AboutWiiSigner")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "About Wii Signer", None, QtGui.QApplication.UnicodeUTF8))

from PyQt4 import QtWebKit
import Qwad_rc

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    Dialog = QtGui.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

