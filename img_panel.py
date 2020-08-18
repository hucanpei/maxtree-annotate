import numpy as np
from scipy.ndimage import label

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from algorithm import get_nodes,get_curve,select_region

### apply window to the image
def windowing(img,wc,ww):
    img_min=(2*wc-ww)/2.0+0.5
    img_max=(2*wc+ww)/2.0+0.5
    img=(img-img_min)*255.0/(float)(img_max-img_min)
    np.clip(img,0,255,out=img)
    img=img.astype(np.uint8)
    return img

def xw_to_x0x1(x,w):
    if(w>=0):
        x0,x1=x,x+w
    else:
        x0,x1=x+w,x
    return x0,x1

### edit the label
class lbl_edit():
    def __init__(self,img_area):
        # self.data stores the label wiht numpy array
        self.data=np.zeros((512,512,512),dtype=np.uint8)
        self.tmp=np.zeros((512,512,512),dtype=np.uint8)
        self.img_area=img_area
    ### draw a circle in label
    def draw_circle(self,x_0,y_0,z_0,r):
        z,y,x=np.ogrid[0:512,0:512,0:512]
        mask=(x-x_0)**2+(y-y_0)**2+(z-z_0)**2<=r**2
        self.data[mask]=1
    ### add a segment area according to initial point in image and selected node in maxtree
    def add_segment(self,node,x,y,z):
        r=self.img_area.img_panel.main_window.fig_panel.fig_area.volume_list[node]
        if x>=0 and y>=0 and z>=0:
            self.draw_circle(x,y,z,r)
    ### erase a connected component which contains given position
    def erase_segment(self,x,y,z):
        # label all component
        data_label,num_label=label(self.data)
        # remove this component
        self.data[data_label==data_label[z,y,x]]=0
    def undo(self):
        self.tmp=np.zeros((512,512,512),dtype=np.uint8)
    def write(self):
        np.bitwise_or(self.data,self.tmp,out=self.data)
        self.tmp=np.zeros((512,512,512),dtype=np.uint8)
#    def get_roi(self):
#        roi=self.img_area.cal_bbox()
#        if len(roi)==4:
#            x0,x1,y0,y1=roi
#        elif len(roi)==6:
#            x0,x1,y0,y1,z0,z1=roi


