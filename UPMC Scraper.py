from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import csv
import regex as re

headers = {"User-Agent" : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'}
html01 = requests.get('https://providers.upmc.com/search?sort=name&filter=insurance_plans%3AHighmark', headers=headers)
html02 = urlopen('https://providers.upmc.com/search?filter=insurance_plans%3AHighmark&sort=name&page=2')
html03 = urlopen('https://providers.upmc.com/search?filter=insurance_plans%3AHighmark&sort=name&page=3')


page1 = BeautifulSoup(html01.text, "html.parser")
page2 = BeautifulSoup(html02.read(), "html.parser")
page3 = BeautifulSoup(html03.read(), "html.parser")

print(page1.prettify())
print(page1.title)

dirty_file = open('dirtyData.csv', 'w', newline = '')
clean_file = open('cleanData.csv', 'w', newline = '')
dirty_writer = csv.writer(dirty_file)
clean_writer = csv.writer(clean_file)

# so get a list of all doctors subtrees
total_doctors_list = []
doctors_list1 = page1.findAll('div', class_ = 'css-16pfjm6-ProviderContainer e16v8r6n0')
doctors_list2 = page2.findAll('div', class_ = 'css-16pfjm6-ProviderContainer e16v8r6n0')
doctors_list3 = page3.findAll('div', class_ = 'css-16pfjm6-ProviderContainer e16v8r6n0')

print(doctors_list1)

total_doctors_list.append(doctors_list1)
total_doctors_list.append(doctors_list2)
total_doctors_list.append(doctors_list3)

print(total_doctors_list)

# Header Row for CSVs
dirty_writer.writerow(['Name', 'Rating', 'numRatings', 'Specialties', 'Location', 'Phone Number'])
clean_writer.writerow(['First Name', 'Middle Name', 'Last Name', 'Title', 'Rating', 'Number of Ratings', 'Specialties', 'Location', 'Address', 'Phone Number'])

num = 1
# iterates through 2 levels - the doctor lists for each page, and the doctors within that list
for docList in total_doctors_list:
    for doc in docList:
        dirty_doctor_name = str(doc.find('h2', class_ = 'css-1yi8h8m-ProviderName e16v8r6n5'))
        # clean name by looking in between the bordering characters
        name_pattern = '\d{7}">(.*?)</a></h2>'
        clean_doctor_name = re.search(name_pattern, dirty_doctor_name).group(1).strip()
        doc_fullname = clean_doctor_name.split(' ')
        doc_titles = clean_doctor_name.split(',')
        doc_first_name = doc_fullname[0]
        # a bunch of stuff to handle names of various lengths, multiple titles, etc
        if len(doc_titles) == 2:
            if len(doc_fullname) == 3:
                doc_middle_name = ''
                doc_last_name = doc_fullname[1].strip(',')
                doc_title = doc_fullname[2]
            elif len(doc_fullname) == 4:
                doc_middle_name = doc_fullname[1]
                doc_last_name = doc_fullname[2].strip(',')
                doc_title = doc_fullname[3]
            elif len(doc_fullname) == 5:
                doc_middle_name = doc_fullname[1]
                doc_last_name = doc_fullname[2]
                doc_title = doc_fullname[-1]
        elif len(doc_titles) == 3:
            if len(doc_fullname) == 4:
                doc_middle_name = ''
                doc_last_name = doc_fullname[1].strip(',')
                doc_title = doc_fullname[2].strip(',') + ',' + doc_fullname[3]
            elif len(doc_fullname) == 5:
                doc_middle_name = doc_fullname[1]
                doc_last_name = doc_fullname[2].strip(',')
                doc_title = doc_fullname[3].strip(',') + ',' + doc_fullname[4]
            elif len(doc_fullname) == 6:
                doc_middle_name = doc_fullname[1]
                doc_last_name = doc_fullname[2]
                doc_title = doc_fullname[4].strip(',') + ',' + doc_fullname[5].strip(',')
        dirty_doctor_rating = str(doc.find('span', class_ = 'css-1g3zr4y-AverageRating ea9gwtc5'))
        if len(dirty_doctor_rating) == 4:
            dirty_doctor_rating = 'No Rating'
            clean_doctor_rating = 'No Rating'
        else:
            rating_pattern = '<span class="css-1g3zr4y-AverageRating ea9gwtc5">(.*?)</span>'
            sub = re.search(rating_pattern, dirty_doctor_rating).group(1).strip()
            clean_doctor_rating = sub[:3] + '/' + sub[-1]
        dirty_doctor_numRatings = str(doc.find('a', class_ = 'css-likv8a-ProviderLink e1anvbbl0'))
        if dirty_doctor_numRatings == None:
            print('No ratings')
            dirty_doctor_numRatings = 0
            clean_doctor_numRatings = 0
        else:
            #Put the pattern in here for cleaninig numratings
            pass
        dirty_doctor_specialties = str(doc.find('li', class_ = 'css-p6aqbe-SummaryColumnItem eeq4ow44'))
        if dirty_doctor_specialties == None:
            dirty_doctor_specialties = 'No Specialties Listed'
            clean_doctor_specialties = 'No Specialties Listed'
        else:
            spec_pattern = '<li class="css-p6aqbe-SummaryColumnItem eeq4ow44">(.*?)</li>'
            clean_doctor_specialties = re.search(spec_pattern, dirty_doctor_specialties).group(1).strip()
        dirty_doctor_location = str(doc.find('tr', class_ = 'css-yk1mm6-LocationRow ecuprll6'))
        if dirty_doctor_location == None:
            dirty_doctor_location = 'No Location Listed'
            clean_doctor_location = 'No Location Listed'
        else:
            loc_pattern = 'LocationRow ecuprll6" data-name="(.*?)"><style data-emotion-'
            clean_doctor_location = re.search(loc_pattern, dirty_doctor_location).group(1).strip()
            add_pattern = '</div>(.*?)<style data-emotion-css'
            clean_doctor_address = re.search(add_pattern, dirty_doctor_location).group(1).strip()
        dirty_doctor_phone = str(doc.find('a', class_ = 'css-vvlvfr-PhoneAnchor ecuprll7'))
        if dirty_doctor_phone == 'None':
            dirty_doctor_phone = 'No Phone Number Listed'
            clean_doctor_phone = 'No Phone Number Listed'
        else:
            phone_pattern = 'PhoneAnchor ecuprll7" href="tel:(.*?)">'
            clean_doctor_phone = re.search(phone_pattern, dirty_doctor_phone).group(1).strip()
        dirty_writer.writerow([dirty_doctor_name.encode('utf-8'), dirty_doctor_rating.encode('utf-8'), dirty_doctor_numRatings.encode('utf-8'), dirty_doctor_specialties.encode('utf-8'), dirty_doctor_location.encode('utf-8'), dirty_doctor_phone.encode('utf-8')])
        clean_writer.writerow([doc_first_name, doc_middle_name, doc_last_name, doc_title, clean_doctor_rating, clean_doctor_numRatings, clean_doctor_specialties, clean_doctor_location, clean_doctor_address, clean_doctor_phone])
        num += 1
    
dirty_file.close()
clean_file.close()

