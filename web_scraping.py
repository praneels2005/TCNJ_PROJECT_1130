# Create a virtual environment: python3 -m venv venv_name
# activate virtual environment: source venv/bin/activate

#Selenium will be used to deal with the dynamically changed pages and content
#Scrapy will be used to obtain static page sources

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selectorlib import Extractor
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import UnexpectedAlertPresentException
import pytest
from playwright.sync_api import Page, expect
import requests 
#from requests_html import HTMLSession
import re
import json
import time
from bs4 import BeautifulSoup
#mpi4py
#Personal Library
import GenManLib
from GenManLib import myfunctions
import threading
import os


from selenium.webdriver.firefox.options import Options
from pymongo import MongoClient

#Step 3
def upload(Protein, data):
    client = MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongodb-vscode+1.10.0")
    
    db = client.Proteins
    
    db.create_collection(Protein)
    db[Protein].insert_many(data)
    
    
#Step 4  
#Call Manipulations each time client would like to view gene sequence manipulations
def Manipulations(Protein,Strain):
    client = MongoClient("mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongodb-vscode+1.10.0")
    
    db = client.Proteins
    
    collection = db[Protein]
    
    #Returns a single document's gene sequence
    result = collection.find_one({"Name": Strain}, {"_id":False, "Sequence": True})
    
    Sequence = str(result["Sequence"])
    print("Original Sequence:\n",Sequence)
    #print("\nComplement of Sequence:\n",myfunctions.complement(Sequence))
    #print("\nReverse of Sequence:\n",myfunctions.reverse(Sequence))
    #print("\nTranslation:\n",myfunctions.Translation(Sequence))
    #Translated_Sequence=myfunctions.Translation(Sequence)
    #print("\nBack-Translation:\n",myfunctions.Back_Translation(Translated_Sequence))
    #print("GC-Content Calculation:",myfunctions.GC_Content(Sequence))
    #print("K-MERS w/ k = 3:",myfunctions.K_MER(Sequence,3))
    
    
    
    
    
#Step 2    
def Extract_Genetic_Sequences(Page,Protein, data):
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    
    with open(data, "r") as file:
        URLS = json.load(file)
        
            
    Name_Sequence= []
    for item in URLS:
        driver.get(item["URL"])
        driver.implicitly_wait(60)
        #join elimnates spacing
        #splitlines() splits the text into a list of lines
        #[1:] skips the first line and keeps the rest
        #Use ""(double-quotations) to access tag elements
        body = "\n".join((driver.find_element(By.TAG_NAME, "pre").text).splitlines()[1:])
        
        Name_Sequence.append({
                    "Name": item["Sequence Name"],
                    "Sequence": body
                })
    file_name = Protein+"_Strains"
    with open(file_name, "w") as outfile:
        json.dump(Name_Sequence, outfile, indent = 4)
        
    upload(Protein,json.load(outfile))
    
URLS = [None] * (int(100)+1)

options = Options()
options.add_argument("--headless")
#driver = webdriver.Firefox()



'''# Directory to save JSON files
output_folder = "output_json"
# Create the folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)'''



#Step 1
def Scrape(Protein,Database_Option):
    driver = webdriver.Firefox(options=options) 
    driver.get("https://www.ncbi.nlm.nih.gov")
    driver.implicitly_wait(30)

    search_box = driver.find_element(By.ID,'term').send_keys(Protein)

    #locate dropdown
    Database = driver.find_element(By.ID, 'database')
    
    #Open the dropdown and select the requested database
    dropdown = Select(Database)
    dropdown.select_by_visible_text(Database_Option)

    search_box = driver.find_element(By.ID,'search').click()
    driver.implicitly_wait(30)
    
    page_source = driver.page_source

    soup = BeautifulSoup(page_source, "html.parser")

    #Total Pages
    num_page = soup.find(class_="num")["last"]
    
    threads = [None] * (int(num_page))
    
    

    #Page 1 until second to last page
    for page_ in range(0,int(num_page)-1):
        try:
            Results = page_source
            threads[page_] = threading.Thread(target=getPageUrls, args=(Results,page_+1,))
            threads[page_].start()
            print("thread_created" + str(page_+1))
        except Exception as e:
            print(e)
            
        #Exception is thrown at the last page and driver clicks on next page button
        try:
            click_next = driver.find_element(By.CLASS_NAME, 'active.page_link.next').click()
            page_source = driver.page_source
        except:
            print("\nEnd of pages")
            break
    
    #Final Page
    try:
        Results = page_source
        threads[int(num_page)-1] = threading.Thread(target=getPageUrls, args=(Results,int(num_page),))
        threads[int(num_page)-1].start()
        print("thread_created" + str(int(num_page)))
    except Exception as e:
        print(e)
        
    for i in range(0,int(num_page)):
        threads[i].join()
        
    print("Done")
    
    '''
   
    
    Final_URLS = []
    for i in range(len(URLS)):
        Final_URLS.append(URLS[i])  
        
    '''
    
    '''for k in Final_URLS:
        try:
            #Send an HTTP reqeust to obtain the URL 
            response = requests.get(k["URL"])
            
            if(response.status_code == 200):
            
            #Use webdriver to open URL and obtain page source code
                
            Results = page_source
            threads[page_] = threading.Thread(target=getPageUrls, args=(Results,temp_driver,page_,Protein, Database_Option,))
            threads[page_].start()
        except Exception as e:
            print(e)'''
        
    '''file_name = "FASTA_URLS_"+Protein+".json"
    #Dumps all FASTA URLS and strain names into json file
    with open(file_name, "w") as outfile:
        json.dump(URLS, outfile, indent = 4)'''
        
    #Extract_Genetic_Sequences(Protein, file_name)
    
    
