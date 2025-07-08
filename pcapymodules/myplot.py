import numpy as np
from matplotlib import pyplot as plt
from ..analysis import mynormalize
import matplotlib as mpl

class DraggableColorbar(object):
    def __init__(self, cbar, mappable):
        self.cbar = cbar
        self.mappable = mappable
        self.press = None
        self.cycle = sorted([i for i in dir(plt.cm) if hasattr(getattr(plt.cm,i),'N')])
        self.index = self.cycle.index(cbar.get_cmap().name)

    def connect(self):
        """connect to all the events we need"""
        self.cidpress = self.cbar.patch.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidrelease = self.cbar.patch.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.cbar.patch.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)
        self.keypress = self.cbar.patch.figure.canvas.mpl_connect(
            'key_press_event', self.key_press)

    def on_press(self, event):
        """on button press we will see if the mouse is over us and store some data"""
        if event.inaxes != self.cbar.ax: return
        self.press = event.x, event.y

    def key_press(self, event):
        if event.key=='down':
            self.index += 1
        elif event.key=='up':
            self.index -= 1
        if self.index<0:
            self.index = len(self.cycle)
        elif self.index>=len(self.cycle):
            self.index = 0
        cmap = self.cycle[self.index]
        self.cbar.set_cmap(cmap)
        self.cbar.draw_all()
        self.mappable.set_cmap(cmap)
        #self.mappable.get_axes().set_title(cmap)
        print("Current CMAP used is ", self.index, " ", cmap)
        self.cbar.patch.figure.canvas.draw()

    def on_motion(self, event):
        'on motion we will move the rect if the mouse is over us'
        if self.press is None: return
        if event.inaxes != self.cbar.ax: return
        xprev, yprev = self.press
        dx = event.x - xprev
        dy = event.y - yprev
        self.press = event.x,event.y
        #print 'x0=%f, xpress=%f, event.xdata=%f, dx=%f, x0+dx=%f'%(x0, xpress, event.xdata, dx, x0+dx)
        scale = self.cbar.norm.vmax - self.cbar.norm.vmin
        perc = 0.03
        if event.button==1:
            self.cbar.norm.vmin -= (perc*scale)*np.sign(dy)
            self.cbar.norm.vmax -= (perc*scale)*np.sign(dy)
        elif event.button==3:
            self.cbar.norm.vmin -= (perc*scale)*np.sign(dy)
            self.cbar.norm.vmax += (perc*scale)*np.sign(dy)
        self.cbar.draw_all()
        self.mappable.set_norm(self.cbar.norm)
        self.cbar.patch.figure.canvas.draw()


    def on_release(self, event):
        """on release we reset the press data"""
        self.press = None
        self.mappable.set_norm(self.cbar.norm)
        self.cbar.patch.figure.canvas.draw()

    def disconnect(self):
        """disconnect all the stored connection ids"""
        self.cbar.patch.figure.canvas.mpl_disconnect(self.cidpress)
        self.cbar.patch.figure.canvas.mpl_disconnect(self.cidrelease)
        self.cbar.patch.figure.canvas.mpl_disconnect(self.cidmotion)

def get_image(M,labels={},cax=None,cbar_connect=True):
    img=plt.imshow(M.Z,cmap=plt.cm.rainbow,interpolation='bilinear',aspect=(M.X.max()-M.X.min())/(M.Y.max()-M.Y.min()),origin='lower',extent=(M.X.min(),M.X.max(),M.Y.min(),M.Y.max()))
    if labels=={}:
        plt.xlabel(M.xlabel)
        plt.ylabel(M.ylabel)
        cbar=plt.colorbar(img,cax,label=M.zlabel)
    else:
        plt.xlabel(labels['x']);plt.ylabel(labels['y'])
        #cbar=plt.colorbar(img)
        cbar=plt.colorbar(img,label=labels['z'])
    extent=(M.X.min(),M.X.max(),M.Y.min(),M.Y.max())
    img.set_extent(extent)
    cbar.set_norm(mynormalize.MyNormalize(vmin=M.Z.min(),vmax=M.Z.max(),stretch='linear'))
    if cbar_connect==True:
        cbar = DraggableColorbar(cbar,img)
        cbar.connect()
    ax=plt.gca()
    ax.set_aspect(abs((ax.get_xlim()[1]-ax.get_xlim()[0])/(ax.get_ylim()[1]-ax.get_ylim()[0])))
    plt.xlim(M.X.min(),M.X.max())    
    plt.ylim(M.Y.min(),M.Y.max())
    return img,cbar

