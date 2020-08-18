import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

### area to show the curve
class fig_area(QLabel):
    def __init__(self,fig_panel):
        super(fig_area,self).__init__()
        self.W,self.H=512,256
        self.setFixedSize(self.W,self.H)
        # when mouse moves, update
        self.setMouseTracking(True)
        # y-axis value, store values on the curve, which is the volume of each node
        self.volume_list=np.arange(self.W)
        self.x=0
        # x-axis value, current node on curve
        self.node_num=0
        # interact with other QLabels
        self.fig_panel=fig_panel
        self.img_area=self.fig_panel.main_window.img_panel.img_area
    ### when left button clicked on fig_area, 
    ### get a node in maxtree, add a segment on label, and display on image
    def mousePressEvent(self,event):
        s=event.pos()
        x,y=int(s.x()),int(s.y())
        if event.buttons()==Qt.LeftButton:
            # select a node according to mouse position
            self.x=x
            self.node_num=int(x*len(self.volume_list)/self.W)
            # get initial point in image
            x_img,y_img,z_img=self.img_area.circle_x,self.img_area.circle_y,self.img_area.slice_num
            # add a setment in label according to selected node in maxtree
#            self.img_area.lbl_edit.add_segment(self.node_num,x_img,y_img,z_img)
#            points=self.img_area.get_region(self.node_num)
            self.img_area.lbl_edit.undo()
            self.img_area.tmp_segment(self.node_num)
            self.img_area.update()
            self.update()
    ### when mouse moving in this area, show value on the curve, which is index of node and its volume
    def mouseMoveEvent(self,event):
        s=event.pos()
        x,y=int(s.x()),int(s.y())
        x_list=int(x*len(self.volume_list)/self.W)
        self.fig_panel.text.setText("node={},volume={}".format(x_list,self.volume_list[x_list]))
        print(x)
    ### draw the curve
    def paintEvent(self,event):
        super().paintEvent(event)
        self.painter=QPainter(self)
        self.painter.begin(self)
        # draw black box
        self.painter.setPen(Qt.black)
        self.painter.drawRect(0,0,self.W-1,self.H-1)
        # draw red curve
        self.draw_curve(self.painter)
        self.draw_thre(self.painter)
        self.painter.end()
    ### draw the curve with red pen
    def draw_curve(self,painter):
        scale_y=self.H/self.volume_list[-1]
        scale_i=self.W/len(self.volume_list)
        self.painter.setPen(Qt.red)
        for i,y in enumerate(self.volume_list):
            painter.drawPoint(i*scale_i,self.H-y*scale_y)
    def draw_thre(self,painter):
        for y in range(self.H):
            painter.drawPoint(self.x,y)


### show the curve and text
class fig_panel(QLabel):
    def __init__(self,main_window):
        super(fig_panel,self).__init__()
        self.main_window=main_window
        self.W,self.H=512,275
        self.setFixedSize(self.W,self.H)
        self._init_elements()
        self._init_layout()
    def _init_elements(self):
        # texts showing the number of current node and its volume
        self.text=QLabel(self)
        self.text.resize(self.text.sizeHint())
        # area to show the curve
        self.fig_area=fig_area(self)
    def _init_layout(self):
        hbox=QHBoxLayout()
        hbox.setSpacing(0)
        hbox.setContentsMargins(0,0,0,0)
        hbox.addStretch(1)
        vbox=QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(0,0,0,0)
        vbox.addLayout(hbox)
        vbox.addWidget(self.text)
        vbox.addWidget(self.fig_area)
        vbox.addStretch(1)
        self.setLayout(vbox)

