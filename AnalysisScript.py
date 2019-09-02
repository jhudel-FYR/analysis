
#packages
import sys
import os
import copy
import xlrd
import xlsxwriter
from tkinter import *
from tkinter import filedialog
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
#from openpyxl import Workbook
#%matplotlib inline

sys.path.append('Git/')
from assistFunctions import square,polyEquation,getMin,smooth,writeSheet,getTwoPeaks,stillIncreasing
from assistFunctions import GroupByLabel,averageTriplicates

def openFile():
    global e1,e2
    global cycle, cut
    cycle = e1.get()
    cut = e2.get()
    root.filename = filedialog.askdirectory()

def setDialog():
    global e1,e2,root
    root = Tk()
    root.geometry("500x255")
    root.title("Inflection Point Identification")
    Label(root,text="Seconds per cycle : - [default=27]").pack()
    e1 = Entry(root,width=25)
    e1.pack()
    Label(root,text = "Enter fluorescence error cut time : - [default=0]").pack()
    e2 = Entry(root,width=25)
    e2.pack()
    Label(root,text = "Leaving the inputs blank will result in the default values being used.").pack()
    return root

if __name__ == '__main__':
    root = setDialog()
    Button(root, text = "Get Folder", command = openFile).pack()
    Button(root, text="Create Output File",command = root.destroy).pack()
    mainloop()

# Load data and define RFU/time columns
path = root.filename

# path = '/Users/KnownWilderness/2019/Coding/Fyr'
# cycle = 27
# cut = 0
for file in os.listdir(path):
    if file.endswith('RFU.xlsx'):
        datapath = os.path.join(path,file)
        break

#Get info file
for file in os.listdir(path):
    if file.endswith('INFO.xlsx'):
        infopath = os.path.join(path,file)
        break

#Get labels
labelraw = pd.ExcelFile(infopath)
labelsheet = labelraw.parse('0')
label = labelsheet.values
header = label[:,17]
triplicateHeaders = np.asarray(GroupByLabel(header,True))

wb = xlrd.open_workbook(datapath)
sheet = wb.sheet_by_name('SYBR')
data = np.empty((sheet.nrows-1,sheet.ncols-1))
for j in range(1,sheet.ncols):
   for i in range(1,sheet.nrows):
       data[i-1,j-1] = sheet.cell_value(i,j)
wb.release_resources()
del wb

#cycle time - update this if the time for one cycle on the qPCR machine changes
if len(cycle) == 0 :
    cycle = 27
else:
    cycle = float(cycle)

#amount to cut due change in fluorescence during heating
if len(cut) == 0:
    cut = 0
else:
    cut = int(cut)

#remove the error cut time, and separate time
time = data[cut:,0]
times = time * cycle

data = data[cut:,1:]
[n,m] = data.shape

#convert data
dataconv = copy.deepcopy(data)

#delta time
dtime = np.diff(time)
extdtime = np.tile(dtime,(1,m-1))
#define a matrix of times for the first derivative that is the average of
#the two numerical data points subtracted to find the derivative.
timediff = [(times[t]+times[t+1])/2 for t in range(n-1)]

#Initialize matrices and lists
W = np.empty(2)
locs,pks,H,Pr,plateau,Max = (np.empty((2,m)) for i in range(6))
Istart,IF,Ie,I,IRFU = (np.empty((4,m)) for i in range(5))
sdata,first,second = (np.empty((n,m)) for i in range(3))
d2time = np.empty((n-2,m))
dLine = []

lastheader = ''
g = -1
IndResult = np.empty((m,14))
GroupResult = np.zeros((int(m/3),26))

