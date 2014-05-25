__author__ = 'Bonus'

import sys
import cv
import cv2
import numpy as np
import freenect
import frame_convert
import time
from PyQt4 import QtGui, QtCore, Qt, uic
from PyQt4.QtCore import SIGNAL, QObject
from main_ui import Ui_MainWindow

class Controller(QtCore.QThread):
    ImageUpdate = QtCore.pyqtSignal(object)

    def __init__(self, cf):
        QtCore.QThread.__init__(self)

    def detect(self):
        try:
            raw_depth = freenect.sync_get_depth()[0]
        except:
            depth_image = None

        if not depth_image:
            return (False, 0)

        min_depth = np.min(raw_depth)
        depth_image = frame_convert.my_depth_convert(raw_depth, min_depth + 180, min_depth)
        depth_image = cv2.GaussianBlur(depth_image, (5, 5), 0)
        # ret, thresh_image = cv2.threshold(depth_image, 120, 255, cv2.THRESH_BINARY)
        thresh_image = cv2.medianBlur(depth_image, 7)
        ret, thresh_image = cv2.threshold(thresh_image, 100, 255, cv2.THRESH_BINARY_INV)
        detect_image = thresh_image

        contours, hierarchy = cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        max_area = 0
        if contours:
            for i in xrange(len(contours)):
                cnt = contours[i]
                area = cv2.contourArea(cnt)
                if area > max_area:
                    max_area = area
                    ci = i

            cnt = contours[ci]
            x,y,w,h = cv2.boundingRect(cnt)
            cv2.rectangle(detect_image, (x,y), (x+w, y+h), (255,0,0), 1)
            hull = cv2.convexHull(cnt)
            # drawing = np.zeros(thresh_image.shape, np.uint8)
            # cv2.drawContours(drawing,[cnt], 0, (0,255,0), 2)
            # cv2.drawContours(drawing,[hull], 0, (0,0,255), 2)
            cnt = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)
            hull = cv2.convexHull(cnt, returnPoints=False)
            # print "Hull count = {}".format(len(hull))
            defects = cv2.convexityDefects(cnt, hull)
            if type(defects) == np.ndarray:
                # print "---------------- {}" .format(defects.shape[0])
                # cv2.putText(color_image, "{}".format(defects.shape[0]), (30, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0))
                cv2.putText(detect_image, "{}".format(defects.shape[0]), (30, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255))
                for i in range(defects.shape[0]):
                    s,e,f,d = defects[i,0]
                    start = tuple(cnt[s][0])
                    end = tuple(cnt[e][0])
                    far = tuple(cnt[f][0])
                    cv2.line(detect_image, start, end, [0,255,0], 2)
                    cv2.circle(detect_image, far, 5, [0,0,255], -1)
            self.ImageUpdate.emit(detect_image)
            return (True, 0)
        else:
            self.ImageUpdate.emit()
            return  (False, 0)

    def run(self):
        while True:
            found, result = self.detect()

class Gui(QtGui.QMainWindow):
    def __init__(self,parent=None):
        self.controller = Controller
        self.controller.start()
        self.controller.ImageUpdate(self.image_update)

    def image_update(self, cvRGBImg):
        qimg = QtGui.QImage(cvRGBImg.data,cvRGBImg.shape[1], cvRGBImg.shape[0], QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)
        myScaledPixmap = pixmap.scaled(self.lbDepth.size(), Qt.KeepAspectRatio)
        self.lbDepth.setPixmap(myScaledPixmap)
    #     QtGui.QMainWindow.__init__(self,parent)
    #     self.ui = Ui_MainWindow()
    #     self.ui.setupUi(self)
    #     self.video = Video()
    #     self._timer = QtCore.QTimer(self)
    #     self._timer.timeout.connect(self.play)
    #     self._timer.start(27)
    #     self.update()
    #
    # def play(self):
    #     try:
    #         self.video.captureNextFrame()
    #         self.ui.lbDepth.setPixmap(
    #             self.video.convertFrame())
    #         self.ui.lbDepth.setScaledContents(True)
    #     except TypeError:
    #         print "No frame"

def main():
    app = QtGui.QApplication(sys.argv)
    ex = Gui()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()