from PyQt5 import QtCore, QtGui, QtWidgets
from ivy.std_api import *
import sys, logging
logger = logging.getLogger('Ivy')
from optparse import OptionParser

FLAPS = ["Full", "3", "2", "1", "0"]
GEARS = ["Down", "Up"]

bus = "127.255.255.255:2010"

class Ui_config(object):
    def setupUi(self, config):
        config.setObjectName("config")
        config.resize(582, 452)
        self.centralWidget = QtWidgets.QWidget(config)
        self.centralWidget.setObjectName("centralWidget")
        self.widget = QtWidgets.QWidget(self.centralWidget)
        self.widget.setGeometry(QtCore.QRect(72, 32, 471, 304))
        self.widget.setObjectName("widget")
        self.global_h_layout = QtWidgets.QHBoxLayout(self.widget)
        self.global_h_layout.setContentsMargins(11, 11, 11, 11)
        self.global_h_layout.setSpacing(6)
        self.global_h_layout.setObjectName("global_h_layout")
        self.gear_v_layout = QtWidgets.QVBoxLayout()
        self.gear_v_layout.setContentsMargins(11, 11, 11, 11)
        self.gear_v_layout.setSpacing(6)
        self.gear_v_layout.setObjectName("gear_v_layout")
        self.gear_up = QtWidgets.QRadioButton(self.widget)
        self.gear_up.setObjectName("gear_up")
        self.gear_v_layout.addWidget(self.gear_up)
        self.gear_down = QtWidgets.QRadioButton(self.widget)
        self.gear_down.setObjectName("gear_down")
        self.gear_v_layout.addWidget(self.gear_down)
        self.global_h_layout.addLayout(self.gear_v_layout)
        self.sliderwithspace_h_layout = QtWidgets.QHBoxLayout()
        self.sliderwithspace_h_layout.setContentsMargins(11, 11, 11, 11)
        self.sliderwithspace_h_layout.setSpacing(6)
        self.sliderwithspace_h_layout.setObjectName("sliderwithspace_h_layout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.sliderwithspace_h_layout.addItem(spacerItem)
        self.slider_h_layout = QtWidgets.QHBoxLayout()
        self.slider_h_layout.setContentsMargins(11, 11, 11, 11)
        self.slider_h_layout.setSpacing(6)
        self.slider_h_layout.setObjectName("slider_h_layout")

        #Flaps slider
        self.verticalSlider = QtWidgets.QSlider(self.widget)
        self.verticalSlider.setMaximum(len(FLAPS) - 1)
        self.verticalSlider.setOrientation(QtCore.Qt.Vertical)
        self.verticalSlider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.verticalSlider.setTickInterval(0)
        self.verticalSlider.setObjectName("verticalSlider")

        self.slider_h_layout.addWidget(self.verticalSlider)
        self.flap_label_vertical_layout = QtWidgets.QVBoxLayout()
        self.flap_label_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.flap_label_vertical_layout.setSpacing(self.verticalSlider.height()/self.verticalSlider.singleStep())
        self.flap_label_vertical_layout.setObjectName("flap_label_vertical_layout")

        #Ajout des flaps
        for i in range(len(FLAPS)):
            k = len(FLAPS) - i - 1
            flap = QtWidgets.QLabel(self.widget)
            if i == 0: flap.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
            if i == (len(FLAPS) - 1):flap.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft)
            self.flap_label_vertical_layout.addWidget(flap)
            flap.setText(FLAPS[k])

        self.slider_h_layout.addLayout(self.flap_label_vertical_layout)
        self.sliderwithspace_h_layout.addLayout(self.slider_h_layout)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.sliderwithspace_h_layout.addItem(spacerItem1)

        #Global orgarnisation
        self.global_h_layout.addLayout(self.sliderwithspace_h_layout)
        config.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(config)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 582, 22))
        self.menuBar.setObjectName("menuBar")
        config.setMenuBar(self.menuBar)
        self.mainToolBar = QtWidgets.QToolBar(config)
        self.mainToolBar.setObjectName("mainToolBar")
        config.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QtWidgets.QStatusBar(config)
        self.statusBar.setObjectName("statusBar")
        config.setStatusBar(self.statusBar)

        self.retranslateUi(config)
        QtCore.QMetaObject.connectSlotsByName(config)

        self.gear_up.setChecked(True)

    def retranslateUi(self, config):
        _translate = QtCore.QCoreApplication.translate
        config.setWindowTitle(_translate("config", "config"))
        self.gear_up.setText(_translate("config", "Gear up"))
        self.gear_down.setText(_translate("config", "Gear down"))

    def getConfig(self):
        gear = "Unknown"
        if self.gear_down.isChecked(): gear = GEARS[0]
        if self.gear_up.isChecked(): gear =  GEARS[1]
        flaps = FLAPS[self.verticalSlider.sliderPosition()]
        return (gear, flaps)

# Reimplementation de la closeEvent pour quitter ivy lorsque la fenetre se ferme
class ConfigWindow(QtWidgets.QMainWindow):
    def closeEvent(self, event):
        IvyStop()
        QtGui.QCloseEvent(event)


# Main
app = QtWidgets.QApplication(sys.argv)
config = ConfigWindow()
ui = Ui_config()
ui.setupUi(config)
config.show()

#parse
usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.set_defaults(ivy_bus="127.255.255.255:2010", interval=5, verbose=False, app_name="Configuration")
parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                  help='Be verbose.')
parser.add_option('-i', '--interval', type='int', dest='interval',
                  help='Interval between messages (in seconds)')
parser.add_option('-b', '--ivybus', type='string', dest='ivy_bus',
                  help='Bus id (format @IP:port, default to 127.255.255.255:2010)')
parser.add_option('-a', '--appname', type='string', dest='app_name',
                  help='Application Name')
(options, args) = parser.parse_args()

# init log
level = logging.INFO
if options.verbose: # update logging level
    level = logging.DEBUG
logger.setLevel(level)

#Msg send
def send_config(agent=None, *larg):
    (gear, flaps) = ui.getConfig()
    IvySendMsg('Config GEAR={0} FLAPS={1}'.format(gear, flaps))


ui.verticalSlider.valueChanged.connect(send_config)
ui.gear_up.toggled.connect(send_config)

#ivy connection
def on_cx_proc(agent, connected):
    if connected == IvyApplicationDisconnected:
        logger.error('Ivy application %r was disconnected', agent)
    else:
        logger.info('Ivy application %r was connected', agent)
        send_config()


def on_die_proc(agent, _id):
    logger.info('received the order to die from %r with id = %d', agent, _id)


def connect(app_name, ivy_bus):
    IvyInit(app_name,                   # application name for Ivy
            "[%s ready]" % app_name,    # ready message
            0,                          # main loop is local (ie. using IvyMainloop)
            on_cx_proc,                 # handler called on connection/disconnection
            on_die_proc)
    IvyStart(ivy_bus)

connect(options.app_name, options.ivy_bus)
IvyBindMsg(send_config, '^Time t=(\S+)')
sys.exit(app.exec_())
