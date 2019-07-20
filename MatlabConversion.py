
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

sys.path.append('Git/')
from assistFunctions import square,polyEquation,getMin,smooth,writeSheet,getTwoPeaks

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
sdata,first,dfirst = (np.empty((n,m)) for i in range(3))
d2time = np.empty((n-2,m))

## Fit peaks in the first derivative with a quadratic to determine inflection points
for i in range(m): # 1 to m-1
    #sdata[:,i] = smooth(data[:,i])
    first[:,i] = smooth(np.gradient(data[:,i]))
    dfirst[:,i] = np.gradient(first[:,i])
    d2time = np.diff(timediff)

    for ip in range(4):
        if ip<2: peaks,properties = getTwoPeaks(first[:,i])
        elif ip>=2:peaks,properties = getTwoPeaks(abs(dfirst[:,i]))

        #find the first two peaks, they need to exceed a min peak height and width
        #peaks,properties = getTwoPeaks(first[:,i])

        if peaks[0]== 0 and peaks[1] == 0:
            print('Peaks could not be found in well:',i+1, 'Derivative:',ip)
            continue
        k = ip % 2
        locs[:,i] = peaks
        pks[:,i] = [first[x,i] for x in peaks]
        H[:,i] = properties["widths"]
        Pr[:,i] = properties["prominences"]

        #take the width of the peak, make it an integer, divide in half, and
        #add two to get a region to fit over
        W[:] = np.maximum(np.round(H[:,i],0)/2,4) #this is the half width, no smaller than 4 units

        #fit the first and second peaks using the location of the peak
        #(inflection point) and fitting over the peak half width.
        #fit to a quadratic polynomial, 2D (y = ax^2+bx+c)

        xStart = np.maximum(int(locs[k,i]-W[k]),1)
        xEnd = int(locs[k,i]+W[k])
        xRange = xEnd-xStart

        #fit a polynomial to the first derivative and retrieve the zero
        fitd = np.polyfit(timediff[xStart:xEnd],first[xStart:xEnd,i],polyDegree)
        check =  polyEquation(fitd,timediff[xStart:xEnd])
        fitrange = first[xStart:xEnd,i]
        IF[ip,i] = -fitd[1]/(2*fitd[0])

        #retrieve the calculated RFU at the inflection point:
        fito = np.polyfit(times[xStart:xEnd],data[xStart:xEnd,i],polyDegree)
        IRFU[ip,i] = polyEquation(fito,[IF[ip,i]])[0]

        #find the closest time index in the data (times) to the inflection points
        Y,I[ip,i] = getMin(times,IF[ip,i])

        #find where the second rise begins in the first derivative data
        Ie[ip,i] = locs[0,i]-W[0]  #start below the second peak in the smoothed first derivative, find where the rise begins
        while first[int(Ie[ip,i]),i]>first[int(Ie[ip,i]-1),i] and first[int(Ie[ip,i])-1,i]>first[int(Ie[ip,i])-2,i] and first[int(Ie[ip,i]),i]>0 and first[int(Ie[ip,i])-1,i]>0:
            Ie[ip,i] -= -1

        Y,Istart[ip,i] = getMin(times,timediff[int(Ie[ip,i])])

        #find the best place to start fitting data on the first rise, in first
        #derivative indices by looking for where the first derivative stops increasing
        Ie[ip,i] = locs[0,i]
        if Ie[ip,i]>2:
            Ie[ip,i] = int(Ie[ip,i] - np.floor(W[0]/2))
            id = int(Ie[ip,i])
            while id>2 and first[id,i]>first[id-1,i] and first[id-1,i]>first[id-2,i] and first[id,i]>0 and first[id-1,i]>0:
                Ie[ip,i] = Ie[ip,i]-1
                if Ie[ip,i] == 2:
                    Ie[ip,i] = 1
                    break

        #find where the first rise begins, index in the data
        Y,Istart[ip,i] = getMin(times,timediff[int(Ie[ip,i])])

        #find max first derivative at each phase
        Max[k,i] = first[int(locs[k,i]),i]

#background correct data
BG = [0]*m
for j in range(m):
    if Istart[0,j] < 2:
        BG[j] = dataconv[0,j]
    elif Istart[0,j]<10:
        BG[j] = dataconv[1,j]
    else:
        BG[j] =  np.nanmean([dataconv[int(Istart[0,j])-i,j] for i in range(2)])
    dataconv[:,j] = [i - BG[j] for i in data[:,j]]

# #find first plateau level - not being used currently
# for j in range(m):
#     for k in range(2):
#         plateau[k,j] = np.nanmean([dataconv[int(Istart[k,j])-i,j] for i in range(2)])


#Get info file
for file in os.listdir(path):
    if file.endswith('INFO.xlsx'):
        infopath = os.path.join(path,file)
        break
#infopath = path + '20190619b_UDAR_miR223-3p_cfx96_Experiment Info.xlsx'

#Get labels
labelraw = pd.ExcelFile(infopath)
labelraw = labelraw.parse('0')
label = labelraw.values
txtLabel = label[:,17]
split = int(label.shape[0]/2)

## Write data to an excel file
workbook = xlsxwriter.Workbook(infopath[:-8]+'_AnalysisOutput.xlsx')

worksheet = workbook.add_worksheet('Inflections')
label = [' ','Inflection 1 (min)','Inflection 2 (min)','RFU of Inflection 1','RFU of Inflection 2','Max derivative 1 (RFU/min)','Max derivative 2 (RFU/min)']

for i,item in enumerate(label):
    worksheet.write(i, 0, item)
    worksheet.write(i + 10, 0, item)

col,r = (0 for i in range(2))
for j,item in enumerate(IF[0,:]):
    col += 1
    if j == split:
        col = 1
        r = r + 10
    for k in range(2):
        worksheet.write(r,col,txtLabel[j])
        worksheet.write(r+1+k,col,IF[k,j]/60)
        worksheet.write(r+3+k,col,IRFU[k,j])
        worksheet.write(r+5+k,col,Max[k,j]/60)
        #worksheet.write(r+7+k,col,plateau[k,j])
width= np.max([len(i) for i in label])
worksheet.set_column(0, 0, width)


worksheet = workbook.add_worksheet('Mean Inflections')
label = ['','Inflection 1 (avg/min)','Inflection 2 (avg/min)','Inflection 1 (std/min)','Inflection 2 (std/min)',
'Max derivative 1 (avg RFU/min)','Max derivative 2 (avg RFU/min)','Max derivative 1 (std RFU/min)','Max derivative 2 (std RFU/min)']

for i,item in enumerate(label):
    worksheet.write(i, 0, item)
    worksheet.write(i + 10, 0, item)

col,r = (0 for i in range(2))
for j,item in enumerate(IF[0,:]):
    if j == split:
        col = 0
        r = r + 10
    if j % 3 == 0:
        col += 1
        worksheet.write(r,col,txtLabel[j])
        for k in range(2):
            worksheet.write(r+1+(2*k),col,np.nanmean([IF[k,j-i]/60 for i in range(3)]))
            worksheet.write(r+2+(2*k),col,np.nanstd([IF[k,j-i]/60 for i in range(3)]))
            worksheet.write(r+5+(2*k),col,np.nanmean([Max[k,j-i]/60 for i in range(3)]))
            worksheet.write(r+6+(2*k),col,np.nanstd([Max[k,j-i]/60 for i in range(3)]))
worksheet.set_column(0, 0, width)

workbook = writeSheet(workbook,'Corr RFU',txtLabel,times,dataconv)
workbook = writeSheet(workbook,'Raw RFU',txtLabel,times,data)
workbook.close()
