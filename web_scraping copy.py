# Create a virtual environment: python3 -m venv venv_name
# activate virtual environment: source venv/bin/activate


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
from selenium.webdriver.common.keys import Keys
import requests
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
    

#Index corresponds to a page number
URLS = [None] * (int(100)+1)
options = Options()
options.add_argument("--headless")
#driver = webdriver.Firefox()



#Step 1
def Scrape(Protein,Database_Option):
    
    #Pass this to each thread
    driver = webdriver.Firefox(options=options)
    #driver = webdriver.Firefox() 
    driver.get("https://www.ncbi.nlm.nih.gov")
    driver.implicitly_wait(30)

    search_box = driver.find_element(By.ID,'term').send_keys(Protein)

    #locate dropdown
    Database = driver.find_element(By.ID, 'database')
    
    #Open the dropdown and select "Nucleotide" database
    dropdown = Select(Database)
    dropdown.select_by_visible_text("Nucleotide")

    search_box = driver.find_element(By.ID,'search').click()
    driver.implicitly_wait(30)
    
    #pages = driver.find_elements(By.ID, 'ui-ncbiexternallink-6')
    #print(len(pages))

    page_source = driver.page_source
    
    soup = BeautifulSoup(page_source, "html.parser")

    #Total Pages
    num_page = soup.find(class_="num")["last"]
    
    threads = [None] * (int(num_page)+1)
    
    #1,int(num_page)+1
    #max_page = int(num_page)
    max_page = 4
    #thread per page
    #Loop traverses until 2nd to last page
    for page_ in range(1,max_page):
        try:     
            #protein name, and page
            threads[page_] = threading.Thread(target=getPageUrls, args=(Protein, page_,))
            threads[page_].start()
            time.sleep(1)
            print("thread_created : " + str(page_))
        except Exception as e:
            print(e)
            
        #Process Bottleneck can be avoided by clicking until the last page, exiting loop, and scraping final page
        #Exception is thrown at the last page and driver clicks on next page button
        try:
            click_next = driver.find_element(By.CLASS_NAME, 'active.page_link.next').click()
            page_source = driver.page_source
        except:
            print("\nEnd of pages")
            break
    
    #Creating thread for last page
    try:     
        #protein name, and page
        threads[max_page] = threading.Thread(target=getPageUrls, args=(Protein, max_page,))
        threads[max_page].start()
        time.sleep(1)
        print("thread_created : " + str(max_page))
    except Exception as e:
        print(e)
    
    
    for i in range(1,max_page):
            threads[i].join()
    
    print("Done")
    
    
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
    
    
#All protein data will be scraped from the nucleotide database    
def getPageUrls(Protein,page_):
    
    #tempdriver = webdriver.Firefox(options=options)
    tempdriver = webdriver.Firefox(options=options) 
    tempdriver.get("https://www.ncbi.nlm.nih.gov")
    tempdriver.implicitly_wait(30)

    search_box = tempdriver.find_element(By.ID,'term').send_keys(Protein)

    #locate dropdown
    Database = tempdriver.find_element(By.ID, 'database')
    
    #Open the dropdown and select the requested database
    dropdown = Select(Database)
    dropdown.select_by_visible_text("Nucleotide")

    search_box = tempdriver.find_element(By.ID,'search').click()
    tempdriver.implicitly_wait(30)
    
    #Change the source code of web element "next"'s "page" attribute to desired page number. Clicking on next again will execute the modified source code 
    Next_Button = (tempdriver.find_element(By.ID,'EntrezSystem2.PEntrez.Nuccore.Sequence_ResultsPanel.Entrez_Pager.Page'))
    
    tempdriver.execute_script("argument[0].setAttribute('page', \'" + str(page_) + "\')", Next_Button)
    #Next_Button.get_attribute("page")
    
    if(page_>1):
        try:
            click_next = tempdriver.find_element(By.CLASS_NAME, 'active.page_link.next').click()
        except:
            print("\nEnd of pages")
    
    #print(Page_Box)
    #Page_finder.clear()
    #print(Page_finder)
    #Page_finder.click()
    #Page_Box.get_attribute("value")
    #print(Page_finder.get_attribute("value"))
    #tempdriver.fi
    #Page_finder.send_keys(page_)
    #Page_Box.send_keys(Keys.ENTER)
    
    '''try:
        click_next = tempdriver.find_element(By.CLASS_NAME, 'active.page_link.next').click()
        page_source = tempdriver.page_source
    except:
        print("\nEnd of pages")'''
    
    '''try:
        WebDriverWait(tempdriver, 10).until(
        EC.presence_of_element_located((By.ID, 'new_element_id'))
    )
    except Exception as e:
        print(f"Error waiting for new element: {e}")'''
    
    #print(tempdriver.page_source)
    Results = tempdriver.find_elements(By.CLASS_NAME, 'rslt')
    #Fasta link
    FASTAS = tempdriver.find_elements(By.ID, 'ReportShortCut6')
    urls = [link.get_attribute('href') for link in FASTAS]

    #Two elements simulatensouly traverse through their respective lists
    links = []
    Page_Index = 0
    
    for url,name in zip(urls, Results):
        links.append({
                "Page:":  page_,
                "Index: ": Page_Index,
                "Sequence Name": name.find_element(By.CLASS_NAME, 'title').text,
                "URL": "https://www.ncbi.nlm.nih.gov"+url
                
        })
        Page_Index+=1
    print(f"\nExtracted strains of",Protein,"from page",str(page_))
    file_name = "OutputFolder//Page"+str(page_)+".json"
    #Dumps all FASTA URLS and strain names into respective page's json file
    try:
        with open(file_name, "w") as outfile:
            json.dump(links, outfile, indent = 4)
    except Exception as e:
        print(e)
    #tempdriver.quit()
        
    
    
    
    
 
  
if __name__ == '__main__':
    start = time.time()
    Scrape("HSP104", "Nucleotide")
    end = time.time()
    length = end - start
    print("Total Time: ", length)
    
#Scrape("HSP104", "Nucleotide")

#Extract_Genetic_Sequences("HSP104")

#Manipulations("HSP104", "Brettanomyces bruxellensis genome assembly, contig: scaffold1, whole genome shotgun sequence")

#with open("testing.json", 'r') as file:
#    data = json.load(file)
#upload("Test_Protein", data)


