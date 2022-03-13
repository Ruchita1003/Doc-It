# -*- coding: utf-8 -*-

"""
Created on Thu Feb 24 20:33:25 2022

@author: Anuja Salvi, Kraig Sheetz, Ashwini Maddur Ashok, Ruchita Nagare, Tim Davison

"""
from IPython.display import display
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import urllib.parse
import haversine as hs
import re
import folium
import webbrowser
import tkinter as tk
import pandastable
from tkinter import ttk
from pandastable import Table
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk)


#Create DF, Sort by Last/First Name, Set index to new DocID
master_df = pd.read_csv('MasterFile3.csv')
master_df.sort_values(by=['Last Name', 'First Name'], inplace = True)
length = len(master_df.index)
master_df.index = range(10000, 10000+length, 1)
# Makes the rating column either 'No Rating' or the rating value out of 5
master_df['Rating'] = master_df['Rating'].str.split('/').str[0]


def rateDoc(firstName, lastName, rating):
    '''
    Parameters
    ----------
    dataframe : pandas DateFrame
        Input dataframe (master_df) in most cases,
        can adapt to display nearest doc df.
    lastName : String
        Last name to search on.
    firstName : String
        First name to search on.
    rating : Int
        User rating for the doctor

    Returns
    -------
    TYPE
        DateFrame for rated doctor with updated rating
    '''
    dataframe = master_df
    matchLast = dataframe[dataframe['Last Name'] == lastName]
    matchFirst = matchLast[matchLast['First Name'] == firstName]
    index = matchFirst.index.tolist()
    curRating = master_df.at[index[0],'Rating']
    if curRating == 'No Rating':
        master_df.at[index[0],'Rating'] = rating
        master_df.at[index[0],'# Ratings'] = 1
    else:
        numRatings = float(master_df.at[index[0],'# Ratings'])
        weightedCurrent = float(curRating) * (numRatings/(numRatings+1))
        weightedNew = float(rating) * (1/(numRatings+1))
        newRating = weightedCurrent + weightedNew
        master_df.at[index[0],'Rating'] = newRating
        master_df.at[index[0],'# Ratings'] = numRatings+1
    return master_df.loc[[index[0]]].filter(items=['First Name', 'Last Name', 'Rating', '# Ratings'
                                    'Specialty','Address 1', 'Phone Number', 
                                    'Medicinal License'])

def distanceData():
    '''
    This funtion uses the nominatim API to obtain
    the latitute and longitutude coordinates of
    every doctor in the dataframe.
    Returns
    -------
    finaldf : pandas dataframe
        Has new columns for coordinates.
    '''
    ziplist = master_df['Zip']
    latlist = []
    lonlist = []
    for zip in ziplist:
        url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(zip) +'?format=json'
        response = requests.get(url).json()
        if (response):
            latlist.append(response[0]["lat"])
            lonlist.append(response[0]["lon"])
        else:
            latlist.append("")
            lonlist.append("")
    latlongdf = pd.DataFrame(data={"Zip":ziplist,"Lat":latlist,"Long":lonlist}, index = master_df.index)
    latlongdf.drop("Zip", axis = 1 , inplace = True)
    finaldf = pd.concat([master_df, latlongdf], axis=1)
    finaldf['Lat']=finaldf["Lat"].astype(np.float64)
    finaldf["Long"]=finaldf["Long"].astype(np.float64)
    finaldf['latlong'] = finaldf[['Lat','Long']].apply(tuple, axis=1)
    return finaldf

def computeDistance(userZip):
    '''
    This function computes the distance between 
    the user and every doctor in the datframe.

    Parameters
    ----------
    userZip : String. 
        The user inputs their zipcode.
    Returns
    -------
    finaldf : pandas dataframe
        A datframe with a coulmn that has the calculated
        distance of the user with every doctor in the dataframe.
    '''
    url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(userZip) +'?format=json'
    response = requests.get(url).json()
    locUser = (float(response[0]["lat"]), float(response[0]["lon"]))
    alldistlist = []
    for x in master_df["latlong"]:
        x = x.strip('(')
        x = x.strip(')')
        full = x.split(',')
        lat = float(full[0].strip())
        long = float(full[1].strip())
        locDoc = lat,long
        alldistlist.append(hs.haversine(locUser,locDoc, unit='mi'))        
    master_df["Distance"] = alldistlist  
    return master_df

