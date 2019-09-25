
from scipy.signal import find_peaks
import numpy as np
import xlsxwriter

def GroupByLabel(header,unique):
    if unique:
        indexes = np.unique(header,return_index=True)[1]
        return [header[x] for x in sorted(indexes)]
    else:
        return header

def getTwoPeaks(data): #todo: make this even more flexible
    for proms in range(30,1,-1): # (50,10,-1):
        for width in range(10,1,-1): # (8,1,-1):
            peaks,properties = find_peaks(data, prominence=proms,width=width)
            if len(peaks)==2:
                return peaks,properties
    return [[0,0],0]

def averageTriplicates(data,triplicates,individuals):
    tripAvgs = np.empty((data.shape[0],int(data.shape[1]/3)))
    for row in range(data.shape[0]):
        for trip in triplicates:
            i = int(trip)
            tripData = [data[row,i] for i,j in enumerate(individuals) if j==trip]
            tripAvgs[row,i] = np.nanmean(tripData)
    return tripAvgs

def writeSheet(workbook,name,labels,times,datas):
    datasheet = workbook.add_worksheet(name)
    datasheet.write(0,0,'Cycle')
    datasheet.write(0,1,'Time (Sec)')
    datasheet.write(0,2,'Time (Min)')
    for i in range(len(labels)):
        datasheet.write(0,i+3,labels[i])
    col = 0
    for row, data in enumerate(times):
        datasheet.write(row+1, col, data/27)
        datasheet.write(row+1,col+1,data)
        datasheet.write(row+1,col+2,data/60)
    row = 1
    for col in range(datas.shape[1]):
        for row in range(datas.shape[0]):
            datasheet.write(row+1, col+3, datas[row,col])
    return workbook

def ind2sub(array_shape, ind):
    ind[ind < 0] = -1
    ind[ind >= array_shape[0]*array_shape[1]] = -1
    rows = (ind.astype('int') / array_shape[1])
    cols = ind % array_shape[1]
    return (rows, cols)

def square(list):
    return [i ** 2 for i in list]

def polyEquation(timelist,observed,timepoint):
    polynomial = 2
    coef = np.polyfit(timelist,observed,polynomial)
    if timepoint is None:
        time = timelist
    else:
        time = timepoint
    x2 = square(time)
    ax2 = [coef[0]*x for x in x2]
    bx = [coef[1]*x for x in time]
    predictions = [(a+b+coef[2]) for (a,b) in zip(ax2,bx)]
    return [predictions,coef]

def stillIncreasing(id,line):
    keepMoving = True
    if line[id]<=line[id-1]: keepMoving = False
    elif line[id-1]<=line[id-2]: keepMoving = False
    elif line[id]<=0: keepMoving = False
    elif line[id-1]<=0: keepMoving = False
    return keepMoving

def getMin(time,inflectionList):
    minIndex = np.argmin(square(time-inflectionList))
    minValue = (time[minIndex]-inflectionList)**2
    return minValue,minIndex

def smooth(a):
    # a: NumPy 1-D array containing the data to be smoothed
    # WSZ: smoothing window size needs, which must be odd number,
    # as in the original MATLAB implementation
    WSZ = 5
    out0 = np.convolve(a,np.ones(WSZ,dtype=int),'valid')/WSZ
    r = np.arange(1,WSZ-1,2)
    start = np.cumsum(a[:WSZ-1])[::2]/r
    stop = (np.cumsum(a[:-WSZ:-1])[::2]/r)[::-1]
    return np.concatenate((  start , out0, stop  ))

nope = False
if nope:
    '''Plots are collected here'''
    ## Plot results
    #check rough and fitted inflection points on the first derivative,
    #calculate the value of y given the inflection point (x).
    x1 = [IF1[j] for j in range(m-1) if IF1[j]>0]
    y1 = [co1[0,j]*IF1[j]**2+co1[1,j]*IF1[j]+co1[2,j] for j in range(m-1) if IF1[j]>0] #max first derivative, first rise (in RFU/s)
    x2 = [IF2[j] for j in range(m-1) if IF2[j]>0]
    y2 = [co2[0,j]*IF2[j]+co2[1,j]*IF2[j]+co2[2,j] for j in range(m-1) if IF2[j]>0] #max first derivative, second rise (in RFU/s)
    plt.plot(timediff,first[:-1])
    plt.title('1st Derivatives with Inflection Points')
    plt.plot(x1,y1,'o')
    plt.plot(x2,y2,'o')
    plt.show()

    plt.plot(locs,pks,'o')
    plt.title('1st Derivatives with Rough Inflection Points')
    plt.show()

    for j in range(m-1):
        plt.plot(times[I1start[j]:I1[j]],dataconv[I1start[j]:I1[j],j])
    plt.title('Fitting Region, Phase I')
    plt.show()

    for j in range(m-1):
        if I2start[j]>0:
            plt.plot(times[I2start[j]:I2[j]],dataconv[I2start[j]:I2[j],j])
    plt.title('Fitting Region, Phase II')
    plt.show()

    #plot the fit over the peak for the first derivative
    plt.plot(x1,check1,'b')
    plt.plot(x1,fitrange1,'k')
    plt.title('Check fit for inflection point 1')
    plt.show()

    #plot the fit over the peak for the second derivative
    if locs[0,0] != 0:
        plt.plot(x2,check2,'b')
        plt.plot(x2,fitrange2,'k')
        plt.title('Check fit for inflection point 2')
        plt.show()

    #plot the background corrected data with the calculated first plateau level
    #indicated
    for j in range(m-1):
        plt.plot(times,dataconv[:,j])
        #ax = gca
        #ax.ColorOrderIndex = 1+np.floor(j/3)
        plt.xlabel('Time (s)')
        plt.ylabel('RFU')
    plt.title('Background Corrected Data with plateau levels')
    plt.show()

    for j in range(1,m-1):
        plt.plot(times, plateau1[j]*np.ones((L,1)),'k')
        plt.ylabel('RFU')
        plt.xlabel('Time (s)')
    plt.show()



    for well in range(0,9,3):
        plt.plot(data[40:100,well])
        for i in range(4):
            plt.plot(I[i,well]-40,IRFU[i,well],'x')
        plt.plot()

    #testing four inflection points
    xs = 60
    x = [t/27 for t in times[xs:]]
    for well in range(0,9,3):
        plt.scatter([x/27 for x in IF[:,well]],IRFU[:,well])
        #plt.plot(x,first[:,well]*10)
        plt.plot(x,dfirst[xs:,well]*20 + 5000)
        plt.plot(x,data[xs:,well])
        for i in range(1,4):
            plt.axvline(IF[i,well]/27)
        plt.savefig('/Users/KnownWilderness/2019/Coding/Fyr/fourInflections.png')
        plt.plot()
