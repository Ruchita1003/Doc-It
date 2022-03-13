# -*- coding: utf-8 -*-
"""
Created on Thu Feb 24 12:37:40 2022

@author: davis
"""
import pandas as pd
import csv
from tabula import read_pdf
from tabula import convert_into

df = read_pdf('PGH-Weed-Doctors.pdf')
dt = convert_into('PGH-Weed-Doctors.pdf', 'Weed-Doctors.csv', pages='all')
dirtyfile = pd.read_csv('Final-Medical.csv')
cleanfile = ('Cleaned-Doctors.csv')
dirtyfile['Last Name'] = dirtyfile['Last Name'].astype(str).str.strip('[]')
dirtyfile['Last Name'] = dirtyfile['Last Name'].astype(str).str.strip("'")
dirtyfile['Specialty']  = dirtyfile['Specialty'].fillna('General Practicioner')
dirtyfile = dirtyfile.dropna(axis=0)
add = dirtyfile['Location'].astype(str)
dirtyfile.to_csv('Cleaned-Doctors.csv', index = False)

cleaned_file = open('Cleaned-Doctors.csv', 'r', newline = '')
master_file = open('finalfile.csv', 'w', newline = '')
doc_reader = csv.reader(cleaned_file)
master_writer = csv.writer(master_file)
first_Row = True
streetaddress = []
city = []
zipc = []
for row in doc_reader:
    if first_Row:
        first_Row = False
    else:
        #print(row[2])
        fulladdress = row[2].split(',')
        streetaddress = fulladdress[0]
        if len(fulladdress) > 2:
            city = fulladdress[1]
        else:
            city = ''
        if len(fulladdress) > 3:
            state = fulladdress[2]
        else:
            state = 'PA'
        if len(fulladdress) > 4:
            zipc = fulladdress[3]
        else:
            zipc = '15213'
  

