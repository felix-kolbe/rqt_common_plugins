import os
from QtBindingHelper import loadUi
from QtCore import qDebug, QEvent, QObject, Qt, Slot
from QtGui import QDockWidget, QIcon, QWidget


class DockWidgetTitleBar(QWidget):

    def __init__(self, dock_widget, hide_close_button=False):
        super(DockWidgetTitleBar, self).__init__(dock_widget)
        self.hide_close_button = hide_close_button

        ui_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'DockWidgetTitleBar.ui')
        loadUi(ui_file, self)
        self.extra_buttons = {
            'settings': self.settings_button,
            'reload': self.reload_button,
            'help': self.help_button,
        }

        self.settings_button.setIcon(QIcon.fromTheme('emblem-system'))
        self.settings_button.setText("")
        self.reload_button.setIcon(QIcon.fromTheme('view-refresh'))
        self.reload_button.setText("")
        self.help_button.setIcon(QIcon.fromTheme('help-browser'))
        self.help_button.setText("")

        self.close_button.setIcon(QIcon.fromTheme('window-close'))
        self.close_button.setText("")

        self.float_button.clicked.connect(self.toggle_floating)
        self.dockable_button.clicked.connect(self.toggle_dockable)
        self.close_button.clicked.connect(dock_widget.close)

        dock_widget.featuresChanged.connect(self.features_changed)
        self.features_changed(0)

        self.update_title()

        self.event_callbacks = {
            QEvent.WindowTitleChange: self.update_title,
        }
        dock_widget.installEventFilter(self)


    def connect_button(self, button_id, callback):
        button = self.extra_buttons.get(button_id, None)
        if button is None:
            qDebug('DockWidgetTitleBar.connect_button(): unknown button_id: %s' % button_id)
            return
        button.clicked.connect(callback)


    def show_button(self, button_id, visibility=True):
        button = self.extra_buttons.get(button_id, None)
        if button is None:
            qDebug('DockWidgetTitleBar.show_button(): unknown button_id: %s' % button_id)
            return
        button.setVisible(visibility)


    def hide_button(self, button_id):
        self.show_button(button_id, False)


    def eventFilter(self, obj, event):
        if event.type() in self.event_callbacks:
            ret_val = self.event_callbacks[event.type()](obj, event)
            if ret_val is not None:
                return ret_val
        return QObject.eventFilter(self, obj, event)


    def update_title(self, *args):
        self.title_label.setText(self.parentWidget().windowTitle())


    @Slot(bool)
    def toggle_dockable(self, enabled):
        dock_widget = self.parentWidget()
        if enabled:
            dock_widget.setAllowedAreas(Qt.AllDockWidgetAreas)
        else:
            dock_widget.setAllowedAreas(Qt.NoDockWidgetArea)
            dock_widget.setFloating(True)


    @Slot()
    def toggle_floating(self):
        dock_widget = self.parentWidget()
        floating = not dock_widget.isFloating()
        dock_widget.setFloating(floating)
        # if widget was docked, make sure the dockable button's state reflects this
        if not floating:
            self.dockable_button.setChecked(True)
            self.toggle_dockable(True)


    def features_changed(self, _features):
        features = self.parentWidget().features()
        self.close_button.setVisible((not self.hide_close_button) and bool(features & QDockWidget.DockWidgetClosable))
        self.float_button.setVisible(bool(features & QDockWidget.DockWidgetFloatable))


if __name__ == '__main__':
    import sys
    from QtCore import Qt
    from QtGui import QApplication, QMainWindow, QDockWidget

    app = QApplication(sys.argv)

    win = QMainWindow()

    dock1 = QDockWidget('dockwidget1', win)
    win.addDockWidget(Qt.LeftDockWidgetArea, dock1)
    title_bar = DockWidgetTitleBar(dock1)
    dock1.setTitleBarWidget(title_bar)

    dock2 = QDockWidget('dockwidget2')
    win.addDockWidget(Qt.RightDockWidgetArea, dock2)
    title_bar = DockWidgetTitleBar(dock2)
    dock2.setTitleBarWidget(title_bar)

    win.resize(640, 480)
    win.show()

    app.exec_()
