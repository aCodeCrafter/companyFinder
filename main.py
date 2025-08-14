from companyInfo import growthFinder, getCompanyRevenue
from scrapeEDGAR import scrape_edgar
def main():
    while True:
        state_code = input("Enter State Abbrieviation (NY, CA, etc.): ")
        sic_code = input("Enter CIK Number: ") #'7370'
        if len(sic_code) < 1 or len(state_code) < 1:
            print("Please enter State and SIC codes")
        else:
            break
    includeNoData = input("Include companies w/ out company fact data (y/n): ")[0] == 'y'
    company_dict = scrape_edgar(state_code,sic_code)
    companyGrowthDict = dict()

    # Get the YoY Growth for each company
    tempList = sorted(company_dict.items())
    for i in range(len(tempList)):
        # print(company_dict[tempList[i][0]])
        try:
            companyGrowthDict[tempList[i][0]] = growthFinder(getCompanyRevenue(tempList[i][0]))
        except Exception as e:
            companyGrowthDict[tempList[i][0]] = {'Ave YoY Growth':None,'Prev YoY Growth':None}
        # Progress Bar
        print(f"\rProgress: {i+1}/{len(tempList)}", end="")
    print()

    # Display Results
    if len(company_dict) > 0:
        print(f"Found {len(company_dict)} companies:")
        print("-" * 30)
        for cik in company_dict.keys():
            if companyGrowthDict[cik]['Ave YoY Growth'] is not None or includeNoData:
                print(f"Company Name: {company_dict[cik]}")
                print(f"CIK: {cik}")
                if companyGrowthDict[cik]['Ave YoY Growth'] is not None:
                    print(f"Ave YoY Growth: {round(companyGrowthDict[cik]['Ave YoY Growth']*100,2)}%")
                    print(f"Prev YoY Growth: {round(companyGrowthDict[cik]['Prev YoY Growth']*100,2)}%")
                else:
                    print("ERROR retrieving company data")
                print("-" * 30)
    else:
        print("No company data found")
if __name__ == "__main__":
    main()
