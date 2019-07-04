
#packages
import sys
import os
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
#%matplotlib inline

sys.path.append('Git/')
from assistFunctions import square,polyEquation,getMin,smooth

#initialization
#root = Tk()
#root.update()

# Load data and define RFU/time columns
#load data, with cycles in first column, data in remaining columns, any
#non-numerical data is ignored by the program (we extract numerical data num)
#root.filename =  filedialog.askopenfilename(initialdir = os.getcwd() ,title = "Select raw file",filetypes = (("Excel files","*.xlsx"),("all files","*.*")))
#path = root.filename #filedialog.askopenfilename()
#path = '20190619b_UDAR_cfx96_RFU_raw.xlsx'
#root.destroy()

infopath = input('Raw data file : - [default: current directory]')
infopath = os.getcwd() or infopath

dataraw = pd.ExcelFile(path)
dataraw = dataraw.parse('SYBR')
data = dataraw.values

#cycle time - update this if the time for one cycle on the qPCR machine changes
cycle = input('Seconds per cycle : - [default:27] \n') #seconds/cycle GUI THIS!
if len(cycle) == 0 :
    cycle = 27
else:
    cycle = float(cycle)

#amount to cut due change in fluorescence during heating
cut = input('Fluorescence error cut time : - [default:0] \n')
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
dataconv = data


#delta time
dtime = np.diff(time)
extdtime = np.tile(dtime,(1,m-1))
#define a matrix of times for the first derivative that is the average of
#the two numerical data points subtracted to find the derivative.
timediff = [(times[t]+times[t+1])/2 for t in range(n-1)]

#Initialize matrices and lists
check1,check2,x1,x2,fitrange1,fitrange2 = (np.empty((100,m)) for i in range(6))
locs,pks,H,Pr,W = (np.empty((2,m)) for i in range(5))
co1,co2 = (np.empty((3,m)) for i in range(2))
sdata,first,dfirst = (np.empty((n,m)) for i in range(3))
I1start,I2start,IF1,I1e,I1,IF2,I2e,I2 = ([0]*m for i in range(8))
d2time = np.empty((n-2,m))
sfirst = first
plateau1,plateau2 = (np.empty((2,m)) for i in range(2))

## Fit peaks in the first derivative with a quadratic to determine inflection points
for i in range(m): # 1 to m-1
    #sdata[:,i] = smooth(data[:,i]); why is the data smoothed here?'''
    sdata[:,i] = smooth(data[:,i]) #'''temporary replacement'''
    sdata[:,i] = data[:,i]
    #take the 1st derivative
    first[:,i] = np.gradient(sdata[:,i])
    #first[:,i] = np.diff(sdata[:,i])/dtime
    dfirst[:,i] = np.gradient(first[:,i])
    #dfirst[:,i] = np.diff(first[:,i])
    d2time = np.diff(timediff)

    #smooth the first derivative.  Without this step the peak finder will find peaks
    #that are trivial, even with thresholding.  It does not change the zeros
    sfirst[:,i] = smooth(first[:,i]) #another smoothing'''

    #find the first two peaks, they need to exceed a min peak height and width
    peaks,properties = find_peaks(first[:,i], prominence=15,width=3)
    l = peaks
    pk = [first[x,i] for x in peaks]
    hi = properties["widths"]
    p = properties["prominences"]
    #    [pk,l,hi,p] = findpeaks(first(:,i),'SortStr','descend','MinPeakProminence',15,'MinPeakWidth',3,'WidthReference','halfprom')

    #Pick the biggest two peaks, then determine which occurs first and put
    #it first (location(first peak, second peak)
    if len(pk)==1:
        locs[:,i] = [l[0],0]
        pks[:,i] = [pk[0],0]
        H[:,i] = [hi[0],0]
        Pr[:,i] = [p[0],0]
        IF2[i] = 0
        co2[:,i] = [0,0,0]
        I2e[i] = 0
        I2start[i] = 0
        I2[i] = 0
    else:
        locs[:,i] = [l[0],l[1]]
        pks[:,i] = [pk[0],pk[1]]
        H[:,i] = [hi[0],hi[1]]
        Pr[:,i] = [p[0],p[1]]

    #take the width of the peak, make it an integer, divide in half, and
    #add two to get a region to fit over
    W[:,i] = np.round(H[:,i],0)/2 #this is the half width
    for j in range(1,2):
        if W[j,i] > 32:
            W[j,i] = np.floor(W[j,i]/1.5)
        if W[j,i] < 2:
            W[j,i] = 2

    #fit the first and second peaks using the location of the peak
    #(inflection point) and fitting over the peak half width.
    #fit to a quadratic polynomial, 2D (y = ax^2+bx+c)
    polyDegree = 2
    b1 = int(locs[0,i]-W[0,i])
    if b1 == 0:
        b1 = 1
    xrange1 = [i for i in range(b1,int(locs[0,i]+W[0,i]))]
    x1[:len(xrange1),i] = xrange1
    fitd = np.polyfit(timediff[xrange1[0]:xrange1[-1]],first[xrange1[0]:xrange1[-1],i],polyDegree)
    if locs[1,i] != 0:
        xrange2 = [i for i in range(int(locs[1,i]-W[1,i]),int(locs[1,i]+W[1,i]))]
        x2[:len(xrange2),i] = xrange2
        fitd2 = np.polyfit(timediff[xrange2[0]:xrange2[-1]],first[xrange2[0]:xrange2[-1],i],polyDegree)
        co2[:,i] = fitd2
        check2[:len(xrange2)-1,i] = polyEquation(co2[:,i],timediff[xrange2[0]:xrange2[-1]])
        fitrange2[:len(xrange2)-1,i] = first[xrange2[0]:xrange2[-1],i]
        IF2[i] = -co2[1,i]/(2*co2[0,i])

        Y,I2[i] = getMin(times,IF2[i])

        #find where the second rise begins in the first derivative data
        I2e[i] = locs[0,i]-W[0,i]  #start below the second peak in the smoothed first derivative, find where the rise begins

        while sfirst[int(I2e[i]),i]>sfirst[int(I2e[i]-1),i] and sfirst[int(I2e[i])-1,i]>sfirst[int(I2e[i])-2,i] and sfirst[int(I2e[i]),i]>0 and sfirst[int(I2e[i])-1,i]>0:
            I2e[i] -= -1

        #find where the rise begins (index) in the data
    Y,I2start[i] = getMin(times,timediff[int(I2e[i])])

    #retrieve the fitting coefficients, co1(1,:) = a, co1(2,:) = b, co1(3,:) = c for peak 1
    co1[:,i] = fitd
    check1[:len(xrange1)-1,i] = polyEquation(co1[:,i],timediff[xrange1[0]:xrange1[-1]])
    fitrange1[:len(xrange1)-1,i] = first[xrange1[0]:xrange1[-1],i]
    #IF1 = first inflection point
    IF1[i] = -co1[1,i]/(2*co1[0,i])

    #find the closest time index in the data (times) to the inflection points
    Y,I1[i] = getMin(times,IF1[i])

    #find the best place to start fitting data on the first rise, in first
    #derivative indices by looking for where the first derivative no longer
    #is increasing (two points in a row)
    I1e[i] = locs[0,i]
    if I1e[i]>2:
        I1e[i] = int(I1e[i] - np.floor(W[0,i]/2))
        while sfirst[I1e[i],i]>sfirst[I1e[i]-1,i] and sfirst[I1e[i]-1,i]>sfirst[I1e[i]-2,i] and I1e[i]>2 and sfirst[I1e[i],i]>0 and sfirst[I1e[i]-1,i]>0:
            I1e[i] = I1e[i]-1
            if I1e[i] == 2:
                I1e[i] = 1
                break


    #find where the first rise begins, index in the data
    Y,I1start[i] = getMin(times,timediff[I1e[i]])

    #clear mins test pk l hi p xrange1 xrange2

