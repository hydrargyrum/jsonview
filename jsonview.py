#!/usr/bin/env python3

from collections import OrderedDict
import json
import os
import subprocess
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QTreeView, QTableView
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

    def setObj(self, obj):
        self.clear()
        self.invisibleRootItem().appendRows(self.convert(obj))

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


class ObjTable(QStandardItemModel):
    def __init__(self, obj, *args, **kwargs):
        super(ObjTable, self).__init__(*args, **kwargs)
        self.setObj(obj)

    def _makeItem(self, item):
        return QStandardItem(repr(item))

    def setObj(self, ls):
        keys = list(OrderedDict((k, 0) for obj in ls for k in obj.keys()))
        for n, k in enumerate(keys):
            self.setHorizontalHeaderItem(n, QStandardItem(k))
        for obj in ls:
            self.appendRow([self._makeItem(obj.get(k)) for k in keys])


class TreeView(QTreeView):
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
            super(TreeView, self).mouseDoubleClickEvent(ev)


def loadJson(txt):
    return json.loads(txt, object_hook=OrderedDict)


class Win(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(Win, self).__init__(*args, **kwargs)

        cont = QWidget()
        self.setCentralWidget(cont)

        self.lay = QVBoxLayout()
        cont.setLayout(self.lay)

        self.le = QLineEdit()
        self.lay.addWidget(self.le)

        self.le.returnPressed.connect(self.loadCommand)

        self.tree = TreeView()
        self.table = QTableView()

        self.name = ''
        self.data = None
        self.lay.addWidget(self.tree)

        menu = self.menuBar().addMenu('Options')
        self.isTable = menu.addAction('Table')
        self.isTable.setCheckable(True)
        self.isTable.setShortcut('Alt+T')
        self.isTable.changed.connect(self.reloadModel)

    def clearModels(self):
        self.tree.setModel(None)
        self.table.setModel(None)

    def reloadModel(self):
        table = self.isTable.isChecked()

        if table:
            table = isinstance(self.data, list) and all(isinstance(obj, dict) for obj in self.data)

        self.clearModels()
        if table:
            self.table.setModel(ObjTable(self.data))
            self.table.resizeColumnsToContents()
            self.table.setSortingEnabled(True)
            self.lay.replaceWidget(self.tree, self.table)
        else:
            self.tree.setModel(ObjConverter(self.data, name=self.name))
            self.tree.expandAll()
            self.lay.replaceWidget(self.table, self.tree)

        self.table.setVisible(table)
        self.tree.setVisible(not table)

    def loadCommand(self):
        text = self.le.text()
        if os.path.isfile(text):
            with open(text) as fd:
                obj = loadJson(fd.read())
        else:
            try:
                out = subprocess.check_output(text, shell=True).decode('utf-8')
            except subprocess.CalledProcessError as e:
                obj = str(e)
            else:
                try:
                    obj = loadJson(out)
                except ValueError as e:
                    try:
                        obj = loadJson('[%s]' % ','.join(out.strip().split('\n')))
                    except ValueError:
                        obj = str(e)

        self.setData(obj, text)

    def setFile(self, f):
        self.le.setText(f)

    def setData(self, obj, name=''):
        self.data = obj
        self.name = name
        self.reloadModel()


if __name__ == '__main__':
    old_hook = sys.excepthook
    sys.excepthook = lambda *args, **kwargs: old_hook(*args, **kwargs)

    app = QApplication(sys.argv)

    win = Win()

    args = app.arguments()[1:]
    if args:
        if args[0] == '-':
            obj = loadJson(sys.stdin.read())
        else:
            with open(args[0]) as fd:
                obj = loadJson(fd.read())
            win.setFile(args[0])

        win.setData(obj, name=args[0])

    win.show()
    app.exec_()