# Calculate lat long for every doctor, add column to df
# Only Needs to be done when doctors are added to the DF
#master_df = distanceData()

# Creates CSV with stored latlong
#master_df.to_csv('MasterFile3.csv', index=False)

computeDistance('15206')
master_df = master_df[master_df['Distance'] < 100]


def mapDoc(dataframe = master_df):
    '''
    This function plots the location of doctors on the map.
    The doctors displayed are filtered on the desired 
    requirements input by the user

    Parameters
    ----------
    dataframe : pandas dataframe
        This dataframe is a snippet from the main dataframe.
        The dataframe contains information of the doctors 
        that match the users search requirement.
        
    Returns
    -------
    None. Opens a brower pop up of the mapped doctors.
    '''
    map = folium.Map(location=[dataframe.Lat.mean(), dataframe.Long.mean()], zoom_start=4, control_scale=True)

    for index, location_info in dataframe.iterrows():
        folium.Marker([location_info["Lat"], location_info["Long"]], popup="Name: " + location_info["First Name"] + " " + location_info["Last Name"] + "\n" 
                      + "Location: " + location_info["Practicing Locations"]).add_to(map)
    loc = 'Doctor''s Around You'
    title_html = '''<h3 align="center" style="font-size:24px"><b>{}</b></h3>'''.format(loc)   
    map.get_root().html.add_child(folium.Element(title_html))
    map.save("index.html")
    url = "index.html"
    new = 2 # open in a new tab, if possible
    webbrowser.open(url,new=new)


