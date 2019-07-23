
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
from assistFunctions import square,polyEquation,getMin,smooth,writeSheet,getTwoPeaks,stillIncreasing,GroupByLabel

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
#load data, with cycles in first column, data in remaining columns, any
#non-numerical data is ignored by the program (we extract numerical data num)
path = root.filename

# path = '/Users/KnownWilderness/2019/Coding/Fyr'
# cycle = 27
# cut = 0
for file in os.listdir(path):
    if file.endswith('RFU.xlsx'):
        datapath = os.path.join(path,file)
        break

wb = xlrd.open_workbook(datapath)
sheet = wb.sheet_by_name('SYBR')
data = np.empty((sheet.nrows-1,sheet.ncols-1))
for j in range(1,sheet.ncols):
   for i in range(1,sheet.nrows):
       data[i-1,j-1] = sheet.cell_value(i,j)
wb.release_resources()
del wb

# dataraw = pd.ExcelFile(datapath)
# dataraw = dataraw.parse('SYBR')
# ddata = dataraw.values

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
L = data.shape[0]
# conv = cref/data(L,1);
dataconv = copy.deepcopy(data)

#delta time
dtime = np.diff(time)
extdtime = np.tile(dtime,(1,m-1))
#define a matrix of times for the first derivative that is the average of
#the two numerical data points subtracted to find the derivative.
timediff = [(times[t]+times[t+1])/2 for t in range(n-1)]

#Initialize matrices and lists
polyDegree = 2
W = np.empty(2)
locs,pks,H,Pr,plateau = (np.empty((2,m)) for i in range(5))
Istart,IF,Ie,I,Max,IRFU = (np.empty((4,m)) for i in range(6))
sdata,first,second = (np.empty((n,m)) for i in range(3))
d2time = np.empty((n-2,m))
dLine = []

## Fit peaks in the first derivative with a quadratic to determine inflection points
for i in range(m): # 1 to m-1
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
            dLine = -(second[:,i])

        #find the first two peaks, they need to exceed a min peak height and width
        #peaks,properties = getTwoPeaks(first[:,i])
        peaks,properties = getTwoPeaks(abs(dLine[:]))
        if peaks[0]== 0 and peaks[1] == 0:
            print('Peaks could not be found in well:',i+1, 'Derivative:',derivative)
            continue
        locs[:,i] = peaks
        pks[:,i] = [dLine[x] for x in peaks]
        Pr[:,i] = properties["prominences"]

        #take the width of the peak, make it an integer, divide in half, and
        #add two to get a region to fit over
        W[:] = np.maximum(properties["widths"]/2,4) #this is the half width, no smaller than 4 units

        for k in range(2):
            #fit the first and second peaks using the location of the peak
            #(inflection point) and fitting over the peak half width.
            #fit to a quadratic polynomial, 2D (y = ax^2+bx+c)
            xStart = np.maximum(int(locs[k,i]-W[k]),1)
            xEnd = int(locs[k,i]+W[k])
            xRange = xEnd-xStart

            #fit a polynomial to the first derivative and retrieve the zero
            fitd = np.polyfit(timediff[xStart:xEnd],dLine[xStart:xEnd],polyDegree)
            check =  polyEquation(fitd,timediff[xStart:xEnd])
            fitrange = dLine[xStart:xEnd]
            IF[ip,i] = -fitd[1]/(2*fitd[0])

            #retrieve the calculated RFU at the inflection point:
            fito = np.polyfit(times[xStart:xEnd],data[xStart:xEnd,i],polyDegree)
            IRFU[ip,i] = polyEquation(fito,[IF[ip,i]])[0]

            #find the closest time index in the data (times) to the inflection points
            Y,I[ip,i] = getMin(times,IF[ip,i])

            #find where the second rise begins in the first derivative data
            Ie[ip,i] = xStart  #start below the second peak in the smoothed first derivative, find where the rise begins
            while stillIncreasing(int(Ie[ip,i]),dLine):
                Ie[ip,i] -= -1

            Y,Istart[ip,i] = getMin(times,timediff[int(Ie[ip,i])])

            #find the best place to start fitting data on the first rise, in first
            #derivative indices by looking for where the first derivative stops increasing
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

            #find max first derivative at each phase
            Max[k,i] = first[int(locs[k,i]),i]
            ip += 2

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
expIndividual = [int(i[-2:].replace('_','')) for i in header]
indIndex = np.unique(expIndividual,return_index=True)[1]
expGroups = [int(i[-2:].replace('_','')) for i in header]
groupIndex = np.unique(expGroups,return_index=True)[1]
## Write data to an excel

