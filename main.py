import sys
from PyQt5.QtWidgets import QDialog, QApplication,QMainWindow
from PyQt5.QtChart import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy as np

from MainWindow import Ui_MainWindow
from CircuitResponse import BodePlot


def series_to_polyline(xdata, ydata):
    """Convert series data to QPolygon(F) polyline

    This code is derived from PythonQwt's function named 
    `qwt.plot_curve.series_to_polyline`"""
    size = len(xdata)
    polyline = QPolygonF(size)
    pointer = polyline.data()
    dtype, tinfo = np.float, np.finfo  # integers: = np.int, np.iinfo
    pointer.setsize(2*polyline.size()*tinfo(dtype).dtype.itemsize)
    memory = np.frombuffer(pointer, dtype)
    memory[:(size-1)*2+1:2] = xdata
    memory[1:(size-1)*2+2:2] = ydata
    return polyline    

class AppWindow(QMainWindow,Ui_MainWindow):
    def __init__(self):
        super(AppWindow, self).__init__()
        self.setupUi(self)
        self.chart =  QChart()
        self.chart.legend().hide()
        self.chartview = QChartView(self.chart)
        self.chartview.setRenderHint(QPainter.Antialiasing)
        self.chartview.setMinimumSize(QSize(1000,500))
        self.BodePlot.layout().addWidget(self.chartview)
        self.resize(self.minimumSizeHint())
        self.ncurves=0
        self.show()  

        self.xAxis = QValueAxis()
        #xAxis.setTickCount(10);
        self.xAxis.setLabelFormat('%.2f')
        self.chart.addAxis(self.xAxis,Qt.AlignBottom)


        self.add_data(range(5),(5))
        
        #connect signals and slots
        self.start_pushButton.clicked.connect(self.bodeMeasurementStart)

    
    def bodeMeasurementStart(self):
        self.plot = BodePlot('A',print)
        if self.plot.connected:
            frequencies = range(self.startFreq_spinBox.value(),self.stopFreq_spinBox.value(),self.stepFreq_spinBox.value())    
            (AvgPhases,AvgAmplitudes) = self.plot.getCharacteristicsAveraged(self.Signal_doubleSpinBox.value(),frequencies,passes = 1)
            self.add_data(frequencies, AvgPhases, color=Qt.blue)
            self.add_data(frequencies, AvgAmplitudes, color=Qt.red)

    def add_data(self, xdata, ydata, color=None):
        curve = QLineSeries()
        pen = curve.pen()
        if color is not None:
            pen.setColor(color)
        pen.setWidthF(.1)
        curve.setPen(pen)
        curve.setUseOpenGL(True)
        curve.append(series_to_polyline(xdata, ydata))
        
        #self.chart.createDefaultAxes()
        yAxis = QValueAxis()
        self.chart.addAxis(yAxis,Qt.AlignLeft)
        
        
        self.chart.addSeries(curve)
        curve.attachAxis(self.xAxis)
        curve.attachAxis(yAxis)
        
 

        self.ncurves += 1


    def printToLog():
        
        return

def main():
    app = QApplication(sys.argv)
    w = AppWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()