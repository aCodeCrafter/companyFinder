import requests
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
import json
import datetime
from time import sleep

def getCompanyGrossFact(cik, terms=['Revenues','RevenueFromContractWithCustomerExcludingAssessedTax']):
  """
  Queries company facts on data.sec.gov to find gross profit over different quarters.
  Accepts:
    cik: the company's cik number (as string so leading zeros arent discarded)
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
    Dictionary with Average YoY Gross Profit growth (using all available years of data), and the previous years YoY growth.
    The YoY growth was calculated as (Current Year Value - Previous Year Value) / Previous Year Value
  """
  # Find most recent filings for each full year
  fullYearData = dict() #Key: year. Value: gross profit
  for data in grossProfit:
    if data['form'] == '10-K': # If its the right form and a more recent filing / the filing has not been encountered yet
      if data['fy'] in fullYearData.keys():
        if data['filed'] > fullYearData[data['fy']]['filed']:
          fullYearData[data["fy"]] = data
      else:
        fullYearData[data["fy"]] = data

  # Find average year over year growth
  fullYearList = sorted(fullYearData.items())
  yearDiffs = []
  for i in range(1,len(fullYearList)):
    yearDiffs.append((fullYearList[i][1]['val']-fullYearList[i-1][1]['val'])/fullYearList[i-1][1]['val'])
  return {"Ave YoY Growth":sum(yearDiffs)/len(yearDiffs),
          "Prev YoY Growth":(fullYearList[-1][1]['val']-fullYearList[-2][1]['val'])/fullYearList[-2][1]['val']}


if __name__ == "__main__":
  print(growthFinder(getCompanyGrossFact('0001652044')))