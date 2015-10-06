'''
Created on 16.05.2013

@author: mtoman

Visualizes DTW results using matplotlib
'''

# class MyClass(object):
#    '''
#    classdocs
#    '''


#    def __init__(selfparams):
#        '''
#        Constructor
#        '''
        
              
from numpy import *
from numpy.random import rand     

def plotDTW(distances, path, xlabels=None, ylabels=None, outfile=None):
    if outfile is not None:
        import matplotlib
        if matplotlib.get_backend() != 'agg':
            matplotlib.use('agg')

    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    """ distances is a map of (x,y) to value """
    rangex = [ x[0] for x in distances.keys() ]
    rangey = [ x[1] for x in distances.keys() ]

    tmpMax = 0
    
    plotmap = zeros((max(rangey) + 1, max(rangex) + 1))
    
    for (x, y) in distances:
        # TODO: >= 1, but why is there crap in col 0?        
        if x > 0 and y > 0:
            #plotmap[y][x] = min(distances[(x, y)], 20000.0)
            plotmap[y][x] = distances[(x, y)]
            if plotmap[y][x] > tmpMax: tmpMax = plotmap[y][x]
        
    for (x, y) in path:
        plotmap[y][x] = tmpMax
            
    fig = plt.figure()    
    ax = fig.add_subplot(111)
    cs = ax.matshow(plotmap)
    fig.colorbar(cs)
        
    if xlabels is not None:    
        beginpos = 0.0
        curlabel = xlabels[0]
        tick_locs = []
        tick_labels = []
        for i in range(len(xlabels)):
            endpos = float(i)
                    
            # the label here is different to the last ones?
            if xlabels[i] != curlabel or i == (len(xlabels) - 1):
                tick_labels.append(curlabel)
                tick_locs.append((endpos + beginpos) / 2.0)
                curlabel = xlabels[i]
                beginpos = endpos
               
        axis = ax.xaxis
        axis.set_major_locator(mticker.FixedLocator(tick_locs))
        axis.set_major_formatter(mticker.FixedFormatter(tick_labels))
        for label in ax.xaxis.get_ticklabels():
            label.set_rotation(90)        
        
    if ylabels is not None:  
        beginpos = 0.0
        curlabel = ylabels[0]
        tick_locs = []
        tick_labels = []
        for i in range(len(ylabels)):
            endpos = float(i)
                    
            # the label here is different to the last ones?
            if ylabels[i] != curlabel or i == (len(ylabels) - 1):
                tick_labels.append(curlabel)
                tick_locs.append((endpos + beginpos) / 2.0)
                curlabel = ylabels[i]
                beginpos = endpos        
                      
        axis = ax.yaxis
        axis.set_major_locator(mticker.FixedLocator(tick_locs))
        axis.set_major_formatter(mticker.FixedFormatter(tick_labels))
    
    if outfile is None:
        plt.show()        
    else:
        plt.savefig(outfile, bbox_inches='tight', dpi=150)
        
    plt.close(fig)
    
    
def plotDTWHorizontal(distances, path, xlabels=None, ylabels=None, outfile=None):
    if outfile is not None:
        import matplotlib
        if matplotlib.get_backend() != 'agg':
            matplotlib.use('agg')

    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    from scipy import ndimage   
    

    """ distances is a map of (x,y) to value """
    rangex = [ x[0] for x in distances.keys() ]
    rangey = [ x[1] for x in distances.keys() ]

    tmpMax = 0
    
    plotmap = zeros((max(rangey) + 1, max(rangex) + 1))
    
    rotAngle = (math.atan(float(max(rangey)) / float(max(rangex)))) * 180.0 / math.pi
    
    for (x, y) in distances:       
        if x > 0 and y > 0:
            plotmap[y][x] = distances[(x, y)]
            if plotmap[y][x] > tmpMax: tmpMax = plotmap[y][x]
        
    for (x, y) in path:
        plotmap[y][x] = tmpMax
        
    plotmap = ndimage.interpolation.rotate(plotmap, rotAngle, reshape=True, order=3, mode='constant', cval=0.0, prefilter=True)
    l = len(plotmap)
    plotmap = plotmap[ int(l * 0.4): int(l * 0.6) ][:]        
        
    # colorbar()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    cs = ax.matshow(plotmap)
    cb = fig.colorbar(cs)
    
    
        
#    if xlabels is not None:    
#        beginpos = 0.0
#        curlabel = xlabels[0]
#        tick_locs = []
#        tick_labels = []
#        for i in range(len(xlabels)):
#            endpos = float(i)
#                    
#            # the label here is different to the last ones?
#            if xlabels[i] != curlabel or i == (len(xlabels) - 1):
#                tick_labels.append(curlabel)
#                tick_locs.append((endpos + beginpos) / 2.0)
#                curlabel = xlabels[i]
#                beginpos = endpos
#               
#        axis = ax.xaxis
#        axis.set_major_locator(mticker.FixedLocator(tick_locs))
#        axis.set_major_formatter(mticker.FixedFormatter(tick_labels))
#        for label in ax.xaxis.get_ticklabels():
#            label.set_rotation(90)        
#        
#    if ylabels is not None:  
#        beginpos = 0.0
#        curlabel = ylabels[0]
#        tick_locs = []
#        tick_labels = []
#        for i in range(len(ylabels)):
#            endpos = float(i)
#                    
#            # the label here is different to the last ones?
#            if ylabels[i] != curlabel or i == (len(ylabels) - 1):
#                tick_labels.append(curlabel)
#                tick_locs.append((endpos + beginpos) / 2.0)
#                curlabel = ylabels[i]
#                beginpos = endpos        
#                      
#        axis = ax.yaxis
#        axis.set_major_locator(mticker.FixedLocator(tick_locs))
#        axis.set_major_formatter(mticker.FixedFormatter(tick_labels))
    
    if outfile is None:
        plt.show()        
    else:
        plt.savefig(outfile, bbox_inches='tight', dpi=150)
        
    plt.close(fig)
    




if __name__ == '__main__':

    pass
