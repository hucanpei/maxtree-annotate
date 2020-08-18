import time
import numpy as np
import SimpleITK as sitk
from skimage.morphology import max_tree

#def update_volume_list(x,y,z,volume_list):
#    for i in range(len(volume_list)):
#        if i>x:
#            volume_list[i]=i-x
#        else:
#            volume_list[i]=0

def calc_maxtree(img,roi):
    if len(roi)==4:
        x0,x1,y0,y1,z=roi
        patch=img[z,y0:y1,x0:x1]
        return max_tree(patch)
    elif len(roi)==6:
        x0,x1,y0,y1,z0,z1=roi
        assert z0>=0 and z1>=0, "invalid ROI"
        patch=img[z0:z1,y0:y1,x0:x1]
        return max_tree(patch)

def read_nii(path):
  nii=sitk.ReadImage(path)
  data_zyx=sitk.GetArrayFromImage(nii)
  space_xyz=nii.GetSpacing()
  origin_xyz=nii.GetOrigin()
  return data_zyx,space_xyz,origin_xyz

def write_nii(data_zyx,space_xyz,origin_xyz,path):
  nii=sitk.GetImageFromArray(data_zyx)
  nii.SetSpacing(space_xyz)
  nii.SetOrigin(origin_xyz)
  sitk.WriteImage(nii,path)

# convert a flattened position to coordinate
def to_coord(p,shape):
    if len(shape)==3:
        D,H,W=shape
        z=int(p/(H*W))
        tmp=p%(H*W)
        y=int(tmp/W)
        x=tmp%W
        return (z,y,x)
    elif len(shape)==2:
        H,W=shape
        y=int(p/W)
        x=p%(W)
        return (y,x)

# get a maxtree, its nodes are dicts
def get_nodes(img):
    shape=img.shape
    P,S=max_tree(img)
    keys=np.unique(P)
    nodes={}
    for i,k in enumerate(keys):
        # declare a node, its key is unique_value
        nodes[k]={}
        # get brother node
        bro_coord=to_coord(k,shape)
        nodes[k]["brother"]=bro_coord
        # get parent
        parent=P[bro_coord]
        nodes[k]["parent_key"]=parent
        nodes[k]["parent"]=to_coord(parent,shape)
        # if parent not exist, create it
        if parent not in nodes.keys():
            nodes[parent]={}
        # set parent node's child
        if "child_list" not in nodes[parent].keys():
            nodes[parent]["child_list"]=[bro_coord]
        else:
            nodes[parent]["child_list"].append(bro_coord)
    # root node's parent is None
    nodes[S[0]]["parent"]=None
    nodes[S[0]]["parent_key"]=None
    return P,S,nodes

# calculate a region in each node
# remove points belong to child area
# append brother point
def get_region(P,S,nodes,key_list):
    for k in key_list:
        node=nodes[k]
        # get this region
        node["points"]=np.array(np.where(P==k))
        # remove points belong to child area
        if "child_list" in node.keys():
            for child in node["child_list"]:
                child=np.array(child)[:,np.newaxis]
                match=(node["points"]==child).all(axis=0)
                match_i=np.where(match)[0][0]
                node["points"]=np.delete(node["points"],match_i,axis=1)
        # add brother point
        node["points"]=np.column_stack((node["points"],np.array(node["brother"])[:,np.newaxis]))
        # compute area
        node["area"]=node["points"].shape[1]
        nodes[k]=node
    return nodes

# calculate area curve from initial point
def get_curve(P,S,nodes,init_point):
    # get keys in this path
    k=P[init_point]
    key_list=[]
    while(nodes[k]["parent"]!=None):
        key_list.append(k)
        k=nodes[k]["parent_key"]
    key_list.append(S[0])
    # get regions in this path
    nodes=get_region(P,S,nodes,key_list)
    # get area curve in this path
    area_list=[]
    area=0
    for k in key_list:
        area+=nodes[k]["area"]
        area_list.append(area)
#    for k in key_list:
#        region=np.zeros(P.shape,dtype=np.uint8)
#        node=nodes[k]
#        points=node["points"]
#        where=(points[0],points[1])
#        region[where]=1
#        data_label,num_label=label(region)
#        if num_label!=1:
#            print("k={},num={}".format(k,num_label))
    return area_list