workbook = xlsxwriter.Workbook(infopath[:-8]+'_AnalysisOutput.xlsx')
worksheet = workbook.add_worksheet('Inflections')
label = ['','Inflection 1 (min)','Inflection 2 (min)','Inflection 3 (min)','Inflection 4 (min)']
label.extend(['RFU of Inflection 1 (RFU)','RFU of Inflection 2 (RFU)','RFU of Inflection 3 (RFU)','RFU of Inflection 4 (RFU)'])
label.extend(['Max derivative 1 (RFU/min)','Max derivative 2 (RFU/min)'])

col,r = (0 for i in range(2))
bumpGroup = 1
for j,item in enumerate(IF[0,:]):
    if j<len(label):
        worksheet.write(j, 0, label[j])
        worksheet.write(j + 12 * bumpGroup, 0, label[j])
    col += 1
    if j in indIndex and j > 0:
        col = 1
        r = r + 12 * bumpGroup
        bumpGroup += 1
    for k in range(4):
        worksheet.write(r,col,header[j])
        worksheet.write(r+1+k,col,IF[k,j]/60)
        worksheet.write(r+5+k,col,IRFU[k,j])
        if k < 2:
            worksheet.write(r+9+k,col,Max[k,j]/60)
width= np.max([len(i) for i in label])
worksheet.set_column(0, 0, width)

worksheet = workbook.add_worksheet('Mean Inflections')
label = [' ','Inflection 1 avg','Inflection 2 avg','Inflection 3 avg','Inflection 4 avg']
label.extend(['Inflection 1 std','Inflection 2 std','Inflection 3 std','Inflection 4 std'])
label.extend(['Max derivative 1 (avg RFU/min)','Max derivative 2 (avg RFU/min)'])
label.extend(['Max derivative 1 (std RFU/min)','Max derivative 2 (std RFU/min)'])

col,r,h = (0 for i in range(3))
bumpGroup = 1
for j in range(len(IF[0,:])):
    h = col%len(triplicateHeaders)
    if j<len(label):
        worksheet.write(j, 0, label[j])
        worksheet.write((j + 15 * bumpGroup), 0, label[j])
    #if j in splitGroupIndex and j>0:
    if j in groupIndex and j > 0:
        col = 0
        r = r + 15 * bumpGroup
        bumpGroup += 1
    col += 1
    worksheet.write(r,col,triplicateHeaders[h])
    for k in range(4):
        worksheet.write(r+1+k,col,np.nanmean([IF[k,j-i]/60 for i,hdr in enumerate(IF[0,:]) if header[i] == triplicateHeaders[h]]))
        worksheet.write(r+5+k,col,np.nanstd([IF[k,j-i]/60 for i,hdr in enumerate(IF[0,:]) if header[i] == triplicateHeaders[h]]))
        if k < 2:
            worksheet.write(r+9+k,col,np.nanmean([Max[k,j-i]/60 for i,hdr in enumerate(IF[0,:]) if header[i] == triplicateHeaders[h]]))
            worksheet.write(r+11+k,col,np.nanstd([Max[k,j-i]/60 for i,hdr in enumerate(IF[0,:]) if header[i] == triplicateHeaders[h]]))
worksheet.set_column(0, 0, width)

workbook = writeSheet(workbook,'Corr RFU',header,times,dataconv)
workbook = writeSheet(workbook,'Raw RFU',header,times,data)

worksheet = workbook.add_worksheet('Inflections (in Cycles)')
label = ['','Inflection 1 (Cycles)','Inflection 2 (Cycles)','Inflection 3 (Cycles)','Inflection 4 (Cycles)']
label.extend(['RFU of Inflection 1 (RFU)','RFU of Inflection 2 (RFU)','RFU of Inflection 3 (RFU)','RFU of Inflection 4 (RFU)'])
label.extend(['Max derivative 1 (RFU/Cycles)','Max derivative 2 (RFU/Cycles)'])

col,r = (0 for i in range(2))
bumpGroup = 1
for j,item in enumerate(IF[0,:]):
    if j<len(label):
        worksheet.write(j, 0, label[j])
        worksheet.write(j + 12 * bumpGroup, 0, label[j])
    col += 1
    if j in indIndex and j > 0:
        col = 1
        r = r + 12 * bumpGroup
        bumpGroup += 1
    for k in range(4):
        worksheet.write(r,col,header[j])
        worksheet.write(r+1+k,col,IF[k,j]/27)
        worksheet.write(r+5+k,col,IRFU[k,j])
        if k < 2:
            worksheet.write(r+9+k,col,Max[k,j]/27)
width= np.max([len(i) for i in label])
worksheet.set_column(0, 0, width)

workbook.close()
