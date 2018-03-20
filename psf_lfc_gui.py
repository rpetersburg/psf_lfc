import sys
from thorlabs_kinesis import list_devices, PiezoController
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QMainWindow, QWidget, QGridLayout, QHBoxLayout,
        QVBoxLayout, QPushButton, QApplication, QLabel, QComboBox, QLineEdit,
        QFrame, QRadioButton, QButtonGroup, QStatusBar)

class PSFLFCGui(QMainWindow):
    """
    The primary GUI window. Includes two FiberStage Widgets, a connect button,
    a VoltageStep Widget, and a disconnect button.
    """
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PSF LFC Alignment')

        self.main_widget = QWidget(self)

        self.piezo_dict = {}

        self.input_box = FiberStage(self, 'Input Stage')
        self.output_box = FiberStage(self, 'Output Stage')

        self.connect_frame = ConnectFrame(self)
        self.connect_frame.connected.connect(self.initPiezos)
        self.connect_frame.disconnected.connect(self.closePiezos)

        self.enable_frame = EnableFrame(self)
        self.enable_frame.enabled.connect(self.enablePiezos)
        self.enable_frame.disabled.connect(self.disablePiezos)

        self.voltage_step = VoltageEdit('Step Size:')
        self.voltage_step.returnPressed.connect(self.setVoltageStep)
        self.all_voltages = VoltageEdit('All Voltages:')
        self.all_voltages.returnPressed.connect(self.setAllVoltages)

        vbox3 = QVBoxLayout()
        vbox3.addStretch(1)
        vbox3.addWidget(self.voltage_step)
        vbox3.addWidget(self.all_voltages)
        vbox3.addStretch(1)
        vbox3.setAlignment(self.voltage_step, Qt.AlignRight)
        vbox3.setAlignment(self.all_voltages, Qt.AlignRight)

        # hbox2 = QHBoxLayout()
        # hbox2.addStretch(1)
        # hbox2.addWidget(self.connect_frame)
        # hbox2.addWidget(self.enable_frame)
        # hbox2.addLayout(vbox3)
        # hbox2.addStretch(1)

        # vbox = QVBoxLayout(self.main_widget)
        # vbox.addStretch(1)
        # vbox.addLayout(hbox1)
        # vbox.addLayout(hbox2)
        # vbox.addStretch(1)

        grid = QGridLayout(self.main_widget)
        grid.addWidget(self.input_box, 0, 0, 1, 2)
        grid.addWidget(self.output_box, 0, 2, 1, 2)
        grid.addWidget(self.connect_frame, 2, 0)
        grid.addWidget(self.enable_frame, 2, 1)
        grid.addLayout(vbox3, 2, 2, 1, 2)

        self.setCentralWidget(self.main_widget)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.keyboard_options = {
            Qt.Key_W: self.input_box.z_axis.pos,
            Qt.Key_S: self.input_box.z_axis.neg,
            Qt.Key_A: self.input_box.x_axis.neg,
            Qt.Key_D: self.input_box.x_axis.pos,
            Qt.Key_Q: self.input_box.y_axis.neg,
            Qt.Key_E: self.input_box.y_axis.pos,
            Qt.Key_I: self.output_box.z_axis.pos,
            Qt.Key_K: self.output_box.z_axis.neg,
            Qt.Key_J: self.output_box.x_axis.neg,
            Qt.Key_L: self.output_box.x_axis.pos,
            Qt.Key_U: self.output_box.y_axis.neg,
            Qt.Key_O: self.output_box.y_axis.pos
            }

        self.show()
        self.status_bar.showMessage('Ready')

    def clearAll(self):
        self.input_box.clear()
        self.output_box.clear()
        self.voltage_step.clear()

    def setAllVoltages(self):
        for stage in [self.input_box, self.output_box]:
            for axis in [stage.x_axis, stage.y_axis, stage.z_axis]:
                axis.setVoltage(self.all_voltages.text())
        self.all_voltages.clearFocus()

    def setVoltageStep(self):
        for serial in self.piezo_dict:
            self.piezo_dict[serial].voltage_step = float(self.voltage_step.text())
        self.setVoltageStepText()        
        self.voltage_step.clearFocus()

    def setVoltageStepText(self):
        self.voltage_step.setText(str(self.piezo_dict[list(self.piezo_dict)[0]].voltage_step))

    def keyPressEvent(self, e):
        if e.key() in self.keyboard_options.keys():
            self.keyboard_options[e.key()].clicked.emit()
        elif e.key() == Qt.Key_Escape:
            self.close()

    def initPiezos(self):
        if not self.piezo_dict:    
            for serial in list_devices():
                self.piezo_dict[serial] = PiezoController(serial)
        else:
            for serial in self.piezo_dict:
                self.piezo_dict[serial].open()

        if self.piezo_dict:
            self.setVoltageStepText()

            for stage in [self.input_box, self.output_box]:
                for axis in [stage.x_axis, stage.y_axis, stage.z_axis]:
                    axis.serial.populateList()

            self.setDefaultPiezos()

            info = [self.piezo_dict[serial].is_enabled for serial in self.piezo_dict]
            if all(info):
                self.enable_frame.pressEnable()
            elif not any(info):
                self.enable_frame.pressDisable()
            else:
            	self.enable_frame.setEnabled(True)

        else:
            self.status_bar.showMessage('No piezos are currently connected')
            self.connect_frame.pressDisconnect()

    def setDefaultPiezos(self):
        i = 0
        piezo_list = sorted(self.piezo_dict)
        for stage in [self.input_box, self.output_box]:
            for axis in [stage.x_axis, stage.y_axis, stage.z_axis]:
                axis.serial.setCurrentText(piezo_list[i])
                i += 1

    def closePiezos(self):
        self.clearAll()
        for stage in [self.input_box, self.output_box]:
            for axis in [stage.x_axis, stage.y_axis, stage.z_axis]:
                axis.piezo = None
        for serial in self.piezo_dict:
            self.piezo_dict[serial].close()
        self.enable_frame.setEnabled(False)

    def enablePiezos(self):
        if self.piezo_dict:
            for serial in self.piezo_dict:
                self.piezo_dict[serial].enable()

            self.input_box.setText()
            self.output_box.setText()
        else:
            self.status_bar.showMessage('No piezos are currently connected')
            self.enable_frame.disabled.emit()

    def disablePiezos(self):
        for serial in self.piezo_dict:
            self.piezo_dict[serial].disable()

        self.input_box.clearVoltage()
        self.output_box.clearVoltage()

