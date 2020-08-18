import sys
import numpy as np
import SimpleITK as sitk

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from img_panel import img_panel
from fig_panel import fig_panel

### main window of the whole program
class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        #self.resize(500,800)
        self.setWindowTitle("Annotate with maxtree")
        self._center()
        self._init_panels()
        self._init_buttons()
        self._init_layout()
        #self.open_image()
    ### set MainWindow on center of screen
    def _center(self):
        qr=self.frameGeometry()
        cp=QDesktopWidget().screenGeometry(2).center()
        #cp=QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    def _init_buttons(self):
        # open image
        open_btn=self.make_btn("open",self.open_image)
        # save label
        save_btn=self.make_btn("save",self.save_label)
        # help
        help_btn=self.make_btn("help",self.help)
        # quit 
        quit_btn=self.make_btn("quit",QCoreApplication.instance().quit)
        # adjust wc/ww
        window_btn=self.make_btn("window",self.set_mode)
        # using default wc/ww
        default_window_btn=self.make_btn("default window",self.img_panel.img_area.set_default_window)
        # 2d roi
        roi_2d_btn=self.make_btn("2d roi",self.set_mode)
        # 3d roi
        roi_3d_btn=self.make_btn("3d roi",self.set_mode)
        # 3d roi begin
        roi_3d_begin_btn=self.make_btn("begin",self.img_panel.img_area.set_3d_roi_begin)
        # 3d roi end
        roi_3d_end_btn=self.make_btn("end",self.img_panel.img_area.set_3d_roi_end)
        # build maxtree
        tree_btn=self.make_btn("tree",self.img_panel.img_area.get_maxtree)
        # select node
        select_btn=self.make_btn("select",self.set_mode)
        # undo
        undo_btn=self.make_btn("undo",self.img_panel.img_area.lbl_edit.undo)
        # write
        write_btn=self.make_btn("write",self.img_panel.img_area.lbl_edit.write)
        # show/hide label
        show_hide_btn=self.make_btn("show/hide",self.img_panel.img_area.show_hide_lbl)
        # horizontal layout
        self.hbox1=self.make_hbox([open_btn,save_btn,help_btn,quit_btn])
        self.hbox2=self.make_hbox([window_btn,default_window_btn])
        self.hbox3=self.make_hbox([roi_2d_btn,roi_3d_btn,roi_3d_begin_btn,roi_3d_end_btn])
        self.hbox4=self.make_hbox([tree_btn,select_btn,undo_btn,write_btn,show_hide_btn])
    def _init_panels(self):
        # display image
        self.img_panel=img_panel(self)
        # display curve
        self.fig_panel=fig_panel(self)
    def _init_layout(self):
        # vertical layout
        vbox=QVBoxLayout()
        vbox.setSpacing(6)
        vbox.setContentsMargins(6,6,6,6)
        [vbox.addLayout(x) for x in [self.hbox1,self.hbox2,self.hbox3,self.hbox4]]
        [vbox.addWidget(x) for x in [self.img_panel,self.fig_panel]]
        vbox.addStretch(1)
        # layout
        self.setLayout(vbox)
    def make_btn(self,name,func):
        btn=QPushButton(name,self)
        btn.resize(btn.sizeHint())
        btn.clicked.connect(func)
        return btn
    def make_hbox(self,btns):
        hbox=QHBoxLayout()
        hbox.setSpacing(6)
        hbox.setContentsMargins(0,0,0,0)
        [hbox.addWidget(x) for x in btns]
        hbox.addStretch(1)
        return hbox
    ### mode="window" for adjusting wc/ww
    ### mode="2d roi" for crop 2d area
    ### mode="3d roi" for crop 3d area
    ### mode="select" for select initial point
    def set_mode(self):
        self.img_panel.img_area.mode=self.sender().text()
        if self.sender().text()=="select":
            # change cursor shape
            self.img_panel.img_area.setCursor(Qt.CrossCursor)
        else:
            # using default cursor
            self.img_panel.img_area.setCursor(Qt.ArrowCursor)

    ### open image and get spacing/origin with sitk
    def open_image(self):
        imgPath,imgType=QFileDialog.getOpenFileName(self, "open image", "", "*.nii.gz;;All Files(*)")
        #imgPath="/home/canpi/aneurysm/data/part1/3187471.nii.gz"
        nii=sitk.ReadImage(imgPath)
        self.img_space=nii.GetSpacing()
        self.img_origin=nii.GetOrigin()
        self.img_3d=sitk.GetArrayFromImage(nii)
        # load image into image panel
        self.img_panel.load_img(self.img_3d)
    ### save edited label with spacing/origin of origin image
    def save_label(self):
        lblPath,lblType=QFileDialog.getSaveFileName(self,"save label","" ,"*.nii.gz;;all files(*.*)")
        nii=sitk.GetImageFromArray(self.img_panel.img_area.lbl_edit.data)
        nii.SetSpacing(self.img_space)
        nii.SetOrigin(self.img_origin)
        sitk.WriteImage(nii,lblPath)
    ### show help information
    def help(self):
        # read txt to a string
        help_str=""
        for line in open("./help.txt"):
            help_str+=line
        # show a message box
        QMessageBox.information(self,"help",help_str,QMessageBox.Ok)
    ### when click "x", ask if sure to quit
    def closeEvent(self,event):
        reply=QMessageBox.question(self,'Message',
                                   "Are you sure to quit?",
                                   QMessageBox.Yes|QMessageBox.No,
                                   QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    my = MainWindow()
    my.show()
    sys.exit(app.exec_())

