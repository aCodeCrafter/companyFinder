This is a project I started in July of 2025, where I attempted to create a bot that scraped the SEC's EDGAR platform for publicly traded companies, and identify ones that are both growing and in technology fields, so I could build prospect lists for interesting companies who may be more likely to hire undergrads.

The SEC has a database of publicly traded companies known as EDGAR that allows the public to browse various companies in different industries. They also have an API for finding basic facts about a company based on the company's filings (at least the filings that were correctly tagged). Unfortunately, however, the EDGAR database is only available in HTML, which means that if we want access to it, we'll have to parse the results. To do this, we'll use Beautiful Soup.

Fortunately for us, parsing the tables provided in the EDGAR interface is fairly simple. Beautiful Soup allows us to find the table containing the information in EDGAR and iterate through each row to process data. The following code does this:

```
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
 text: html from SEC EDGAR
 Returns:
 Dictionary with cik number as key, and company name.
 If there is no table found, return an empty dict
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
 company_dict[temp[0]] = temp[1]
 return company_dict
```

Once we have the data parsed, we place it into a dictionary (where the key is the CIK number, and the value is the company name) and pass it off to the rest of the program. This is because once we have the cik number, we can query the Company Facts *https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json* for revenue data on each of the companies we found in EDGAR.

That said, the Company Facts API doesn't always list revenue consistently. The filing data for Alphabet Inc. lists its data under *Revenues*, while Vimeo lists it under *RevenueFromContractWithCustomerExcludingAssessedTax*. To get around this, I provided the function with a list of matching phrases that could be used for revenue. I used a list because I may want to reuse this function in the future to gather different metrics that may require more phrases.
```
def getCompanyRevenue(cik, terms=['Revenues','RevenueFromContractWithCustomerExcludingAssessedTax']):
 """
 Query the company facts on data.sec.gov to find gross profit over different quarters.
 Accepts:
 cik: the company's cik number (as string, so leading zeros aren't discarded)
 terms: different terms for the same metric
 Returns:
 Dictionary with gross profit for a number of years
 """
 url=f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'
 headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
 resp = requests.get(url=url,headers=headers)
 term = ''
 for i in terms:
 if i in resp.json()['facts']['us-gaap'].keys():
 term = i
 return resp.json()['facts']['us-gaap'][term]['units']['USD']
```

After I had a list of revenue data from Fact Finder, I wanted a way to calculate growth indicators. I decided on using the Average Year over Year for all the company's history (at least as was present in the Company Facts database) and the Year over Year change for the last reported year. So I used the formula (Current Year Value - Previous Year Value) / Previous Year Value. However, I also found that there were multiple filings for the same form and the same period. I suspect that these are the result of amended filings with the SEC, so I used the most recent filings for a given period.

```
def growthFinder(grossProfit):
 """
 Quantify growth based on multiple Gross Profit statements
 Accepts: 
 grossProfit: list of dictionaries, each in the form {
 "start": "2025-04-01",
 "end": "2025-06-30",
 "val": 81503000,
 "accn": "0001837686-25-000093",
 "fy": 2025,
 "fp": "Q2",
 "form": "10-Q",
 "filed": "2025-08-04",
 "frame": "CY2025Q2"
 }
 Returns:
 Dictionary with Average YoY Gross Profit growth (using all available years of data), and the previous years' YoY growth.
 The YoY growth was calculated as (Current Year Value - Previous Year Value) / Previous Year Value.
 """
 # Find most recent filings for each full year
 fullYearData = dict() #Key: year. Value: gross profit
 for data in grossProfit:
 if data['form'] == '10-K': # If it's the right form and a more recent filing / the filing has not been encountered yet
 if data['fy'] in fullYearData.keys():
 if data['filed'] > fullYearData[data['fy']]['filed']:
 fullYearData[data["fy"]] = data
 else:
 fullYearData[data["fy"]] = data

 # Find average year over year growth
 fullYearList = sorted(fullYearData.items())
 yearDiffs = []
 for i in range(1,len(fullYearList)):
 if (fullYearList[i-1][1]['val'] != 0):
 yearDiffs.append((fullYearList[i][1]['val']-fullYearList[i-1][1]['val'])/fullYearList[i-1][1]['val'])
 return {"Ave YoY Growth":sum(yearDiffs)/len(yearDiffs),
 "Prev YoY Growth":(fullYearList[-1][1]['val']-fullYearList[-2][1]['val'])/fullYearList[-2][1]['val']}
```

One thing I noticed about the Company Facts database is that it doesn't have the data for all the companies in EDGAR. Many of the CIKs found in EDGAR produce an error when put into Company Facts. Apparently, not all the filings with the SEC were submitted with machine-readable tags; many were probably just submitted as PDF files. So that said, for now I would like to print a brief error when a company's company facts were not found, and provide an option to hide the companies that don't have Company Facts data. If I were to continue this project in the future, I might see if it is possible to process PDF files (possibly using an LLM) to extract more company revenue data.

Once it was all stitched together, I was able to get it working with a terminal interface.

```
Enter State Abbreviation (NY, CA, etc.): NY
Enter CIK Number: 7370
Include companies w/ out company fact data (y/n): n
Progress: 28/28
Found 28 companies:
------------------------------
Company Name: AdTheorent Holding Company, Inc.
CIK: 0001838672
Ave YoY Growth: 18.54%
Prev YoY Growth: 0.43%
------------------------------
Company Name: DoubleVerify Holdings, Inc.
CIK: 0001819928
Ave YoY Growth: 35.31%
Prev YoY Growth: 35.97%
------------------------------
Company Name: Function(x) Inc.
CIK: 0000725876
Ave YoY Growth: 165.61%
Prev YoY Growth: -68.45%
------------------------------
Company Name: IAC Inc.
CIK: 0001800227
Ave YoY Growth: 21.14%
Prev YoY Growth: 41.51%
------------------------------
Company Name: INTEGRAL AD SCIENCE HOLDING CORP.
CIK: 0001842718
Ave YoY Growth: 24.46%
Prev YoY Growth: 26.22%
------------------------------
Company Name: MAGNITE, INC.
CIK: 0001595974
Ave YoY Growth: 40.34%
Prev YoY Growth: 23.2%
------------------------------
Company Name: Moxian, Inc.
CIK: 0001516805
Ave YoY Growth: 8.96%
Prev YoY Growth: 8.96%
------------------------------
Company Name: Synacor, Inc.
CIK: 0001408278
Ave YoY Growth: -1.18%
Prev YoY Growth: -15.31%
------------------------------
Company Name: Taboola.com Ltd.
CIK: 0001840502
Ave YoY Growth: 8.8%
Prev YoY Growth: 1.65%
------------------------------
Company Name: Teads Holding Co.
CIK: 0001454938
Ave YoY Growth: 13.89%
Prev YoY Growth: -2.32%
------------------------------
Company Name: Vimeo, Inc.
CIK: 0001837686
Ave YoY Growth: 31.11%
Prev YoY Growth: 10.56%
------------------------------
```

This was a fun little project, and it really makes me wonder what else I could do with this data beyond prospecting potential employers. I wonder if a system like this would be useful in making a paper trading algorithm. But those are questions for another day. The code is available [on my github](https://github.com/aCodeCrafter/companyFinder) if anyone wants to check it out and try it for themselves.