### area to show the image
class img_area(QLabel):
    def __init__(self,img_panel):
        super(img_area,self).__init__()
        self.W,self.H=512,512
        self.setFixedSize(self.W,self.H)
        # "window" for adjusting wc/ww
        self.mode="window"
        # ROI
        self.roi_type="null"
        self.roi_x,self.roi_y,self.roi_z=-1,-1,-1
        self.roi_w,self.roi_h,self.roi_d=-1,-1,-1
        # when mouse moves, update
        self.setMouseTracking(True)
        # current slice
        self.slice_num=0
        # selected initial point
        self.circle_x=self.circle_y=-1
        self.circle_slice=-1
        # drag_flag=True when dragging(move mouse with left button pressed)
        self.drag_flag=False
        # show/hide label
        self.show_flag=True
        # wc/ww
        self.wc,self.ww=400,800
        # 3d image
        self.img_3d=np.zeros((512,512,512),dtype=np.uint8)
        self.lbl_edit=lbl_edit(self)
        self.img_panel=img_panel
    ### when left button pressed and mode is "window", adjusting wc/ww
    ### when left button pressed and mode is "select", select initial point
    ### whrn right button pressed, remove connected component at this position
    def mousePressEvent(self,event):
        s=event.pos()
        z,y,x=self.slice_num,int(s.y()),int(s.x())
        self.x_click,self.y_click=x,y
        if event.buttons()==Qt.LeftButton:
            if self.mode=="window":
                # set drag_flag=True for dragging
                self.drag_flag=True
                self.x_window,self.y_window=x,y
            if self.mode=="2d roi":
                self.drag_flag=True
                self.roi_x,self.roi_y=x,y
                self.roi_z=self.slice_num
                self.roi_d=-1
            if self.mode=="3d roi":
                self.drag_flag=True
                self.roi_x,self.roi_y=x,y
                self.roi_z=self.roi_d=-1
            if self.mode=="select":
                # select initial point, draw a circle, and update the curve in fig_panel
                self.setCursor(Qt.CrossCursor)
                self.circle_x,self.circle_y=x,y
                self.circle_slice=self.slice_num
                self.img_panel.main_window.fig_panel.fig_area.volume_list=self.get_curve()
                self.update()
                self.img_panel.main_window.fig_panel.fig_area.update()
        if event.buttons()==Qt.RightButton:
            # erase current connected component
            self.lbl_edit.erase_segment(x,y,z)
            self.update()
    ### when mouse released, exit dragging
    def mouseReleaseEvent(self,event):
        self.drag_flag=False
        self.update()
    ### when mouse moved, update text in img_panel
    ### if dragging, adjusting wc/ww according to relative offset
    def mouseMoveEvent(self,event):
        x,y,z=self.show_text(event)
        if self.mode=="2d roi":
            self.roi_type="2d"
        elif self.mode=="3d roi":
            self.roi_type="3d"
        if self.drag_flag:
            if self.mode=="window":
                # compute offset from last position
                d_x,d_y=x-self.x_window,y-self.y_window
                # adjust wc/ww
                self.wc+=int(d_x*4)
                self.ww+=int(d_y*4)
                self.show_img(self.wc,self.ww)
                # update last position
                self.x_window,self.y_window=x,y
            if self.mode=="2d roi":
                self.roi_w,self.roi_h=x-self.roi_x,y-self.roi_y
            if self.mode=="3d roi":
                self.roi_w,self.roi_h=x-self.roi_x,y-self.roi_y
                # crop 2d area to compute maxtree
        print("x={},y={},z={},w={},h={},d={}".format(self.roi_x,self.roi_y,self.roi_z,self.roi_w,self.roi_h,self.roi_d))
        roi=self.calc_bbox()
        print(roi)
        self.update()
    ### when wheel scrolled, show next slice in 3d image
    def wheelEvent(self,event):
        x,y,z=self.show_text(event)
        # compute how far it scrolled
        angle=event.angleDelta()/120
        angleX,angleY=angle.x(),angle.y()
        # update current slice number
        self.slice_num+=angleY
        # update slider in img_panel
        self.img_panel.sld.setValue(self.slice_num)
        # show current slice
        self.show_img(self.wc,self.ww)
    ### when painting, draw circle for initial point, draw label
    def paintEvent(self,event):
        super().paintEvent(event)
        self.painter=QPainter(self)
        self.painter.begin(self)
        self.draw_rectangle(self.painter)
        # draw circle for initial point
        self.draw_circle(self.painter)
        # draw label
        self.draw_label(self.painter)
        self.painter.end()
    ### draw a rectangle when selecting roi
    def draw_rectangle(self,painter):
        # draw black box
        painter.setPen(Qt.black)
        painter.drawRect(0,0,self.W-1,self.H-1)
        painter.setPen(Qt.red)
        if self.roi_type=="2d" and self.slice_num==self.roi_z:
            painter.drawRect(self.roi_x,self.roi_y,self.roi_w,self.roi_h)
        if self.roi_type=="3d" and (self.roi_z==-1 or self.roi_d==-1):
            painter.drawRect(self.roi_x,self.roi_y,self.roi_w,self.roi_h)
        if self.roi_type=="3d" and abs(self.slice_num-self.roi_z)+abs(self.slice_num-(self.roi_z+self.roi_d))==abs(self.roi_d):
            painter.drawRect(self.roi_x,self.roi_y,self.roi_w,self.roi_h)
    ### draw a circle at selected initial point
    def draw_circle(self,painter):
        if self.circle_slice==self.slice_num:
            roi=self.calc_bbox()
            x0,x1,y0,y1=roi[:4]
            assert self.circle_x>x0 and self.circle_x<x1 and self.circle_y>y0 and self.circle_y<y1, "selected initial point must in bbox"
            # choose a color for initial point
            painter.setPen(QColor(255,80,0,160))
            painter.drawEllipse(self.circle_x-2,self.circle_y-2,5,5)
    ### paint label
    def draw_label(self,painter):
        if self.show_flag:
            # choose a color for label_tmp
            painter.setPen(QColor(250,0,0,160))
            # paint where label_tmp=1, only paint current slice
            labels_tmp=np.where(self.lbl_edit.tmp[self.slice_num]==1)
            for (y,x) in zip(labels_tmp[0],labels_tmp[1]):
                painter.drawPoint(x,y)
            # choose a color for label
            painter.setPen(QColor(255,80,0,160))
            # paint where label=1, only paint current slice
            labels=np.where(self.lbl_edit.data[self.slice_num]==1)
            for (y,x) in zip(labels[0],labels[1]):
                painter.drawPoint(x,y)

    def set_3d_roi_begin(self):
        self.roi_z=self.slice_num
    def set_3d_roi_end(self):
        self.roi_d=self.slice_num-self.roi_z
    def calc_bbox(self):
        x0,x1=xw_to_x0x1(self.roi_x,self.roi_w)
        y0,y1=xw_to_x0x1(self.roi_y,self.roi_h)
        if self.roi_type=="2d":
            return [x0,x1,y0,y1,self.roi_z]
        elif self.roi_type=="3d":
            z0,z1=xw_to_x0x1(self.roi_z,self.roi_d)
            return [x0,x1,y0,y1,z0,z1]
    ### toggle show/hide label
    def show_hide_lbl(self):
        self.show_flag=not self.show_flag
        self.update()
    ### show origin image in area
    def show_img(self,wc,ww):
        # get current slice
        img_slice=self.img_3d[self.slice_num]
        # adjust wc/ww
        img_w=windowing(img_slice,wc,ww)
        H,W=img_w.shape
        # convert to QImage with 8-bit gray
        self.image=QtGui.QImage(img_w,W,H,QtGui.QImage.Format_Grayscale8)
        # creatt a QPixmap to show image
        self.pixmap=QtGui.QPixmap.fromImage(self.image)
        self.setPixmap(self.pixmap)
    ### default wc/ww
    def set_default_window(self):
        self.wc,self.ww=400,800
        self.show_img(self.wc,self.ww)
    ### update current slice with slider in img_panel
    def sld_get_slice(self):
        # get value in slider
        self.slice_num=self.img_panel.sld.value()
        self.show_img(self.wc,self.ww)
    def show_text(self,event):
        s=event.pos()
        z,y,x=self.slice_num,int(s.y()),int(s.x())
        # update text, showing coordinate and Hu
        self.img_panel.text.setText("X={},Y={},Z={},Hu={}\nmode:{},roi:{},".format(x,y,z,self.img_3d[z,y,x],self.mode,self.roi_type))
        return x,y,z
    def get_maxtree(self):
        bbox=self.calc_bbox()
        if len(bbox)==5:
            x0,x1,y0,y1,z=bbox
            patch=self.img_3d[z,y0:y1,x0:x1]
        elif len(bbox)==6:
            x0,x1,y0,y1,z0,z1=bbox
            patch=self.img_3d[z0:z1,y0:y1,x0:x1]
        self.P,self.S,self.nodes=get_nodes(patch)
        print("maxtree finished!")
    def get_curve(self):
        x,y,z=self.circle_x,self.circle_y,self.circle_slice
        bbox=self.calc_bbox()
        if len(bbox)==5:
            x0,x1,y0,y1,z=bbox
            volume_list=get_curve(self.P,self.S,self.nodes,(y-y0,x-x0))
        elif len(bbox)==6:
            x0,x1,y0,y1,z0,z1=bbox
            volume_list=get_curve(self.P,self.S,self.nodes,(z-z0,y-y0,x-x0))
        return volume_list
    def tmp_segment(self,thre):
        x,y,z=self.circle_x,self.circle_y,self.circle_slice
        bbox=self.calc_bbox()
        if len(bbox)==5:
            x0,x1,y0,y1,z=bbox
            points=select_region(self.P,self.S,self.nodes,(y-y0,x-x0),thre)
            points[0]=points[0]+y0
            points[1]=points[1]+x0
            points.astype(np.uint8)
            region=(np.array([self.circle_slice]*points.shape[1],dtype=np.uint16),np.array(points[0],dtype=np.uint16),np.array(points[1],dtype=np.uint16))
            print(region)
        elif len(bbox)==6:
            x0,x1,y0,y1,z0,z1=bbox
            points=select_region(self.P,self.S,self.nodes,(z-z0,y-y0,x-x0),thre)
            points[0]=points[0]+z0
            points[1]=points[1]+y0
            points[2]=points[2]+x0
            points.astype(np.uint8)
            region=(np.array(points[0],dtype=np.uint16),np.array(points[1],dtype=np.uint16),np.array(points[2],dtype=np.uint16))
            print(region)
        self.lbl_edit.tmp[region]=1