#Cleaning up redundant data in specialty and city columns
master_df = master_df.apply(lambda x: x.astype(str).str.title())
master_df.loc[master_df['Specialties'] == "Infectious Disease",'Specialties']  = "Infectious Diseases"
master_df.loc[master_df['Specialties'] == "Interventional Pain",'Specialties'] = "Pain Management"
master_df.loc[master_df['Specialties'] == "Obstetrics/Gynecology","Specialties"] = "Obstetrics and Gynecology"
master_df.loc[master_df['Specialties'] == "Obstetrics And Gynecology","Specialties"] = "Obstetrics and Gynecology"
master_df.loc[master_df['Specialties'] == "Adult Psychiatry And\r\nChild And Adolescent\r\nPsychiatry","Specialties"] =  "Adult Psychiatry And Child And Adolescent Psychiatry"
master_df.loc[master_df['Specialties'] == "Pulmonology","Specialties"] = "Pulmonary Diseases"
master_df.loc[master_df['Specialties'] == "Emergency Medicine\r\nFamily Medicine","Specialties"] = "Family Medicine"
master_df.loc[master_df['Specialties'] == "Plastic Surgery","Specialties"] ="Plastic And Reconstructive Surgery"
master_df.loc[master_df['Specialties'] == "Endocrinology, Diabetes\r\nAnd Metabolis","Specialties"] ="Endocrinology"
master_df.loc[master_df['Specialties'] == "Pediatric Neurosurgery","Specialties"] = "Pediatric Neurology"
master_df.loc[master_df['Specialties'] == "Hematology/Oncology","Specialties"] = "Hematology Oncology"
master_df.loc[master_df['Specialties'] == "Family And Sports\r\nMedicine","Specialties"] = "Family Medicine"
master_df.loc[master_df['Specialties'] == "Family Hospice And\r\nPalliative Care","Specialties"] = "Hospice And Palliative Care"
master_df.loc[master_df['Specialties'] == "Hospice And Palliative, Medicine,  Rheumatology","Specialties"] = "Hospice And Palliative Care"
master_df.loc[master_df['Specialties'] == "Hospice/Palliative Care"] = "Hospice And Palliative Care"
master_df.loc[master_df['Specialties'] == "Palliative Care"] = "Hospice And Palliative Care"
master_df.loc[master_df['Specialties'] == "Interventional Pain\r\nManagement","Specialties"] = "Pain Management"
master_df.loc[master_df['Specialties'] == "Neurology And Pain\nMedicine","Specialties"] = "Neurology"
master_df.loc[master_df['Specialties'] == "Family Medicine,\r\nHospice And Palliative\r\nCare","Specialties"] = "Hospice And Palliative Care"
master_df.loc[master_df['Specialties'] == "Family Practice And\r\nGeriatrics","Specialties"] =  "Family Practice And Geriatrics"
master_df.loc[master_df['Specialties'] == "Cardiovascular Disease (Cardiology)","Specialties"] = "Cardiology"
master_df.loc[master_df['Specialties'] == "Physical Medicine And\r\nRehabilitation","Specialties"] = "Physical Medicine And Rehabilitation"
master_df.loc[master_df['Specialties'] == "Pain Medicine And\r\nPhysical Medicine And\r\nRehabilitation","Specialties"] = "Physical Medicine And Rehabilitation"
master_df.loc[master_df['Specialties'] == "Pain Management,\r\nPhysical Medicine And\r\nRehabilitation","Specialties"] = "Physical Medicine And Rehabilitation"
master_df.loc[master_df['Specialties'] == "Pain Management And\r\nRehabilitation","Specialties"] = "Physical Medicine And Rehabilitation"
master_df.loc[master_df['Specialties'] == "General Practice","Specialties"] = "General Practitioner"
master_df.loc[master_df['Specialties'] == "General Practicioner","Specialties"] = "General Practitioner"
master_df.loc[master_df['Specialties'] == "Preventive Medicine And\r\nIntegrative-Functional\r\nMedicine","Specialties"] = "Preventive Medicine"
master_df.loc[master_df['Specialties'] == "Pulmonary And Critical\r\nCare Medicine","Specialties"] = "Pulmonary Diseases"
master_df.loc[master_df['Specialties'] == "Pulmonary Disease","Specialties"] = "Pulmonary Diseases"
master_df.loc[master_df['Specialties'] == "Physical Medicine, Rehabilitation And Pain Management'","Specialties"] = "Pain Medicine"
master_df.loc[master_df['Specialties'] == "Pediatric\r\nGastroenterology","Specialties"] = "Pediatric"
master_df.loc[master_df['Specialties'] == "Pain Medicine And\r\nAnesthesiology","Specialties"] = "Pain Medicine"
master_df.loc[master_df['Specialties'] == "Hematology","Specialties"] = "Hematology Oncology"
master_df.loc[master_df['Specialties'] == "Oncology And\r\nHematology","Specialties"] = "Hematology Oncology"
master_df.loc[master_df['Specialties'] == "Hematology And\r\nOncology","Specialties"] = "Hematology Oncology"
master_df.loc[master_df['Specialties'] == "Addictive Medicine","Specialties"] = "Addiction Medicine"
master_df.loc[master_df['Specialties'] == "Pain Medicine And\r\nAnesthesiology And\r\nAddiction Medicine","Specialties"] = "Addiction Medicine"
master_df.loc[master_df['Specialties'] == "Addictive Medicine","Specialties"] = "Addiction Medicine"
master_df.loc[master_df['Specialties'] == "Endocrinology, Diabetes\r\nAnd Metabolism","Specialties"] = "Endocrinology"
master_df.loc[master_df['Specialties'] == "Addictive Medicine","Specialties"] = "Addiction Medicine"
master_df.loc[master_df['Specialties'] == "Pediatric","Specialties"] = "Pediatrics"
master_df.loc[master_df['Specialties'] == "Pediatric","Specialties"] = "Pediatrics"
master_df.loc[master_df['Specialties'] == "Physical Medicine, Rehabilitation And Pain Management","Specialties"] = "Physical Medicine And Rehabilitation"
master_df.loc[master_df['City'] == "Pittsbugh","City"] = "Pittsburgh"
master_df.loc[master_df['City'] == " Pittsburgh","City"] = "Pittsburgh"
master_df = master_df[master_df['First Name'] != "Hospice And Palliative Care"]

#To get a set of all the specialities and cities
specialitiesSet = set(master_df['Specialties'].values)
specialitiesSet = sorted(specialitiesSet)
citySet = (set(master_df['City'].values))
hospitalsDataSet = (set(master_df['Practicing Locations'].values))

def getSpecialities():
    print("We have doctors in all the following specialities:")
    print('---------------------------------------------------------------------------------')
    for item in specialitiesSet:
        print(item)

doctorsCountByCity = []
doctorsCountBySpec = []
doctorsCountByHospital = []
hospitalsSet = set()

