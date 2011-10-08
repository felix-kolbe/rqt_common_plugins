#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from rosgui.QtBindingHelper import loadUi
from QtCore import Qt, QTimer, Signal, Slot, qDebug
from QtGui import QCompleter, QDockWidget, QStringListModel

import roslib
roslib.load_manifest('rosgui_plot')
import rospy
from rxtools.rosplot import ROSData
from rostopic import get_topic_type
from DataPlot import DataPlot
from TopicCompleter import TopicCompleter

# main class inherits from the ui window class
class Plot(QDockWidget):

    def __init__(self, parent, plugin_context):
        QDockWidget.__init__(self, plugin_context.main_window())
        self.setObjectName('Plot')

        ui_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Plot.ui')
        loadUi(ui_file, self, {'DataPlot': DataPlot})

        self.subscribe_topic_button.setEnabled(False)

        self.topic_completer = TopicCompleter(self.topic_edit)
        self.topic_edit.setCompleter(self.topic_completer)

        self.start_time = rospy.get_time()
        self.rosdata_ = {}

        # setup drag 'n drop
        self.data_plot.dropEvent = self.dropEvent
        self.data_plot.dragEnterEvent = self.dragEnterEvent

        # setup data plot 
        self.data_plot.redrawManually = True
        self.pause_button.clicked[bool].connect(self.data_plot.togglePause)

        # add our self to the main window
        plugin_context.main_window().addDockWidget(Qt.RightDockWidgetArea, self)

        # init and start update timer for plot
        self.timerUpdatePlot = QTimer(self)
        self.timerUpdatePlot.timeout.connect(self.update_plot)
        self.timerUpdatePlot.start(40)


    def update_plot(self):
        for topic_name, rosdata in self.rosdata_.items():
            # TODO: use data_x as time stamp
            data_x, data_y = rosdata.next()
            for value in data_y:
                self.data_plot.updateValue(topic_name, value)
        self.data_plot.redraw()


    def _get_field_type(self, topic_name):
        # get message
        topic_type, _, message_evaluator = get_topic_type(topic_name)
        if topic_type is None:
            return None
        message = roslib.message.get_message_class(topic_type)()

        # return field type
        if message_evaluator:
            try:
                field_type = type(message_evaluator(message))
            except:
                field_type = None
        else:
            field_type = type(message)

        return field_type


    @Slot('QDragEnterEvent*')
    def dragEnterEvent(self, event):
        if not event.mimeData().hasText():
            if not hasattr(event.source(), 'selectedItems') or len(event.source().selectedItems()) == 0:
                qDebug('Plot.dragEnterEvent(): not hasattr(event.source(), selectedItems) or len(event.source().selectedItems()) == 0')
                return
            item = event.source().selectedItems()[0]
            ros_topic_name = item.data(0, Qt.UserRole)
            if ros_topic_name == None:
                qDebug('Plot.dragEnterEvent(): not hasattr(item, ros_topic_name_)')
                return

        # get topic name
        if event.mimeData().hasText():
            topic_name = str(event.mimeData().text())
        else:
            droped_item = event.source().selectedItems()[0]
            topic_name = str(droped_item.data(0, Qt.UserRole))

        # check for numeric field type
        field_type = self._get_field_type(topic_name)
        if field_type in (int, float):
            event.acceptProposedAction()
        else:
            qDebug('Plot.dragEnterEvent(): rejecting topic "%s" of non-numeric type "%s"' % (topic_name, field_type))


    @Slot('QDropEvent*')
    def dropEvent(self, event):
        if event.mimeData().hasText():
            topic_name = str(event.mimeData().text())
        else:
            droped_item = event.source().selectedItems()[0]
            topic_name = str(droped_item.data(0, Qt.UserRole))
        self.add_topic(topic_name)


    @Slot(str)
    def on_topic_edit_textChanged(self, topic_name):
        # on empty topic name, update topics 
        if topic_name in ('', '/'):
            self.topic_completer.update_topics()

        # check for numeric field type
        field_type = self._get_field_type(topic_name)
        if field_type in (int, float):
            self.subscribe_topic_button.setEnabled(True)
            self.subscribe_topic_button.setToolTip('topic "%s" is numeric: %s' % (topic_name, field_type))
        else:
            self.subscribe_topic_button.setEnabled(False)
            self.subscribe_topic_button.setToolTip('topic "%s" is NOT numeric: %s' % (topic_name, field_type))


    @Slot()
    def on_subscribe_topic_button_clicked(self):
        self.add_topic(str(self.topic_edit.text()))


    def add_topic(self, topic_name):
        if topic_name in self.rosdata_:
            qDebug('Plot.add_topic(): topic already subscribed: %s' % topic_name)
            return

        self.data_plot.addCurve(topic_name, topic_name)
        self.rosdata_[topic_name] = ROSData(topic_name, self.start_time)


    @Slot()
    def on_clear_button_clicked(self):
        self.clean_up_subscribers()


    def clean_up_subscribers(self):
        for topic_name, rosdata in self.rosdata_.items():
            rosdata.close()
            self.data_plot.removeCurve(topic_name)
        self.rosdata_ = {}


    def save_settings(self, global_settings, perspective_settings):
        #perspective_settings.set_value('publishing_', self.publishing_)
        pass


    def restore_settings(self, global_settings, perspective_settings):
        #self.publishing_ = perspective_settings.value('publishing_') in [True, 'true']
        pass


    def set_name(self, name):
        self.setWindowTitle(name)


    # override Qt's closeEvent() method to trigger plugin unloading
    def closeEvent(self, event):
        QDockWidget.closeEvent(self, event)
        if event.isAccepted():
            self.deleteLater()


    def close_plugin(self):
        self.clean_up_subscribers()
        QDockWidget.close(self)
