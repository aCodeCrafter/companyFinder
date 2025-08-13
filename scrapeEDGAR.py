import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
from time import sleep

def get_td_tag_contents(td_tag):
    """
    Extracts the contents of a td tag as found in EDGAR html
    """
    extracted_text = ""
    for content in td_tag.contents:
        # Check if the current content is a <br> tag
        if isinstance(content, Tag) and content.name == 'br':
            break  # Stop when the first <br> is encountered
        elif isinstance(content, NavigableString):
            # If it's a string (text node), add its stripped content
            extracted_text += content.strip()
        elif isinstance(content, Tag):
            # If it's another tag (like <strong>, <a>, etc.), get its text
            # and add it. This handles cases like "<strong>Company</strong> Name<br>"
            extracted_text += content.get_text(strip=True)
    return extracted_text

def parse_edgar_html(text):
    """
    Parses scraped html from SEC EDGAR
    Accepts:
        text: Html from sec edgar
    Returns:
        Dictionary with cik number as key, and company name.
        If there is no table found, return empty dict
    """
    bs = BeautifulSoup(text, 'html.parser')
    table = bs.find('table')
    company_dict = dict()
    if table:
        for row in table.find_all('tr'):
            temp = []
            for data in row.find_all('td'):
                temp.append(get_td_tag_contents(data))
            if len(temp) > 1:
                company_dict[temp[0]] = (temp[1], temp[2])
    return company_dict

if __name__ == "__main__":
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
    state_code = 'NY'
    sic_code = '7370'
    start = 0
    company_dict = dict()
    while True: # do-while loop to go until there is less than 100 results
        target_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&SIC={sic_code}&State={state_code}&owner=exclude&match=&start={start}&count=100"
        print(target_url)
        content = requests.get(target_url,headers=headers).text
        temp_dict = parse_edgar_html(content)
        company_dict.update(temp_dict)
        print(str(len(company_dict))+" "+str(start))
        start+=100
        if len(temp_dict) < 100:
            break
        sleep(1)
    if len(company_dict) > 0:
        print(f"Found {len(company_dict)} companies:")
        for cik in company_dict.keys():
            print(f"  Company Name: {company_dict[cik][0]}")
            print(f"  CIK: {cik}")
            print("-" * 30)
    else:
        print("No company data found")