#background correct data
BG = [0]*m
for j in range(m):
    if I1start[j] == 0:
        BG[j] = dataconv[0,j]
    elif I1start[j]<10:
        BG[j] = dataconv[1,j]
    else:
        #index out of bounds eror:
        BG[j] = np.nanmean([dataconv[int(I1start[j]-i),j] for i in range(1)])
    dataconv[:,j] = dataconv[:,j]-BG[j]

#find first plateau level
for j in range(m):
    if locs[1,j] != 0:
        plateau1[:,j] = np.nanmean([dataconv[I2start[j]-i,j] for i in range(3)])
    else:
        plateau1[:,j] = 0


#Calculate the final RFU for all points
plateau2 = dataconv #[L-1,:]

#find max first derivative at each phase
index = [(int(j),i) for i,j in enumerate(locs[0,:])]
Max1 = [first[int(j),i] for i,j in enumerate(locs[0,:])]
if locs[1,1]!=0:
    Max2 = [first[int(j),i] for i,j in enumerate(locs[1,:])]
else:
    Max2 = np.zeros((1,m-1))


#Get labels
infopath = input('Experiment info file : - [default: current directory]')
infopath = infopath or os.getcwd()
for file in os.listdir(infopath):
    if file.endswith('Info.xlsx'):
        infopath = infopath + file
        break

#infopath = path + '20190619b_UDAR_miR223-3p_cfx96_Experiment Info.xlsx'
labelraw = pd.ExcelFile(infopath)
labelraw = labelraw.parse('0')
label = labelraw.values
txtLabel = label[:,4]+'_'+label[:,5]
for i,item in enumerate(txtLabel):
    if i<int(label.shape[0]/2):
        txtLabel[i] = item +'_1'
    else:
        txtLabel[i] = item + '_2'

## Write data to an excel file
workbook = xlsxwriter.Workbook(path[:-8]+'AnalysisOutput.xlsx')
worksheet = workbook.add_worksheet('InflectionPoints.xlsx')

label = [' ','Inflection 1 (min)','Inflection 2 (min)','Max derivative 1 RFU/min)','Max derivative 2 RFU/min)','Plateau 1 (RFU)','Plateau 2 (RFU)']

for i,item in enumerate(label):
    worksheet.write(i, 0, item)
    worksheet.write(i + 10, 0, item)

col,r = (0 for i in range(2))
for j,item in enumerate(IF1):
    col += 1
    if j == 33:
        col = 1
        r = r + 10
    worksheet.write(r,col,txtLabel[j])
    worksheet.write(r+1,col,IF1[j]/60)
    worksheet.write(r+2,col,IF2[j]/60)
    worksheet.write(r+3,col,Max1[j]/60)
    worksheet.write(r+4,col,Max2[j]/60)
    worksheet.write(r+5,col,plateau1[0,j])
    worksheet.write(r+6,col,plateau2[1,j])
    #worksheet.write(10,1,[IF1[1]/60,IF2[1]/60,Max1[1]/60,plateau1[1],plateau2[1]])

worksheet.set_column(0,40)

datasheet = workbook.add_worksheet('Data.xlsx')
for i in range(m):
    datasheet.write(0,i,txtLabel[i])
col = 1
for row, data in enumerate(times):
    datasheet.write(row+1, col, data)
row = 1
for col, data in enumerate(dataconv):
    datasheet.write_column(row, col+1, data)

workbook.close()
