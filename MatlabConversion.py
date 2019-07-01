[2
#packages
from tkinter import filedialog
from tkinter import *
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

#initialization
root = Tk()

# Load data and define RFU/time columns
#load data, with cycles in first column, data in remaining columns, any
#non-numerical data is ignored by the program (we extract numerical data num)
root.filename =  filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("Excel files","*.xlsx"),("all files","*.*")))
path = root.filename #filedialog.askopenfilename()

dataraw = pd.ExcelFile(path)
dataraw = dataraw.parse('SYBR')
data = dataraw.values

#cycle time - update this if the time for one cycle on the qPCR machine changes
cycle = input('Seconds per cycle : - [default:27] \n') #seconds/cycle GUI THIS!
if len(cycle) == 0 :
    cycle = 27

#amount to cut due change in fluorescence during heating
cut = input('Fluorescence error cut time : - [default:0] \n')
if len(cut) == 0:
    cut = 0

#remove the error cut time, and separate time
time = data[cut:,1]
times = time * cycle

data = data[cut:,1:];
[n,m] = data.shape

'''not used elsewhere:
#convert data
L = data.shape[0];
# conv = cref/data(L,1);
dataconv = data;
'''

#delta time
dtime = np.diff(time);
'''extdtime = dtime * np.ones(shape=(1,m-1)) <- doesn't get called anywhere'''
#define a matrix of times for the first derivative that is the average of
#the two numerical data points subtracted to find the derivative.
timediff = [(times[t]+times[t+1])/2 for t in range(n-1)]

#Initialize matrices and lists
check1,check2,x1,x2,fitrange1,fitrange2 = (np.empty((50,m)) for i in range(6))
sdata,locs,pks,H,Pr,co2 = (np.empty((n,m)) for i in range(6))
first = np.empty((n-1,m))
IF2,I2e,I2 = ([] for i in range(3))
dfirst,d2time = (np.empty((n-2,m)) for i in range(2))
sfirst = first

i = 1
## Fit peaks in the first derivative with a quadratic to determine inflection points
for i in range(m-1): # 1 to m-1
    '''sdata[:,i] = smooth(data[:,i]); why is the data smoothed here?'''
    sdata[:,i] = data[:,i] #'''temporary replacement'''
    #take the 1st derivative
    first[:,i] = np.diff(sdata[:,i])/dtime
    dfirst[:,i] = np.diff(first[:,i])
    d2time = np.diff(timediff)
    #smooth the first derivative.  Without this step the peak finder will
    #find peaks that are trivial, even with thresholding.  It does not
    #change the zeros
    '''sfirst[:,i] = smooth(first[:,i]) another smoothing'''
    sfirst[:,i] = first[:,i]

    #find the first two peaks, they need to exceed a min peak height and width
    peaks,properties = find_peaks(first[:,i], prominence=15, width=3)
    pk = properties["peak_heights"]
    l = peaks
    hi = properties["width_heights"]
    p = properties["prominences"]

    #    [pk,l,hi,p] = findpeaks(first(:,i),'SortStr','descend','MinPeakProminence',15,'MinPeakWidth',3,'WidthReference','halfprom')

    #Pick the biggest two peaks, then determine which occurs first and put
    #it first (location(first peak, second peak)
    if len(pk)==1:
        locs[:,i] = [l[1],0]
        pks[:,i] = [pk[1],0]
        H[:,i] = [hi[1],0]
        Pr[:,i] = [p[1],0]
        IF2[i] = 0
        co2[:,i] = [0,0,0]
        I2e[i] = 0
        I2start[i] = 0
        I2[i] = 0
    else:
        if l[1]>l[2]:
            locs[:,i] = [l[2],l[1]]
            pks[:,i] = [pk[2],pk[1]]
            H[:,i] = [hi[2],hi[1]]
            Pr[:,i] = [p[2],p[1]]
        else:
            locs[:,i] = [l[1],l[2]]
            pks[:,i] = [pk[1],pk[2]]
            H[:,i] = [hi[1],hi[2]]
            Pr[:,i] = [p[1],p[2]]

    #take the width of the peak, make it an integer, divide in half, and
    #add two to get a region to fit over
    W[:,i] = round(H[:,i]/2,0)-1 #this is the half width
    for j in range(1,2):
        if W[j,i] > 32:
            W[j,i] = np.floor(W[j,i]/1.5)
        if W[j,i] < 2:
            W[j,i] = 2


