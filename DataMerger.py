# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 20:32:55 2022

@author: KraigSheetz
"""
import csv

upmc_file = open('UPMC_Clean.csv', 'r', newline = '')
dac_file = open('dacClean.csv', 'r', newline = '')
mj_file = open('MJDocs.csv', 'r', newline = '')
master_file = open('masterFile2.csv', 'w', newline = '')

upmc_reader = csv.reader(upmc_file)
dac_reader = csv.reader(dac_file)
mj_reader = csv.reader(mj_file)
master_writer = csv.writer(master_file)

# Need to add gender, figure out how to get from UPMC
master_writer.writerow(['Doctor ID', 'First Name', 'Middle Name', 'Last Name', 'Title', 'Rating', 
                        '# Ratings', 'Specialties', 'Practicing Locations', 'Address 1', 'Address 2', 
                        'City', 'State', 'Zip', 'Phone Number', 'Medicinal License'])

doc_ID = 10000
first_Row = True
for row in upmc_reader:
    if first_Row:
        first_Row = False
    else:
        address = row[8].split(',')
        statezip = address[-1].split(' ')
        state = statezip[1]
        zipp = statezip[2]
        address1 = address[0]
        address2 = address[1]
        city = address[-2]
        master_writer.writerow([doc_ID, row[0], row[1], row[2], row[3].upper(), row[4], row[5], row[6].title(), 
                                row[7], address1, address2, city, state, zipp, row[9], False])
        doc_ID += 1

first_Row = True    
for row in dac_reader:
    if first_Row:
        first_Row = False
    else:
        phone = row[15]
        if len(phone) == 0:
            phone = 'Not Listed'
        master_writer.writerow([doc_ID, row[4].capitalize(), row[5].capitalize(), row[3].capitalize(),
                               row[8].upper(), 'No Rating', 0, row[9].title(), row[-1].title(), 
                               row[10].title(), row[11].capitalize(), row[12].capitalize(), 
                               row[13], row[14], phone, False])
        doc_ID += 1

first_Row = True
for row in mj_reader:
    if first_Row:
        first_Row = False
    else:
        address1 = row[3].strip()
        address2 = row[4]
        city = row[5].strip()
        state = 'PA'
        zipp = row[7]
        master_writer.writerow([doc_ID, row[0], '', row[1], 'MD', 'No Rating', 0, row[2].title(),
                                'Private Practice - See Address', address1, address2, city, 
                                state, zipp, 'Not Listed', True])
        doc_ID += 1

upmc_file.close()
dac_file.close()
mj_file.close()
master_file.close()
