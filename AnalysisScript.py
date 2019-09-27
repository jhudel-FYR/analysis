import sys
#sys.path.insert(0, '/Users/KnownWilderness/.pyenv/versions/3.7.4/lib/python3.7/site-packages')

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
import seaborn
#%matplotlib inline


sys.path.append('Git/')
from assistFunctions import square,polyEquation,getMin,smooth,writeSheet,getTwoPeaks,stillIncreasing
from assistFunctions import GroupByLabel,averageTriplicates, saveImage, removeBadWells

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
# path = '/Users/KnownWilderness/FYR Diagnostics/FYR-Database - Data Science_Analysis/For Claire to Review/New Analysis Errors/20190918f_AA'
# path = '/Users/KnownWilderness/FYR Diagnostics/FYR-Database - Data Science_Analysis/For Claire to Review/Data Analysis Graphs/20190906b_AA'
# path = '/Users/KnownWilderness/FYR Diagnostics/FYR-Database - Data Science_Analysis/For Claire to Review/Data Analysis Graphs/20190916c_AA'
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

# cycle time - update this if the time for one cycle on the qPCR machine changes
if len(cycle) == 0 :
    cycle = 27 #TODO: twice as many data points in each cycle
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

#graphing data
datagraph = copy.deepcopy(data)

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
locs,pks,H,Pr,plateau,Max = (np.zeros((2,m)) for i in range(6))
Istart,IF,Ie,I,IRFU = (np.zeros((4,m)) for i in range(5))
sdata,first,second = (np.zeros((n,m)) for i in range(3))
d2time = np.zeros((n-2,m))
dLine = []
badWells = []

lastheader = ''
group = -1
triplicateiterator = -1
IndResult = np.zeros((m,16))
GroupResult = np.zeros((int(m/3),26))
previousgroup = 0
triplicateLabel = 0

## Fit peaks in the first derivative with a quadratic to determine inflection points
for i in range(m): # 1 to m-1
    WellResult = {}
    ip = 0
    first[:,i] = smooth(np.gradient(data[:,i]))
    second[:,i] = smooth(np.gradient(first[:,i]))
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
            badWells.append(i)
            break

        locs[:,i] = peaks
        pks[:,i] = [dLine[x] for x in peaks]
        Pr[:,i] = properties["prominences"]

        #find max first derivative at each phase
        if derivative == 1:
            Max[:,i] = [first[int(x),i] for x in locs[:,i]]

        #take the width of the peak, divide in half, this is the half width, no smaller than 4 units
        #TODO: use something different then the generic 4
        W[:] = np.maximum(properties["widths"]/2,2)

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
            if ip == 3:
                if IF[ip,i] < IF[ip-1,i]:
                    IF[ip,i] = 0

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
        triplicateiterator += 1
        triplicateLabel += 1
    group = int(header[i][-2:].replace('_',''))
    lastheader = header[i]

    if group > previousgroup:
            triplicateLabel = 0
            previousgroup = group

    #each row is an individual well, the first column is the triplicate #, the second is the experiment #,
    #following columns are the parameters
    IndResult[i,:4] = [i, triplicateiterator, group, triplicateLabel]
    IndResult[i,4:8] = [x/60 for x in IF[:,i]] #time of inflection points 1 thru 4
    IndResult[i,8:12] = [x for x in IRFU[:,i]] #RFU of inflection points 1 through 4
    IndResult[i,12] = (IF[2,i] - IF[0,i])/60 #diff of inf 1 and 3
    IndResult[i,13] = (IF[3,i] - IF[1,i])/60 #diff of inf 2 and 4
    IndResult[i,14:] = [x/60 for x in Max[:,i]] #max derivative of first and of second derivative


#each row is a triplicate, each column is a variable, avg then std
#first column is group, second column is triplicate
nVars = len(IndResult[0,4:])
Groups = np.unique(IndResult[:,2])
Triplicates = np.unique(IndResult[:,3])
for trip in Triplicates:
    trip = int(trip)
    col = 0
    for var in range(len(IndResult[0,3:])):
        triplicateVars = [k for j,k in enumerate(IndResult[:,var+3]) if IndResult[j,1] == trip]
        if var == 0:
            triplicateVars = [k for j,k in enumerate(IndResult[:,2]) if IndResult[j,1] == trip]
            GroupResult[trip,:2] = [triplicateVars[0],trip]
            col += 2
        else:
            GroupResult[trip,col] = np.nanmean(triplicateVars)
            col += 1
            GroupResult[trip,col] = np.nanstd(triplicateVars)
            col += 1


[k for j,k in enumerate(IndResult[:,var]) if IndResult[j,1] == trip]
#background correct data
BG = [0]*m
for j in range(m):
    if Istart[0,j] < 3:
        BG[j] = dataconv[0,j]
    elif Istart[0,j] < 10:
        BG[j] = dataconv[1,j]
    elif Istart[0,j] < dataconv.shape[0]: #TODO: start of inflection is not calculating correctly
        BG[j] =  np.nanmean([dataconv[int(Istart[0,j])-i,j] for i in range(2)])
    else:
        BG[j] = dataconv[0,j]
    dataconv[:,j] = [i - BG[j] for i in dataconv[:,j]]





