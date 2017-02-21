#!/usr/bin/env python3

import json
import os
import subprocess
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QTreeView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem


class ObjConverter(QStandardItemModel):
    def __init__(self, obj, name='', *args, **kwargs):
        super(ObjConverter, self).__init__(*args, **kwargs)
        self.invisibleRootItem().appendRows(self.convert(obj))
        self.setHorizontalHeaderItem(0, QStandardItem(name))

    def pack(self, item):
        if item.rowCount() == 1 and item.child(0).rowCount() == 0:
            item.setText('%s: %s' % (item.text(), item.child(0).text()))
            #item.parent().setChild(item.row(), 1, QStandardItem(item.child(0).text()))
            item.removeRow(0)

    def convert(self, obj):
        if isinstance(obj, list):
            ret = []
            for n, sub in enumerate(obj):
                item = QStandardItem(str(n))
                item.appendRows(self.convert(sub))
                self.pack(item)
                ret.append(item)
            return ret
        elif isinstance(obj, dict):
            ret = []
            for k in sorted(obj):
                item = QStandardItem(k)
                item.appendRows(self.convert(obj[k]))
                self.pack(item)
                ret.append(item)
            return ret
        return [QStandardItem(repr(obj))]


def loadCommand():
    if os.path.isfile(le.text()):
        with open(le.text()) as fd:
            obj = json.load(fd)
    else:
        try:
            out = subprocess.check_output(le.text(), shell=True).decode('utf-8')
        except subprocess.CalledProcessError as e:
            obj = str(e)
        else:
            try:
                obj = json.loads(out)
            except ValueError as e:
                try:
                    obj = json.loads('[%s]' % ','.join(out.strip().split('\n')))
                except ValueError:
                    obj = str(e)

    tv.setModel(ObjConverter(obj, name=le.text()))
    tv.expandAll()


class View(QTreeView):
    def setRecursive(self, idx, b):
        self.setExpanded(idx, b)
        for i in range(self.model().rowCount(idx)):
            self.setRecursive(self.model().index(i, 0, idx), b)

    def mouseDoubleClickEvent(self, ev):
        if ev.button() & Qt.RightButton:
            idx = self.indexAt(ev.pos())
            if not idx.isValid():
                return

            self.setRecursive(idx, not self.isExpanded(idx))
        else:
            super(View, self).mouseDoubleClickEvent(ev)


if __name__ == '__main__':
    old_hook = sys.excepthook
    sys.excepthook = lambda *args, **kwargs: old_hook(*args, **kwargs)

    app = QApplication(sys.argv)

    win = QMainWindow()
    lay = QVBoxLayout()
    cont = QWidget()
    win.setCentralWidget(cont)
    cont.setLayout(lay)

    le = QLineEdit()
    lay.addWidget(le)

    le.returnPressed.connect(loadCommand)

    tv = View()
    lay.addWidget(tv)

    args = app.arguments()[1:]
    if args:
        if args[0] == '-':
            obj = json.loads(sys.stdin.read())
        else:
            with open(args[0]) as fd:
                obj = json.load(fd)
            le.setText(args[0])

        tv.setModel(ObjConverter(obj, name=args[0]))

    win.show()
    app.exec_()