## Fit peaks in the first derivative with a quadratic to determine inflection points
for i in range(m): # 1 to m-1
    WellResult = {}
    ip = 0
    first[:,i] = smooth(np.gradient(data[:,i]))
    second[:,i] = np.gradient(first[:,i])
    d2time = np.diff(timediff)

    for derivative in range(1,3):
        if derivative == 1:
            dLine = first[:,i]
        elif derivative == 2:
            dLine = second[:,i]
            ip = 1
        elif derivative == 3:
            dLine = -(second[:,i]) #flip in order to find the negative peak

        #find the first two peaks
        peaks,properties = getTwoPeaks(abs(dLine[:]))
        if peaks[0]== 0 and peaks[1] == 0:
            print('Peaks could not be found in well:',i+1, 'Derivative:',derivative)
            continue
        locs[:,i] = peaks
        pks[:,i] = [dLine[x] for x in peaks]
        Pr[:,i] = properties["prominences"]

        #find max first derivative at each phase
        if derivative == 1:
            Max[:,i] = [first[int(x),i] for x in locs[:,i]]

        #take the width of the peak, divide in half, this is the half width, no smaller than 4 units
        #TODO: use something different then the generic 4
        W[:] = np.maximum(properties["widths"]/2,4)

        for k in range(2):
            #fit the first and second peaks using the location of the peak
            #(inflection point) and fitting over the peak half width.
            #fit to a quadratic polynomial, 2D (y = ax^2+bx+c)
            xStart = np.maximum(int(locs[k,i]-W[k]),1)
            xEnd = int(locs[k,i]+W[k])
            xRange = xEnd-xStart

            #fit a polynomial to the first derivative and retrieve the zero
            [predictions,fitd] =  polyEquation(timediff[xStart:xEnd],dLine[xStart:xEnd],None)
            IF[ip,i] = -fitd[1]/(2*fitd[0])

            #retrieve the expected RFU at the inflection point:
            [predictions,_] = polyEquation(times[xStart:xEnd],data[xStart:xEnd,i],[IF[ip,i]])
            IRFU[ip,i] = predictions[0]

            #find the closest time index in the data (times) to the inflection points
            Y,I[ip,i] = getMin(times,IF[ip,i])

            #find where the second rise begins in the first derivative data
            Ie[ip,i] = xStart  #start below the second peak in the smoothed first derivative, find where the rise begins
            while stillIncreasing(int(Ie[ip,i]),dLine):
                Ie[ip,i] -= -1

            Y,Istart[ip,i] = getMin(times,timediff[int(Ie[ip,i])])

            #find where the first derivative stops increasing -> to fit data to the first rise
            Ie[ip,i] = int(locs[k,i])
            if Ie[ip,i]>2:
                Ie[ip,i] = int(Ie[ip,i] - np.floor(W[k]/2))
                id = int(Ie[ip,i])
                while stillIncreasing(id,dLine[:]) and id>=2:
                    Ie[ip,i] = Ie[ip,i]-1
                    if Ie[ip,i] == 2:
                        break

            #find where the first rise begins, index in the data
            Y,Istart[ip,i] = getMin(times,timediff[int(Ie[ip,i])])

            ip += 2

    #Retrieve experiment number from label
    if lastheader != header[i]:
        g += 1
    exp = int(header[i][-2:].replace('_',''))
    lastheader = header[i]

    #each row is an individual well, the first column is the triplicate #, the second is the experiment #,
    #following columns are the parameters
    IndResult[i,:2] = [g,exp]
    IndResult[i,2:6] = [x/60 for x in IF[:,i]] #time of inflection points 1 thru 4
    IndResult[i,6:10] = [x for x in IRFU[:,i]] #RFU of inflection points 1 through 4
    IndResult[i,10] = (IF[2,i] - IF[0,i])/60 #diff of inf 1 and 3
    IndResult[i,11] = (IF[3,i] - IF[1,i])/60 #diff of inf 2 and 4
    IndResult[i,12:] = [x/60 for x in Max[:,i]] #max derivative of first and of second derivative

#each row is a triplicate, each column is a variable, avg then std
nVars = len(IndResult[0,2:])
Triplicates = np.unique(IndResult[:,0])
for trip in Triplicates:
    i = int(trip)
    col = 0
    for var in range(len(IndResult[0,:])):
        triplicateVars = [k for j,k in enumerate(IndResult[:,var]) if IndResult[j,0] == i]
        if var < 2:
            GroupResult[i,col] = triplicateVars[0]
            col += 1
        else:
            GroupResult[i,col] = np.nanmean(triplicateVars)
            col += 1
            GroupResult[i,col] = np.nanstd(triplicateVars)
            col += 1