def getDataBySpec():
    for item in citySet:
        df = (master_df.loc[master_df['City'] == item])
        doctorsCountByCity.append(len(df))  # int
    for item in specialitiesSet:
        df = (master_df.loc[master_df['Specialties'] == item])
        doctorsCountBySpec.append(len(df))  # int
    for item in hospitalsDataSet:
        splitsList = item.split(", ")
        for i in range(0, len(splitsList)):
            temp = splitsList[i]
            hospitalsSet.add(temp)
    itemsToRemove = set()

    pat = r'(^Department.*$)|(^Division.*$)|(The.*)|(Nose And Throat)'

    for item in hospitalsSet:
        if re.search(pat, item) != None:
            itemsToRemove.add(item)
    for item in itemsToRemove:
        hospitalsSet.remove(item)

getDataBySpec()

# creating the cityData and specData
cityData = {}
specData ={}
hospData = {}
index1=0;
index2=0;
index3 = 0;
for item in citySet:
    cityData[item] = doctorsCountByCity[index1]
    index1 += 1
for item in specialitiesSet:
    specData[item] = doctorsCountBySpec[index2]
    index2 += 1
for item in hospitalsSet:
    count = 0
    for index, row in master_df.iterrows():
        if (item in row['Practicing Locations']):
            count += 1
    doctorsCountByHospital.append(count)
for item in hospitalsSet:
    hospData[item] = doctorsCountByHospital[index3]
    index3 += 1

#credits for sorting dict: https://stackoverflow.com/questions/613183/how-do-i-sort-a-dictionary-by-value
cityData = dict(sorted(cityData.items(), key=lambda item: item[1]))
specData = dict(sorted(specData.items(), key=lambda item: item[1]))
hospData = dict(sorted(hospData.items(), key=lambda item: item[1]))

plt.title("Percentage of doctors that hold medical license to prescribe Marijuana")
labels = ["Can prescribe","Cannot prescribe"]
sizes = [len((master_df.loc[master_df['Medicinal License'] == "True"])),len((master_df.loc[master_df['Medicinal License'] == "False"]))]

#%%%

# Window
root=tk.Tk()
root.title('Doc-It!')
 
# setting the windows size
root.geometry("600x500")

# declaring string variable
# for storing fields

fname_var=tk.StringVar()
lname_var=tk.StringVar()
special = tk.StringVar()
pres = tk.StringVar(value='False')
zipcode_var = tk.StringVar()
## Code 
rating_var = tk.IntVar()
f_name_rate = tk.StringVar()
l_name_rate = tk.StringVar()
  
# These methods must be called after the GUI is established, which
# is why they are imbedded in the GUI portion and not above with the other
# methods
    
def submit():
 
    first_name=fname_var.get()
    last_name=lname_var.get()
    specialisation = special.get()
    prescription = pres.get()
    zipcode_entered=zipcode_var.get()

    rslt_df = master_df[(master_df['First Name'].str.contains(first_name.strip())) & (master_df['Last Name'].str.contains(last_name.strip())) & (master_df['Specialties'].str.contains(specialisation))  & (master_df['Medicinal License'].str.contains(prescription)) & (master_df['Zip'].str.contains(zipcode_entered))]

    root2 = tk.Tk()
    root2.geometry("1700x1000")
    
    root2.title('Doctors data')

    frame = tk.Frame(root2)
    
    pt = Table(frame, dataframe = rslt_df)
       
    pt.show()
    frame.pack(fill=tk.BOTH, expand=True)
    root2.mainloop()
     
    fname_var.set("")
    lname_var.set("")
    special.set("")

# defining a function that is called when show graphs is clicked