def get_Ticks(n2_lim,no=5,round_off=0.01,factor=1):
    lim_max=n2_lim[1]*factor
    lim_min=n2_lim[0]*factor
    TicksValue=[];TicksPos=[]
    for tick in np.linspace(lim_min,lim_max,no):
        TicksValue.append(str(int(tick/round_off)*round_off))
        TicksPos.append(int(tick/round_off)*round_off/factor)
    return TicksPos, TicksValue

def get_contourf(M,labels={}):
    img=plt.contourf(M.X,M.Y,M.Z,cmap=plt.cm.rainbow,interpolation='bilinear',aspect=(M.X.max()-M.X.min())/(M.Y.max()-M.Y.min()),origin='lower',extent=(M.X.min(),M.X.max(),M.Y.min(),M.Y.max()))
    if labels=={}:
        plt.xlabel(M.xlabel)
        plt.ylabel(M.ylabel)
        cbar=plt.colorbar(img,label=M.zlabel)
    else:
        plt.xlabel(labels['x']);plt.ylabel(labels['y'])
        #cbar=plt.colorbar(img)
        cbar=plt.colorbar(img,label=labels['z'])
    #extent=(M.X.min(),M.X.max(),M.Y.min(),M.Y.max())
    #img.set_extent(extent)
    cbar.set_norm(mynormalize.MyNormalize(vmin=M.Z.min(),vmax=M.Z.max(),stretch='linear'))
    cbar = DraggableColorbar(cbar,img)
    cbar.connect()
    ax=plt.gca()
    ax.set_aspect(abs((ax.get_xlim()[1]-ax.get_xlim()[0])/(ax.get_ylim()[1]-ax.get_ylim()[0])))
    plt.xlim(M.X.min(),M.X.max())    
    plt.ylim(M.Y.min(),M.Y.max())
    return img,cbar        


def cmtoinch(cm_value):
    return   cm_value/2.54

def get_location(Mother_location,Daughter_location):
    New_location=[0,0,0,0]
    New_location[0]=Mother_location[0]+Mother_location[2]*Daughter_location[0]
    New_location[1]=Mother_location[1]+Mother_location[3]*Daughter_location[1]
    New_location[2]=Daughter_location[2]*Mother_location[2]
    New_location[3]=Daughter_location[3]*Mother_location[3]  
    return New_location

def get_norm(vlist,ncolors=256):
    l=len(vlist)-1
    n=int(420/l)
    bound=np.array([])
    for i in range (l):
        b=np.linspace(vlist[i],vlist[i+1],n)
        bound=np.concatenate((bound,b),axis=0)
    norm = mpl.colors.BoundaryNorm(boundaries=bound, ncolors=ncolors)
    return norm
	
def put_panel_label (fignumber,Location,xoffset=0.08,yoffset=0.02,style='nature', fontweight='none',fontsize='none'):
    if style == 'nature':
        if fontweight == 'none':
            fontweight = 'bold'
        if fontsize == 'none':
            fontsize = 'large'
    elif style == 'thesis':
        if fontweight == 'none':
            fontweight = 'bold'
        if fontsize == 'none':
            fontsize = 'x-large'
    elif style == 'aps':
        if fontweight == 'none':
            fontweight = 'normal'
        if fontsize == 'none':
            fontsize = 'x-large'
        fignumber = '('+fignumber + ')'
    plt.figtext(Location[0]-xoffset,Location[1]+Location[3]-yoffset,fignumber,fontweight=fontweight,fontsize=fontsize)
    
    