'''
Stopping point
'''

    #fit the first and second peaks using the location of the peak
    #(inflection point) and fitting over the peak half width.
    #fit to a quadratic polynomial, 2D (y = ax^2+bx+c)
    b1 = locs[1,i]-W[1,i]
    if b1 == 0:
        b1 = 1
    xrange1 = [range(b1,(locs[1,i]+W[1,i]))]
    x1[1:len(xrange1),i] = xrange1
    fitd = fit(timediff(xrange1),first[xrange1,i],'poly2');'''python equivalent?'''
    if locs[2,i] != 0
        xrange2 = [(locs[2,i]-W[2,i]):(locs[2,i]+W[2,i])]
         x2[1:len(xrange2),i] = xrange2
        fitd2 = fit(timediff(xrange2),first[xrange2,i],'poly2')
        co2[:,i] = coeffvalues(fitd2)
        check2[1:len(xrange2),i] = (timediff(xrange2).^2)*co2[1,i]+timediff(xrange2)*co2[2,i]+co2[3,i]
        fitrange2[1:len(xrange2),i] = first[xrange2,i]

        IF2[i] = -co2[2,i]/[2*co2[1,i])
       [Y,I2[i]] = min((times-IF2[i]).^2)

        #find where the second rise begins in the first derivative data
        I2e[i] = locs[2,i]-W[2,i]  #start below the second peak in the smoothed first derivative, find where the rise begins

        while sfirst[I2e[i],i]>sfirst[I2e[i]-1,i] and sfirst[I2e[i]-1,i]>sfirst[I2e[i]-2,i] and sfirst[I2e[i],i]>0 & sfirst[I2e[i]-1,i]>0:
            I2e[i] = I2e[i]-1
        #find where the rise begins (index) in the data
        [Y,I2start[i]] = min((times-timediff(I2e[i])).^2)


    #retrieve the fitting coefficients, co1(1,:) = a, co1[2,:) = b, co1(3,:)
    #= c for peak 1
    co1[:,i] = coeffvalues(fitd)
    check1[1:len(xrange1),i] = (timediff(xrange1).^2)*co1[1,i]+timediff(xrange1)*co1[2,i]+co1[3,i]
    fitrange1[1:len(xrange1),i] = first[xrange1,i]
    #IF1 = first inflection point
    IF1[i] = -co1[2,i]/(2*co1[1,i])


    #find the closest time index in the data (times) to the inflection points
    [Y,I1[i]] = min((times-IF1[i]).^2)

    #find the best place to start fitting data on the first rise, in first
    #derivative indices by looking for where the first derivative no longer
    #is increasing (two points in a row)
    I1e[i] = locs[1,i]
     if I1e[i]>2:
         I1e[i] = I1e[i] - np.floor(W[1,i]/2)
        while sfirst[I1e[i],i]>sfirst[I1e[i]-1,i] & sfirst[I1e[i]-1,i]>sfirst[I1e[i]-2,i] &
                I1e[i]>2 & sfirst[I1e[i],i]>0 &sfirst[I1e[i]-1,i]>0:
            I1e[i] = I1e[i]-1
            if I1e[i] == 2:
                I1e[i] = 1
                break


    #find where the first rise begins, index in the data
    [Y,I1start[i]] = min((times-timediff(I1e[i])).^2)



    #clear mins test pk l hi p xrange1 xrange2


## Plot results
#check rough and fitted inflection points on the first derivative,
#calculate the value of y given the inflection point (x).
y1 = (co1[1,:].*IF1.^2+co1[2,:].*IF1+co1[3,:]) #max first derivative, first rise (in RFU/s)
y2 = (co2[1,:].*IF2.^2+co2[2,:].*IF2+co2[3,:]) #max first derivative, second rise (in RFU/s)
plot(timediff,first)
title('1st Derivatives with Inflection Points')
hold on
plot(IF1,y1,'o')
plot(IF2,y2,'o')
hold off
figure(2)
plot(first)
hold on
plot(locs,pks,'o')
title('1st Derivatives with Rough Inflection Points')
hold off

