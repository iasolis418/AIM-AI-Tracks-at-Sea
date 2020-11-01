import math
import pandas as pd
from matplotlib import pyplot as plt
from xml.dom import minidom

### This section can parse gpx files into a dataframe with lat,long & time column

filepathXml = 'boatGPS12417.gpx' # ***WARNING:My file name, change to what yours is in directory***

# Opens Gpx file and creates a mini xml tag tree
xml = minidom.parse(filepathXml) 

# sets trkpts to the trkseg node which includes lat/lon attributes and child node with timestamp data
trkpts = xml.getElementsByTagName("trkpt")

# Variables that hold each dataframe column's info
lats=[]
longs=[]
times=[]

# Iterate through trkpts elements and add lats, longs and times to appropriate lists
# trkpts have lat and lon attributes and two child nodes time & ele(elevation), we are
# interested in child 0's (time) data and we want to split it after date and before Z
for trkpt in trkpts:
    lats.append(float(trkpt.attributes["lat"].value))
    longs.append(float(trkpt.attributes["lon"].value))
    times.append(trkpt.getElementsByTagName("time")[0].firstChild.data.split("T")[1].split("Z")[0])

# zips lists together and assigns column names, all to a data frame
trkpts12417Df = pd.DataFrame(list(zip(lats, longs, times)), columns = ['Latitudes','Longitudes','TimeStamps'])
print(trkpts12417Df)

### This section can parse txt files with specific gpx formatting into a dataframe with similar columns

filepathTxt = 'boatGPS1.txt' # ***SAME WARNING AS BEFORE ***

# More Variables for data
latsTxt = []
longsTxt = []
timesTxt = []
lines = []

# Reads through txt file and puts relevant lines in lines list
with open(filepathTxt) as fp:
    for i in range(5):
        fp.readline() #get rid of junk at beginning
    for cnt, line in enumerate(fp):
        lines.append(line)
        #print("{}".format(line)), formatting note for myself

# Adds time lines to time list and add lat/lon to lats & longs lists
for line in lines:
    if len(line) == len(lines[1]):
        timesTxt.append(line.split("T")[1].split("Z")[0])
    elif len(line) == len(lines[0]):
        coords = line.split("\"")
        latsTxt.append(float(coords[1]))
        longsTxt.append(float(coords[3]))

#Another dataframe
trkptsS1Df = pd.DataFrame(list(zip(latsTxt, longsTxt, timesTxt)), columns = ['Latitudes', 'Longitudes', 'TimeStamps'])
print(trkptsS1Df)

# This section takes the camera logs and generates dataframe with appropriate columns
cameraFile = 'all_camera_gps_logs.csv' # ***SAME WARNING AS BEFORE***
cameraPtsDf = pd.read_csv(cameraFile) # reads csv into a dataframe
print(cameraPtsDf)

# Plot 12417's data with latitude on x and longitude on y in order of time, you
# will notice that the graph looks similar to the plot png we were given, and I 
# have magnified the values to show the correlation 
plt.plot(trkpts12417Df['Latitudes'], trkpts12417Df['Longitudes'], label = 'Boat Coordinates from Start', linewidth=1, linestyle='dotted')
plt.xlabel('Latitudes')
plt.ylabel('Longitudes')
plt.title('Boat Source 12417 Lat vs. Long')
plt.show()

# Plot S1's data with same parameters as before, I cleaned the axes up, and with
# the clean up we see the boat path, however with the missing points auto filled by plot
plt.plot(trkptsS1Df['Latitudes'], trkptsS1Df['Longitudes'], label = 'Boat Coordinates from Start', linewidth=1, linestyle='dotted')
#plt.axis([32.7, 32.71, -117.24, -117.22]) zoom in on swirly part
plt.xlabel('Latitudes')
plt.ylabel('Longitudes')
plt.title('Boat Source 1 Lat vs. Long')
plt.show()

#Formatting notes: Timestamp '%Y-%m-%dT%H:%M:%SZ'

# This function returns the seconds of a timestamp as an int
def seconds(time):
    return int(time[-2:])

# This function returns the minutes of a timestamp as an int
def minutes(time):
    return int(time[3:5])