#background correct data
BG = [0]*m
for j in range(m):
    if Istart[0,j] < 3:
        BG[j] = dataconv[0,j]
    elif Istart[0,j]<10:
        BG[j] = dataconv[1,j]
    else:
        BG[j] =  np.nanmean([dataconv[int(Istart[0,j])-i,j] for i in range(2)])
    dataconv[:,j] = [i - BG[j] for i in data[:,j]]





## Write data to an excel
workbook = xlsxwriter.Workbook(infopath[:-8]+'_AnalysisOutput.xlsx')

#Create labels for excel sheet
label = ['Inflection 1 (min)','Inflection 2 (min)','Inflection 3 (min)','Inflection 4 (min)']
label.extend(['RFU of Inflection 1 (RFU)','RFU of Inflection 2 (RFU)','RFU of Inflection 3 (RFU)','RFU of Inflection 4 (RFU)'])
label.extend(['Diff of Inf 1 to Inf 3 (min)','Diff of Inf 2 to Inf 4 (min)'])
label.extend(['Max derivative of first phase (RFU/min)','Max derivative of second phase (RFU/min)'])

worksheet = workbook.add_worksheet('Inflections')
col,r = (0 for i in range(2))
for j in range(m): #each experiment
    r = int(IndResult[j,1]-1) * (nVars+2)
    if IndResult[j,1] != IndResult[j-1,1] and j > 0:#reset to left for each experiment
        col = 0
    col += 1
    for var in range(nVars):
        if var == 0: #Well labels only need to be written in first row once
            worksheet.write(r,col,header[j])
        r += 1
        if col == 1: #Variable labels only need to be written in first column once
            worksheet.write(r, 0, label[var])
        worksheet.write(r,col,IndResult[j,var+2]) #Variable value

width= np.max([len(i) for i in label])
worksheet.set_column(0, 0, width)

label = ['Inflection 1 avg','Inflection 1 std','Inflection 2 avg','Inflection 2 std']
label.extend(['Inflection 3 avg','Inflection 3 std','Inflection 4 avg','Inflection 4 std'])
label.extend(['RFU 1 avg','RFU 1 std','RFU 2 avg','RFU 2 std'])
label.extend(['RFU 3 avg','RFU 3 std','RFU 4 avg','RFU 4 std'])
label.extend(['Diff 1 to 3 avg','Diff 1 to 3 std','Diff 2 to 4 avg','Diff 2 to 4 std'])
label.extend(['Max slope phase 1 (avg RFU/min)','Max slope phase 1 (std RFU/min)'])
label.extend(['Max slope phase 2 (std RFU/min)','Max phase slope 2 (std RFU/min)'])

worksheet = workbook.add_worksheet('Mean Inflections')
col,r = (0 for i in range(2))
for trip in Triplicates: #each triplicate
    j = np.where(GroupResult[:,0] == trip)[0][0]
    r = int(GroupResult[j,1]-1) * (nVars*2+2)
    if GroupResult[j,1] != GroupResult[j-1,1] and j > 0:
        col = 0
    col += 1

    for var in range(nVars*2):
        if var == 0: #Well labels only need to be written in first row once
            worksheet.write(r,col,triplicateHeaders[j])
        r += 1
        if col == 1: #Variable labels only need to be written in first column once
            worksheet.write(r, col-1, label[var])
        worksheet.write(r,col,GroupResult[j,var+2]) #Variable value
width= np.max([len(i) for i in label])
worksheet.set_column(0, 0, width)

workbook = writeSheet(workbook,'Corr RFU',header,times,dataconv)
workbook = writeSheet(workbook,'Raw RFU',header,times,data)
dataAverages = averageTriplicates(data,Triplicates,IndResult[:,0])
workbook = writeSheet(workbook,'Raw RFU avgs',triplicateHeaders,times,dataAverages)

workbook.close()

def averageTriplicates(data,triplicates,individuals):
    tripAvgs = np.empty((data.shape[0],int(data.shape[1]/3)))
    for row in range(data.shape[0]):
        for trip in triplicates:
            i = int(trip)
            tripData = [data[row,i] for i,j in enumerate(individuals) if j==trip]
            tripAvgs[row,i] = np.nanmean(tripData)
    return tripAvgs