#Using BeautifulSoup to extract page info
def getPageUrls(Result1,page_):
    
    #print(Result1)
    soup = BeautifulSoup(Result1, "html.parser")
    #print(soup.prettify())
    #FASTAS = driver1.find_elements(By.ID, 'ReportShortCut6')
    FASTAS = soup.find_all("a", id='ReportShortCut6')
    
    #print(FASTAS)
    #List of all FASTA URLS
    urls = [link["href"] for link in FASTAS]
    #print(urls)
    
    #List of all names
    names = soup.find_all(class_ = 'title')
    #print(names[0].text)
    links = []
    #Two elements simulatensouly traverse through their respective lists
    Page_Index = 0
    
    for url,name in zip(urls, names):
        links.append({
                "Page:":  page_,
                "Index: ": Page_Index,
                "Sequence Name": name.text,
                "URL": "https://www.ncbi.nlm.nih.gov"+url
                
        })
        Page_Index+=1
    #print(links)
    #URLS[page_] = links
    print(f"\nExtracted strains from page",str(page_))
    
    file_name = "OutputFolder//Page"+str(page_)+".json"
    #Dumps all FASTA URLS and strain names into json file
    with open(file_name, "w") as outfile:
        json.dump(links, outfile, indent = 4)
    
    return
    #print(page_) 
    
    
def getSequence(Name,Page_Source):
    soup = BeautifulSoup(Page_Source, "html.parser")
    
    time.sleep(5)
    #Print page source
    print(Page_Source)
    
    element = soup.select_one('div#viewercontent1')
    text_content = element.text.strip()  # Get all text within the element and strip whitespace
    print(text_content)
    
    
    
def getPageStrains():
    folder_path = "/Users/praneelpothukanuri/Desktop/Sophomore/TCNJ_PROJECT_1130/OutputFolder"
    
    
    for item in os.listdir(folder_path):
        full_pwd = os.path.join(folder_path, item)
        if os.path.isfile(full_pwd):
            #print(len(item))
            #threads = [None] * (len(item))
            #Traverse URLS within page, obtaining page sources
            #Create a new folder with json files of pages' strains' names and sequences
            print(item)
            with open(full_pwd, "r") as file:
                Page = json.load(file)
            print(len(Page))
            threads = [None] * (len(Page))
            #Implement nested threading
            for strain in Page:
                response = requests.get(strain["URL"])
                if response.status_code == 200:
                    #print(response.headers["Content-Type"])
                    #threads[strain["Index: "]] = threading.Thread(target=getSequence, args=(strain["Sequence Name"],response.text,))
                    #threads[strain["Index: "]].start()
                    break
                
            #for i in threads:
             #   i.join()
                
            
            
'''
for item in URLS:
        driver.get(item["URL"])
        driver.implicitly_wait(60)
        #join elimnates spacing
        #splitlines() splits the text into a list of lines
        #[1:] skips the first line and keeps the rest
        #Use ""(double-quotations) to access tag elements
        body = "\n".join((driver.find_element(By.TAG_NAME, "pre").text).splitlines()[1:])
        
        Name_Sequence.append({
                    "Name": item["Sequence Name"],
                    "Sequence": body
                })
    file_name = Protein+"_Strains"
    with open(file_name, "w") as outfile:
        json.dump(Name_Sequence, outfile, indent = 4)
'''           
 
  
'''if __name__ == '__main__':
    start = time.time()
    Scrape("HSP104", "Nucleotide")
    end = time.time()
    length = end - start
    print("Total Time: ", length)'''
    
getPageStrains()
    
#Scrape("HSP104", "Nucleotide")

#Extract_Genetic_Sequences("HSP104")

#Manipulations("HSP104", "Brettanomyces bruxellensis genome assembly, contig: scaffold1, whole genome shotgun sequence")

#with open("testing.json", 'r') as file:
#    data = json.load(file)
#upload("Test_Protein", data)