#background correct data
for j in range(1,m-1):
    if I1start[j] == 1:
        BG[j] = dataconv[1,j]
    elif I1start[j]<10:
        BG[j] = dataconv[2,j]
    else
        BG[j] = mean(dataconv[I1start[j],j],dataconv[I1start[j]-1,j])
    dataconv[:,j] = dataconv[:,j]-BG[j]

#find first plateau level
for j in range(1,m-1):
    if locs[2,j] != 0:
    plateau1[:,j] = mean([dataconv[I2start[j]-2,j],dataconv[I2start[j]-1,j],dataconv[I2start[j],j]]);
    else
        plateau1(:,j) = 0

figure(3)
for j in range(1,m-1):
    plt.plot(times[I1start[j]:I1[j]],dataconv[I1start[j]:I1[j],j])
title('Fitting Region, Phase I')
plt.show()

if locs[2,1] != 0:
    figure(4)
    for j in range(1,m-1):
        if I2start>0:
        plt.plot(times[I2start[j]:I2[j]],dataconv[I2start[j]:I2[j],j])
    title('Fitting Region, Phase II')
    plt.show()


#plot the fit over the peak for the first derivative
figure(5)
plot(x1,check1,'b')
plot(x1,fitrange1,'k')
plt.show()
title('Check fit for inflection point 1')

#plot the fit over the peak for the second derivative
if locs[2,1) != 0
    figure(6)
    plot(x2,check2,'b')
    plot(x2,fitrange2,'k')
    title('Check fit for inflection point 2')
    plt.show()

#plot the background corrected data with the calculated first plateau level
#indicated
figure(7)
for j in range(1,m-1):
    plt.plot(times,dataconv[:,j])
    ax = gca
    ax.ColorOrderIndex = 1+np.floor(j/3)
    legend(TXT[2:m))
    plt.xlabel('Time (s)')
    plt.ylabel('RFU')
    plt.show()
title('Background Corrected Data with plateau levels')

for j in range(1,m-1):
    plt.plot(times, plateau1[j]*np.ones((L,1)),'k')
    plt.ylabel('RFU')
    plt.xlabel('Time (s)')
plt.show()

#Calculate the final RFU for all points
plateau2 = dataconv[L,:]

#find max first derivative at each phase
idx1 = sub2ind(size(first),locs[1,:],[1:len(locs)])
Max1 = first[idx1]
if locs[:,2]!=0:
    idx2 = sub2ind[size(first),locs[2,:],[1:len(locs)]]
    Max2 = first[idx2]
else
    Max2 = np.zeros((1,m-1))

## Write data to an excel file

label = {' ';'Inflection 1 (s)';'Inflection 2 (s)';'Max derivative 1 RFU/s)';'Max derivative 2 (RFU/s)';'Plateau 1 (RFU)';'Plateau 2 (RFU)'};

xlswrite('InflectionPoints.xlsx', label, 'Inflection','A1')
xlswrite('InflectionPoints.xlsx', TXT[2:m],'Inflection','B1')
if locs[2,1]!=0:
    xlswrite('InflectionPoints.xlsx', [IF1;IF2;Max1;Max2;plateau1;plateau2], 'Inflection','B2')
else:
    xlswrite('InflectionPoints.xlsx', [IF1;IF2;Max1;Max2;plateau1;plateau2], 'Inflection','B2')

xlswrite('InflectionPoints.xlsx', TXT[2:m],'Data','B1')
xlswrite('InflectionPoints.xlsx', [times, dataconv],'Data','A2')



'''
SIDE NOTES:

# Alternative python writer:
writer = pd.ExcelWriter('example.xlsx', engine='xlsxwriter')
yourData.to_excel(writer, 'Sheet1')
writer.save()

'''