class ConnectFrame(QFrame):
    """
    QFrame containing QPushButtons for connecting and disconnecting all of the piezos

    Args
    ----
    parents : QWidget
        The parent Widget
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setFrameShape(QFrame.Box)

        self.connect_button = QPushButton('Connect')
        self.connected = self.connect_button.clicked
        self.connected.connect(self.pressConnect)

        self.disconnect_button = QPushButton('Disconnect')
        self.disconnected = self.disconnect_button.clicked
        self.disconnected.connect(self.pressDisconnect)

        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        layout.addStretch(1)

        self.disconnect_button.setEnabled(False)

    def pressConnect(self):
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)

    def pressDisconnect(self):
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)

class EnableFrame(QFrame):
    """
    QFrame containing QPushButtons for enabling and disabling all of the piezos

    Args
    ----
    parent : QWidget
        The parent Widget
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setFrameShape(QFrame.Box)

        self.button_group = QButtonGroup(self)

        self.enable_button = QPushButton('Enable')
        self.enabled = self.enable_button.clicked
        self.enabled.connect(self.pressEnable)

        self.disable_button = QPushButton('Disable')
        self.disabled = self.disable_button.clicked
        self.disabled.connect(self.pressDisable)

        layout = QVBoxLayout(self)
        layout.addStretch(1)
        layout.addWidget(self.enable_button)
        layout.addWidget(self.disable_button)
        layout.addStretch(1)

        self.enable_button.setEnabled(False)
        self.disable_button.setEnabled(False)

    def setEnabled(self, option):
        self.enable_button.setEnabled(option)
        self.disable_button.setEnabled(option)

    def pressEnable(self):
        self.enable_button.setEnabled(False)
        self.disable_button.setEnabled(True)

    def pressDisable(self):
        self.enable_button.setEnabled(True)
        self.disable_button.setEnabled(False)

class FiberStage(QFrame):
    """
    QFrame containing controls for the three axes of a fiber stage. Each axis
    is a StageAxis object.

    Args
    ----
    parents : QWidget
        The parent Widget
    title : str
        Name of the fiber stage, such as "Input Stage", used to title the
        Widget
    """
    def __init__(self, parent, title):
        super().__init__(parent)
        self.setFrameShape(QFrame.Box)

        self.title = title
        self.piezo_dict = parent.piezo_dict

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)

        label = QLabel(self.title)
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)

        self.x_axis = StageAxis(self, 'X')
        self.y_axis = StageAxis(self, 'Y')
        self.z_axis = StageAxis(self, 'Z')

        self.layout.addWidget(self.x_axis)
        self.layout.addWidget(self.y_axis)
        self.layout.addWidget(self.z_axis)

    def clear(self):
        for axis in [self.x_axis, self.y_axis, self.z_axis]:
            axis.clear()

    def clearVoltage(self):
        for axis in [self.x_axis, self.y_axis, self.z_axis]:
            axis.clearVoltage()

    def setText(self):
        for axis in [self.x_axis, self.y_axis, self.z_axis]:
            axis.setText()