def graph():
    
    #Bar graph to show the number of doctors in each specialty which have mpre than ten doctors
    
    ##1
    font = {'family': 'Arial','weight': '40','size': 24,}
    specs = list(({key : val for key, val in specData.items()
                   if val>10}).keys())
    numbers = list(({key : val for key, val in specData.items()
                     if val>10}).values())
    
    fig = plt.figure(figsize=(7,12))

    # creating the bar plot
    plt.bar(specs, numbers,width=0.3)
    plt.xlabel("Specialities offered",fontdict=font, fontsize=10)
    plt.ylabel("No. of doctors",fontdict=font, fontsize=10)
    #plt.title("Specialities with more than 10 Doctors",fontdict=font)
    ax = plt.gca()
    ax.set_xticks(specs)
    ax.set_xticklabels(specs, rotation=40,horizontalalignment="right")
    ax.tick_params(axis='x', labelsize='large')
    ax.tick_params(axis='x', labelsize='10')
    ax.tick_params(axis='y', labelsize='small')
    ax.tick_params(axis='y', labelsize='10')
    ax.set_xlim([0, 20])
    ax.set_ylim([0, 200])

    plt.show()
    
    root2 = tk.Tk()
    root2.geometry("1700x1000")
    
    root2.title('Graphs')
    btn = tk.Label(root2, text='Specialities with more than 10 Doctors')
    btn.grid(row=0, column=0, padx=20, pady=10)
    
    # specify the window as master
    canvas = FigureCanvasTkAgg(fig, master=root2)
    canvas.draw()
    canvas.get_tk_widget().grid(row=1, column=0, ipadx=40, ipady=20)
    
    # navigation toolbar
    toolbarFrame = tk.Frame(master=root2)
    toolbarFrame.grid(row=2,column=0)

    ##2
    fig2 = plt.figure(figsize=(7,12))
    btn = tk.Label(root2, text='Percentage of doctors that hold medical license to prescribe Marijuana')
    btn.grid(row=0, column=1, padx=20, pady=10)
    #plt.title("Percentage of doctors that hold medical license to prescribe Marijuana",fontsize=10)
    labels = ["Can prescribe","Cannot prescribe"]
    sizes = [len((master_df.loc[master_df['Medicinal License'] == "True"])),len((master_df.loc[master_df['Medicinal License'] == "False"]))]
    # Plot
    plt.pie(sizes, labels=labels, rotatelabels=False, autopct='%1.1f%%',
            shadow=True, startangle=90)
    plt.axis('equal')
    plt.show()
    
    canvas2 = FigureCanvasTkAgg(fig2, master=root2)
    canvas2.draw()
    canvas2.get_tk_widget().grid(row=1, column=1, ipadx=40, ipady=20)
    
    # navigation toolbar
    toolbarFrame2 = tk.Frame(master=root2)
    toolbarFrame2.grid(row=2,column=1)
    

    ##3
    specs = list(({key: val for key, val in hospData.items()
                   if val > 25}).keys())
    numbers = list(({key: val for key, val in hospData.items()
                     if val > 25}).values())
    # Figure Size
    fig3, ax1 = plt.subplots(figsize=(7,12))
    
    # Horizontal Bar Plot
    ax1.barh(specs, numbers)
    
    # Remove axes splines
    for s in ['top', 'bottom', 'left', 'right']:
        ax1.spines[s].set_visible(False)
        
    # Remove x, y Ticks
    ax1.xaxis.set_ticks_position('none')
    ax1.yaxis.set_ticks_position('none')

    # Add padding between axes and labels
    ax1.xaxis.set_tick_params(pad=5)
    ax1.yaxis.set_tick_params(pad=10)

    # Add x, y gridlines
    ax1.grid(visible=True, color='grey',
            linestyle='-.', linewidth=0.5,
            alpha=0.2)

    # Show top values
    ax1.invert_yaxis()

    # Add annotation to bars
    for i in ax.patches:
        plt.text(i.get_width() + 0.2, i.get_y() + 0.5,
                 str(round((i.get_width()), 2)),
                 fontsize=10, fontweight='bold',
                 color='grey')

    # Add Plot Title
    btn = tk.Label(root2, text='Hospitals with >25 of doctors')
    btn.grid(row=0, column=2, padx=20, pady=10)

    plt.yticks(fontsize=8,wrap=True)
    plt.xticks(fontsize=10)
    # Show Plot
    plt.show()
    
    canvas3 = FigureCanvasTkAgg(fig3, master=root2)
    canvas3.draw()
    canvas3.get_tk_widget().grid(row=1, column=2, ipadx=40, ipady=20)
    
    # navigation toolbar
    toolbarFrame3 = tk.Frame(master=root2)
    toolbarFrame3.grid(row=2,column=2)
    
    root2.mainloop()
          
     
# label text for title
ttk.Label(root, text = "Welcome to Doc-It", 
          background = '#49A', foreground ="white", 
          font = ("Times New Roman", 15)).grid(row = 0, column = 1, pady = 25)     