## Write data to an excel
workbook = xlsxwriter.Workbook(infopath[:-8]+'_AnalysisOutput2.xlsx', {'nan_inf_to_errors': True})

#Create labels for excel sheet
label = ['Inflection 1','Inflection 2','Inflection 3','Inflection 4']
label.extend(['RFU of Inflection 1 (RFU)','RFU of Inflection 2 (RFU)','RFU of Inflection 3 (RFU)','RFU of Inflection 4 (RFU)'])
label.extend(['Diff of Inf 1 to Inf 3 (min)','Diff of Inf 2 to Inf 4 (min)'])
label.extend(['Max derivative of first phase (RFU/min)','Max derivative of second phase (RFU/min)'])

worksheet = workbook.add_worksheet('Inflections')
col,r = (0 for i in range(2))
for j in range(m): #each experiment
    r = int(IndResult[j,2]-1) * (nVars+2)
    if IndResult[j,2] != IndResult[j-1,2] and j > 0:#reset to left for each experiment
        col = 0
    col += 1
    for var in range(nVars):
        if var == 0: #Well labels only need to be written in first row once
            worksheet.write(r,col,header[j])
        r += 1
        if col == 1: #Variable labels only need to be written in first column once
            worksheet.write(r, 0, label[var])
        worksheet.write(r,col,IndResult[j,var+4]) #Variable value

width= np.max([len(i) for i in label])
worksheet.set_column(0, 0, width)

label = ['Inflection 1 avg','Inflection 1 std','Inflection 2 avg','Inflection 2 std']
label.extend(['Inflection 3 avg','Inflection 3 std','Inflection 4 avg','Inflection 4 std'])
label.extend(['RFU 1 avg','RFU 1 std','RFU 2 avg','RFU 2 std'])
label.extend(['RFU 3 avg','RFU 3 std','RFU 4 avg','RFU 4 std'])
label.extend(['Diff 1 to 3 avg','Diff 1 to 3 std','Diff 2 to 4 avg','Diff 2 to 4 std'])
label.extend(['Max slope phase 1 (avg RFU/min)','Max slope phase 1 (std RFU/min)'])
label.extend(['Max slope phase 2 (avg RFU/min)','Max phase slope 2 (std RFU/min)'])

worksheet = workbook.add_worksheet('Mean Inflections')
col,r = (0 for i in range(2))
for trip in Triplicates: #each triplicate
    j = np.where(GroupResult[:,1] == trip)[0][0]
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

workbook = writeSheet(workbook,'Corr RFU',header,cycle,times,dataconv)
workbook = writeSheet(workbook,'Raw RFU',header,cycle,times,data)
dataAverages = averageTriplicates(data,Triplicates,IndResult[:,1])
workbook = writeSheet(workbook,'Raw RFU avgs',triplicateHeaders,cycle,times,dataAverages)

workbook.close()






################Graphing################

figpath = os.path.join(path,'Graphs')
generictitle = file[:-14] + '_'
try:
    os.mkdir(figpath)
except OSError as exc:
    pass

#seaborn.set_palette("bright")
#TODO: add more colors and keep gray as the first, blue as the last
manualcolors = ["gray", "purple","sienna","olivedrab","pink", "lightgreen", "orange", "skyblue"]
seaborn.set_palette(manualcolors)
seaborn.palplot(seaborn.color_palette(manualcolors))
#seaborn.palplot(seaborn.color_palette())

####RFU averages and individuals, and inflections, by group
df = pd.DataFrame(dict(index=IndResult[:,0],
    triplicate=IndResult[:,3]%8,
    group=IndResult[:,2],
    label=[triplicateHeaders[int(x%8)] for x in IndResult[:,1]],
    inflection1=IndResult[:,4],
    inflection2=IndResult[:,5],
    inflection3=IndResult[:,6],
    inflection4=IndResult[:,7]))
idg = df.melt(id_vars=['triplicate', 'group','label','index'], var_name='inflection')
rdf = pd.DataFrame(data)
rdf.insert(0,'time',times/60)

xaxis = ['Inflection 1','Inflection 2','Inflection 3','Inflection 4']