class DirectionButton(QPushButton):
    def __init__(self, label, parent):
        super().__init__(label, parent)
        self.setFixedSize(40, 40)

class SerialDropdown(QComboBox):
    def __init__(self, parent):
        super().__init__(parent)

    def populateList(self):
        self.addItems([''] + list(self.parent().piezo_dict))
        self.setCurrentIndex(0)

def _if_piezo_connected(func):
    def wrapper(self, *args, **kwargs):
        if self.piezo is not None:
        	return func(self, *args, **kwargs)
        else:
            print('No serial number chosen')
    return wrapper

class StageAxis(QWidget):
    """
    Widget for each axis of the fiber stage. Contains the PiezoController
    object as well as a dropdown to choose the serial number and direction
    buttons.

    Args
    ----
    parent : QWidget
        Object of the parent Widget. Passed to the superclass QWidget.
    axis : str {'X', 'Y', 'Z'}
        Which axis to create. Labels the Widget and buttons
    """
    def __init__(self, parent, axis):
        super().__init__(parent)
        self.layout = QGridLayout(self)

        self.parent = parent
        self.piezo_dict = self.parent.piezo_dict
        self.piezo = None

        self.label = QLabel(axis + '-Axis:')
        self.serial = SerialDropdown(self)
        self.voltage_edit = VoltageEdit()
        self.neg = DirectionButton(axis + '-', self)
        self.pos = DirectionButton(axis + '+', self)

        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.serial, 0, 1, 1, 2)
        self.layout.addWidget(self.voltage_edit, 1, 0)
        self.layout.addWidget(self.neg, 1, 1)
        self.layout.addWidget(self.pos, 1, 2)

        self.serial.currentTextChanged.connect(self.serialChanged)
        self.voltage_edit.returnPressed.connect(self.setVoltage)
        self.neg.clicked.connect(self.decreaseVoltage)
        self.pos.clicked.connect(self.increaseVoltage)

    def clear(self):
        self.clearVoltage()
        self.clearSerial()

    def clearVoltage(self):
        self.voltage_edit.clear()

    def clearSerial(self):
        self.serial.clear()

    @_if_piezo_connected
    def setText(self):
        """Set the text of the voltage to the current reading from the piezo"""
        if self.piezo.voltage is not None:
            self.voltage_edit.setText(str(round(self.piezo.voltage, 2)))

    def serialChanged(self):
        """Set the object to the piezo object with the selected serial number"""
        current_text = self.serial.currentText()
        if current_text:
            self.piezo = self.piezo_dict[current_text]
            self.setText()

    @_if_piezo_connected
    def decreaseVoltage(self, something=True):
        """Decrease voltage by one voltage step"""
        self.piezo.decrease_voltage()
        self.setText()

    @_if_piezo_connected
    def increaseVoltage(self, something=True):
        """Increase voltage by one voltage step"""
        self.piezo.increase_voltage()
        self.setText()

    @_if_piezo_connected
    def setVoltage(self, voltage=None):
        """Set voltage to the value in the voltage edit box"""
        if voltage is None:
            self.piezo.set_voltage(float(self.voltage_edit.text()))
        else:
            self.piezo.set_voltage(float(voltage))
        self.setText()
        self.voltage_edit.clearFocus()

class VoltageEdit(QWidget):
    """
    An editable text box for entering voltages. Standardizes QLineEdit to
    include a label and the unit 'V'

    Args
    ----
    label : str, optional
        Label for the voltage box presented to the left of the box.
    """
    def __init__(self, label=''):
        super().__init__()
        self.layout = QHBoxLayout(self)

        if label:
            self.label = QLabel(label)
        self.line_edit = QLineEdit()
        self.line_edit.setAlignment(Qt.AlignRight)
        self.line_edit.setMaximumWidth(80)
        self.v_label = QLabel('V')

        self.layout.addStretch(1)
        if label:
            self.layout.addWidget(self.label)
        self.layout.addWidget(self.line_edit)
        self.layout.addWidget(self.v_label)
        self.layout.addStretch(1)
        self.layout.setSpacing(10)

        self.returnPressed = self.line_edit.returnPressed
        self.text = self.line_edit.text
        self.clearFocus = self.line_edit.clearFocus

    def clear(self):
        self.line_edit.clear()

    def setText(self, text):
        self.line_edit.setText(text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = PSFLFCGui()
    sys.exit(app.exec_())