# creating a label for
# name using widget Label
fname_label = tk.Label(root, text = 'Doctor First Name', font=('calibre',10, 'normal'))
  
# creating a entry for input
# name using widget Entry
fname_entry = tk.Entry(root,textvariable = fname_var, font=('calibre',10,'normal'))
  
# creating a label for last name
lname_label = tk.Label(root, text = 'Doctor Last Name', font = ('calibre',10,'normal'))
  
# creating a entry for last name
lname_entry=tk.Entry(root, textvariable = lname_var, font = ('calibre',10,'normal'))
  
# placing the label and entry in
# the required position using grid
# method
# label
ttk.Label(root, text = "Select a specialty :",
          font = ('calibre',10,'normal')).grid(column = 0,
          row = 6, padx = 10, pady = 25)
  
# Combobox creation

specialty_chosen = ttk.Combobox(root, width = 27, textvariable = special)
  
# Adding combobox drop down list
specialty_chosen['values'] = specialitiesSet
specialty_chosen['state'] = 'readonly'
specialty_chosen.current()

ttk.Label(root, text = "Can prescribe Medical Marijuana?",
          font = ('calibre',10,'normal')).grid(column = 0,
          row = 7, padx = 10)
                                               
RBttn = tk.Radiobutton(root, text = "No", variable = pres,
                    value = "False")
 
RBttn2 = tk.Radiobutton(root, text = "Yes", variable = pres,
                     value ="True")

# creating a label for zipcode
#zipcode_label = tk.Label(root, text = 'Enter Zipcode', font = ('calibre',10,'normal'))
ttk.Label(root, text = "Zipcode",
            font = ('calibre',10,'normal')).grid(column = 0,
            row = 10, padx = 10)
# creating a entry for zipcode
zipcode_entry=tk.Entry(root, textvariable = zipcode_var, font = ('calibre',10,'normal'))

# Create label for rate a doctor text
ttk.Label(root, text = "Rate a Doc!",
            font = ('calibre',16,'bold')).grid(column = 1,
            row = 19, padx = 10)
                                                 
# Create label for rate a doctor firstname
ttk.Label(root, text = "First Name",
            font = ('calibre',10,'normal')).grid(column = 0,
            row = 20, padx = 10)
                                        
# Create label for rate a doctor lastname
ttk.Label(root, text = "Last Name",
            font = ('calibre',10,'normal')).grid(column = 1,
            row = 20, padx = 10)
                                                 
# Create label for rate a doctor rating
ttk.Label(root, text = "Rating (0-5)",
            font = ('calibre',10,'normal')).grid(column = 2,
            row = 20, padx = 10)

# creating a entry for firstname rating
rate_first=tk.Entry(root, textvariable = f_name_rate, font = ('calibre',10,'normal'))

# creating a entry for firstname rating
rate_last=tk.Entry(root, textvariable = l_name_rate, font = ('calibre',10,'normal'))

# creating a entry for firstname rating
rate_rating=tk.Entry(root, textvariable = rating_var, font = ('calibre',10,'normal'))

# creating a button using the widget
# Button that will call the submit function
sub_btn=tk.Button(root,text = 'Submit', command = submit)
graph_btn = tk.Button(root,text = 'Show Graphs', command = graph)
map_btn = tk.Button(root, text = 'Show Map', command = mapDoc)
rate_btn = tk.Button(root, text = 'Rate', 
                     command = lambda: rateDoc(f_name_rate.get(), l_name_rate.get(), rating_var.get()))

#displaying on window
fname_label.grid(row=3,column=0)
fname_entry.grid(row=3,column=1)
lname_label.grid(row=4,column=0)
lname_entry.grid(row=4,column=1)
specialty_chosen.grid(row = 6,column = 1)
RBttn.grid(row=7, column=1)
RBttn2.grid(row=8, column = 1)
zipcode_entry.grid(row=10, column =1)

sub_btn.grid(row=15,column=1)
graph_btn.grid(row=17,column=1)
map_btn.grid(row = 18, column = 1)
rate_first.grid(row = 21, column= 0)
rate_last.grid(row = 21, column= 1)
rate_rating.grid(row = 21, column= 2)
rate_btn.grid(row = 22, column = 1)

# performing an infinite loop
# for the window to display
root.mainloop()

#%%%


