# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'updateUi.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(590, 547)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        Dialog.setFont(font)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.btn_report = QtWidgets.QPushButton(Dialog)
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(30)
        self.btn_report.setFont(font)
        self.btn_report.setObjectName("btn_report")
        self.verticalLayout.addWidget(self.btn_report)
        self.progressBar = QtWidgets.QProgressBar(Dialog)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.verticalLayout.addWidget(self.progressBar)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btn_start_update = QtWidgets.QPushButton(Dialog)
        self.btn_start_update.setObjectName("btn_start_update")
        self.horizontalLayout.addWidget(self.btn_start_update)
        self.btn_cancle = QtWidgets.QPushButton(Dialog)
        self.btn_cancle.setObjectName("btn_cancle")
        self.horizontalLayout.addWidget(self.btn_cancle)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.btn_report.setText(_translate("Dialog", "更新程序"))
        self.btn_start_update.setText(_translate("Dialog", "开始更新"))
        self.btn_cancle.setText(_translate("Dialog", "取消更新"))