# select a region from area curve
def select_region(P,S,nodes,init_point,thre):
    u=P[init_point]
    node=nodes[u]
    region=np.array([[]]*len(init_point))
    for i in range(thre):
        region=np.column_stack((region,node["points"]))
        node=nodes[node["parent_key"]]
    return region


if __name__=="__main__":
    import matplotlib.pyplot as plt
    from scipy.ndimage import label

#    imgPath="./data/3242898_patch.nii.gz"
    imgPath="./data/3242898.nii.gz"
    img_3d,space,origin=read_nii(imgPath)
#    img=img_3d[300,250:400,150:300]
    img=img_3d[300,:,:]
    print(img.shape)

#    P,S=max_tree(img)
#    unique=np.unique(P)
#    for u in unique:
#        region=np.zeros(img.shape,dtype=np.uint8)
#        region[P==u]=1
#        data_label,num_label=label(region)
#        if num_label!=1:
#            print("k={},num={}".format(u,num_label))


    T=3
    img=np.zeros((7*T,9*T),dtype=np.uint8)
    img[2*T:3*T,1*T:6*T]=1
    img[1*T:4*T,2*T:3*T]=2
    img[1*T:4*T,4*T:5*T]=2
    img[5*T:6*T,7*T:8*T]=4
#    img=np.zeros((7*T,8*T,9*T),dtype=np.uint8)
#    img[2*T:3*T,1*T:2*T,1*T:6*T]=1
#    img[1*T:4*T,3*T:4*T,2*T:3*T]=2
#    img[1*T:4*T,5*T:6*T,4*T:5*T]=2
#    img[5*T:6*T,7*T:8*T,7*T:8*T]=4



    begin=time.time()
    P,S,nodes=get_nodes(img)
    print(P.shape)
    end=time.time()
    print("nodes time:",end-begin)

#    init_point=(206,92)
    init_point=(6,3)
    begin=time.time()
    area_list=get_curve(P,S,nodes,init_point)
    print(len(area_list))
    end=time.time()
    print("curve time:",end-begin)

#    thre=1
#    begin=time.time()
#    region=select_region(P,S,nodes,init_point,thre).astype(np.uint16)
#    end=time.time()
#    print("region time:",end-begin)

#    region_mask=(region[0],region[1])
#    mask=np.zeros(img.shape,dtype=np.uint8)
#    print(nodes[8428]["points"])
#    points=nodes[8428]["points"]
#    region=(np.array(points[0]),np.array(points[1]))
#    mask[region]=1
#    mask[region_mask]=1



#    plt.plot(np.arange(len(area_list)),area_list)
#    plt.show()
#    write_nii(mask,space,origin,"./test.nii.gz")

#    for i,k in enumerate(nodes.keys()):
#        node=nodes[k]
#        print("key:",k)
#        print("brother:",node["brother"])
#        print("parent:",node["parent"])
#        print("area",node["area"])
#        if "child_list" in node.keys():
#            print("childs:",node["child_list"])
#        print()

    regions=[]
    for i,k in enumerate(nodes.keys()):
        node=nodes[k]
        region=np.zeros(img.shape,dtype=np.uint8)
        where=(node["points"][0,:],node["points"][1,:])
        region[where]=1
        regions.append(region)
    plt.subplot(421);plt.imshow(img);plt.title("img")
    plt.subplot(422);plt.imshow(P);plt.title("P")
    #plt.subplot(423);plt.imshow(S.reshape(7*T,9*T));plt.title("S")
    plt.subplot(424);plt.imshow(regions[0]);plt.title("region_0")
    plt.subplot(425);plt.imshow(regions[1]);plt.title("region_1")
    plt.subplot(426);plt.imshow(regions[2]);plt.title("region_2")
    plt.subplot(427);plt.imshow(regions[3]);plt.title("region_3")
    plt.subplot(428);plt.imshow(regions[4]);plt.title("region_4")
    plt.show()

#    plt.subplot(221);plt.imshow(img,cmap='gray');plt.title("img")
#    plt.subplot(222);plt.imshow(P,cmap='gray');plt.title("P")
#    plt.subplot(223);plt.plot(np.arange(len(area_list)),area_list)
#    plt.subplot(224);plt.imshow(mask);plt.title("mask")
#    plt.show()
#