# This function returns the amount of repeated timestamps for use in calculations
def countRepeats(data, spot):
    count = 2
    spot2 = spot + 1
    while seconds(data[spot2]) == seconds(data[spot]):
        count += 1
        spot2 += 1
    return count

# Returns n-1 velocity points in a velocity column for a dataframe containing GPS coords and time
def addVelocitiesDF(data):
    velocities = []     # holds velocities
    tmpSecs = -1.0      # holds seconds delta of repeated times
    first = 0           # first datapoint
    second = 1          # second datapoint
    
    # Iterates through datapoints finding the distance of two points then figures
    # out the time delta between them, time change is a little tricky with missing chunks and repitions
    for a in range(len(data['Latitudes'])-1):
        # Distance formula for points
        distance = math.sqrt(((data['Latitudes'][second] - data['Latitudes'][first])**2) + ((data['Longitudes'][second] - data['Longitudes'][first])**2))
        
        # holds seconds and minutes for timestamp points
        firstSecs = seconds(data['TimeStamps'][first])
        firstMins = minutes(data['TimeStamps'][first])
        secondSecs = seconds(data['TimeStamps'][second])
        secondMins = minutes(data['TimeStamps'][second])
       
        # !!!CAUTION!!!: does not account for missing chunks of time in hours,
        # figures out difference of seconds between point 1 and point 2
        if secondMins != firstMins:
            if secondMins > firstMins:
                secondSecs += (secondMins - firstMins) * 60
            elif secondMins < firstMins:
                secondSecs += ((60-firstMins) + secondMins) * 60 
        
        # This is the portion that takes into account repeated times, when a repeated
        # time is encountered, store that time and use it for the rest of repeated times, then change when repeats stop
        if secondSecs != tmpSecs:
            if secondSecs == firstSecs:
                count = countRepeats(data['TimeStamps'], second)
                timeDelt = 1/float(count)
                tmpSecs = secondSecs
                tmpTime = timeDelt
                repeats = count - 1
            else:
                timeDelt = secondSecs - firstSecs 
        else:
            timeDelt = tmpTime
            
        # Add velocity to list
        velocity = distance/timeDelt
        velocities.append(velocity)
      
        # Iterate counters, if repeats is 0 tmpSecs is negated and if negated repeats doesnt iterate
        first += 1
        second += 1
        if tmpSecs != -1.0:
            repeats -= 1
        if repeats == 0:
            tmpSecs = -1.0
            
    # Add velocities to dataframe, and account for missing term with additional final term
    velocities.append(velocities[-1])
    data['Velocities'] = velocities
    
# Returns n-1 acceleration vectors in a dataframe that has velocity and time data
# basically the same as the last function but doesnt need to use the distance formula
def addAccelerationsDF(data):
    accels = []
    tmpSecs = -1.0
    first = 0
    second = 1
    for a in range(len(data['Velocities'])-1):
        velocityDelt = data['Velocities'][second] - data['Velocities'][first]
        
        firstSecs = seconds(data['TimeStamps'][first])
        firstMins = minutes(data['TimeStamps'][first])
        secondSecs = seconds(data['TimeStamps'][second])
        secondMins = minutes(data['TimeStamps'][second])
       
        #CAUTION: does not account for missing chunks of time in hours
        if secondMins != firstMins:
            if secondMins > firstMins:
                secondSecs += (secondMins - firstMins) * 60
            elif secondMins < firstMins:
                secondSecs += ((60-firstMins) + secondMins) * 60 
        
        if secondSecs != tmpSecs:
            if secondSecs == firstSecs:
                count = countRepeats(data['TimeStamps'], second)
                timeDelt = 1/float(count)
                tmpSecs = secondSecs
                tmpTime = timeDelt
                repeats = count - 1
            else:
                timeDelt = secondSecs - firstSecs 
        else:
            timeDelt = tmpTime
        
        accel = velocityDelt/timeDelt
        accels.append(accel)
        
        first += 1
        second += 1
        if tmpSecs != -1.0:
            repeats -= 1
        if repeats == 0:
            tmpSecs = -1.0
            
    accels.append(accels[-1])
    data['Accelerations'] = accels
    
# Adds the velocity and acceleration columns to the dataframe
addVelocitiesDF(trkptsS1Df)
addAccelerationsDF(trkptsS1Df)
print(trkptsS1Df)