#individual data by group #colored by triplicate
idf = pd.DataFrame(columns=['time','index','value','triplicate'])
for group in Groups:
    group = int(group)
    title = generictitle + 'Individuals_' + str(group)
    #TODO: create a subdf with the three lines in a triplicate
    for index, triplicate in enumerate(triplicateHeaders):
        if int(triplicate[-1]) == group:
            listIndsInTrip = np.where(IndResult[:,1] == index)
            listIndsInTrip = [elem for elem in listIndsInTrip[0] if elem not in badWells]
            tripdf = rdf[listIndsInTrip]
            tripdf.insert(0,'time',times/60)
            tripdf = tripdf.melt(id_vars = 'time',var_name='index')
            tripdf['triplicate'] = triplicate
            idf = idf.append(tripdf,ignore_index=True,sort=True)
    snsplt = seaborn.lineplot(x='time', y='value', hue='triplicate', units='index',estimator=None, data=idf, linewidth=.7)
    plt.legend(loc='best',fontsize = 'x-small',fancybox=True, framealpha=0.5)
    handles, labels = snsplt.get_legend_handles_labels()
    plt.legend(handles=handles[1:], labels=labels[1:])
    plt.ylabel('RFU')
    plt.xlabel('Time (Min)')
    #plt.show()
    saveImage(plt,figpath,title)


    #average data by group
for group in Groups:
    group = int(group)
    title = generictitle + 'Averages_' + str(group)
    for index, triplicate in enumerate(triplicateHeaders):
        if int(triplicate[-1]) == group:
            listIndsInTrip = np.where(IndResult[:,1] == index)
            listIndsInTrip = [ elem for elem in listIndsInTrip[0] if elem not in badWells]
            subdf = rdf[listIndsInTrip]
            seaborn.lineplot(rdf['time'], subdf.mean(1),label=triplicate,linewidth=.7)
    plt.legend(loc='best',fontsize = 'x-small')
    plt.ylabel('RFU')
    plt.xlabel('Time (Min)')
    #plt.show()
    saveImage(plt,figpath,title)


#inflection data by group
for group in Groups:
    group = int(group)
    title = generictitle + 'Inflections_' + str(group)
    subidg = idg[(idg['group']==group)]
    subidg = removeBadWells(badWells, subidg,'index')
    indplt = seaborn.stripplot(x="inflection", y="value", hue="label",data=subidg, dodge=True, jitter=True, marker='o',s=4,edgecolor='black',linewidth=1)
    indplt.set(xticklabels=xaxis)
    plt.legend(loc='best',fontsize = 'x-small')
    plt.xlabel('')
    plt.ylabel('Time (Min)')
    #plt.show()
    saveImage(plt,figpath,title)


#all data colored by group
adf = pd.DataFrame(columns=['triplicate','group','value'])
title = generictitle + 'Averages_All'
for group in Groups:
    group = int(group)
    for index, triplicate in enumerate(triplicateHeaders):
        if int(triplicate[-1]) == group:
            listIndsInTrip = np.where(IndResult[:,1] == index)
            listIndsInTrip = [ elem for elem in listIndsInTrip[0] if elem not in badWells]
            tripdf = pd.DataFrame(dict(value=rdf[listIndsInTrip].mean(1)))
            tripdf['time'] = times/60
            tripdf['triplicate'] = index
            tripdf['group'] = 'Group ' + str(group)
            adf = adf.append(tripdf,ignore_index=True,sort=True)
snsplt = seaborn.lineplot(x='time', y='value', hue='group', units='triplicate',estimator=None, data=adf, linewidth=.7)
plt.legend(loc='best',fontsize = 'x-small',fancybox=True, framealpha=0.5)
handles, labels = snsplt.get_legend_handles_labels()
plt.legend(handles=handles[1:], labels=labels[1:])
plt.ylabel('RFU')
plt.xlabel('Time (Min)')
#plt.show()
saveImage(plt,figpath,title)



####inflection by number

df = pd.DataFrame(dict(index=IndResult[:,1],
    triplicate=IndResult[:,3]%8,
    triplicateIndex=index,
    group=IndResult[:,2],
    label=[triplicateHeaders[int(x%8)] for x in IndResult[:,1]],
    inf1=IndResult[:,4],
    inf2=IndResult[:,5],
    inf3=IndResult[:,6],
    inf4=IndResult[:,7]))
gd = df.sort_values(by=['triplicate','group'],ascending=True)
gd['triplicateIndex'] = int(gd['group'].max())*df['triplicate']+df['group']
df = removeBadWells(badWells,gd,'index')
numGroups = int(int(gd['group'].max()))
xaxis = [i+1 for i in range(numGroups)]
xaxis =  xaxis * int(len(IndResult[:,0])/(numGroups))
# xaxis[:8]

# xt[:8]
# count = 0
# xt = []
# for idx,group in enumerate(xaxis):
#     if (xaxis[idx]-1)==0 and idx > 0:
#         xt.append('')
#         count += 1
#         xt.append(count)
#     else:
#         xt.append(count)
#     count += 1
for inf in range(4):
    title = generictitle + 'Inflection' + str(inf+1)
    indplt = seaborn.swarmplot(x="triplicateIndex", y='inf'+str(inf+1), hue="label",data=gd, dodge=True,linewidth=1)
    indplt.set(xticklabels=xaxis)
    plt.legend(loc='best',fontsize = 'x-small',fancybox=True, framealpha=0.5)
    plt.ylabel('Time (Min)')
    plt.xlabel('Group Number')
    #plt.show()
    saveImage(plt,figpath,title)