### show the image, text, slider
class img_panel(QLabel):
    def __init__(self,main_window):
        super(img_panel,self).__init__()
        self.main_window=main_window
        self.setFixedSize(512,560)
        self._init_elements()
        self._init_layout()
    def _init_elements(self):
        self.text=QLabel(self)
        self.text.resize(self.text.sizeHint())
        self.img_area=img_area(self)
        self.sld=QSlider(Qt.Horizontal,self)
        self.sld.resize(self.sld.sizeHint())
        # set minimum index for slices
        self.sld.setMinimum(0)
        self.sld.valueChanged.connect(self.img_area.sld_get_slice)
    def _init_layout(self):
        # horizontal layout
        hbox=QHBoxLayout()
        hbox.setSpacing(0)
        hbox.setContentsMargins(0,0,0,0)
        hbox.addStretch(1)
        # vertical layout
        vbox=QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(0,0,0,0)
        vbox.addLayout(hbox)
        vbox.addWidget(self.text)
        vbox.addWidget(self.img_area)
        vbox.addWidget(self.sld)
        vbox.addStretch(1)
        # layout
        self.setLayout(vbox)
    ### load 3d image
    def load_img(self,img_3d):
        self.img_area.img_3d=img_3d
        # set maximum index for slices according to 3d image shape
        self.sld.setMaximum(self.img_area.img_3d.shape[0]-1)

