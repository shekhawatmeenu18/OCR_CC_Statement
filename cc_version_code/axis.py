import re
import parse
import pdfplumber
import pandas as pd
from collections import namedtuple
import numpy as np


def get_axis_statement(file):
  tab = pd.DataFrame(columns = [0,1,2,3,4])
  lines = []
  lines2 = []
  total_check = 0
  customer_name, account_no, bank_name, doctype= None, None, None, None
   
  # Regular Expression to serach key words
  customer_name_re = re.compile(r'Name.*')
  bank_name_re = re.compile(r'.*Statement$')
  line_re = re.compile(r'\d{2}/\d{2}/\d{4} . \d{2}/\d{2}/\d{4} \d{2}/\d{2}/\d{4} \d{2}/\d{2}/\d{4}')
  second_re = re.compile(r'\d+[*]+\d+\s\d')

  # Col names
  Line = namedtuple('Line', 'Customer_Name Bank_Name Total_Payment_Due A Minimum_Payment_Due B Statement_Period C D Payment_Due_Date Statement_Generation_Date')
  Line2 = namedtuple('Line2', 'Card_no Credit_limit Available_Cr_Limit Available_Cash_Limit')

  with pdfplumber.open(file) as pdf:
      pages = pdf.pages
      for no,page in enumerate(pages):
        if no<len(pages)-1:
          # print(page)
          text = page.extract_text()
          table = page.extract_table()
          tab2 = pd.DataFrame(table)

          # For Summary Report
          for line in text.split('\n'):            
            comp = customer_name_re.search(line)
            if comp:
                customer_name = comp[0]
                customer_name = customer_name.replace('Name','').strip()
                # print(customer_name)

            bank = bank_name_re.search(line)
            if bank:
                bank_name = bank[0]
                # print(bank_name)

            elif line_re.search(line):
                items = line.split()
                lines.append(Line(customer_name, bank_name, *items))

            elif second_re.search(line):
                items2 = line.split()
                acc_no,Credit_limit,Available_Cr_Limit,Available_Cash_Limit = items2[0],items2[1],items2[2],items2[3]
                lines2.append(Line2(acc_no,Credit_limit,Available_Cr_Limit,Available_Cash_Limit))
        
          # For Transaction table extraction
          row_data = []
          for row_index, row in tab2.iterrows():
            if ('End of Statement' in row.tolist() or 'Name' in row.tolist() or 'Card No:' in row.tolist()):
              continue
            elif (row.isna().sum(axis=0))>=len(row)-2:
              continue
            else:
              row_data.append(row)

          try:
            tab2 = pd.DataFrame(row_data).dropna(axis=1).reset_index(drop=True)
            tab2.columns = [0,1,2,3,4]
            tab = pd.concat([tab,tab2],axis =0,ignore_index = True)
          except: pass

      tab.drop_duplicates(inplace=True)
      tab = tab.replace({'': np.nan}).dropna(how = 'all')
      tab.reset_index(drop=True)

      for i,elt in enumerate(list(lines[0])):
        if elt == None:
          temp = list(lines[i])
          temp[0] = customer_name
          lines[i] = tuple(temp)
          
      df1 = pd.DataFrame(lines)
      df1.columns = ['Customer_Name', 'Bank_Name', 'Total_Payment_Due', 'A' ,'Minimum_Payment_Due', 'B', 'Statement_Period', 'C', 'D', 'Payment_Due_Date', 'Statement_Generation_Date']
      df1['Statement_Period'] = df1['Statement_Period'] +' '+ df1['C'] +' '+ df1['D']
      df1.drop(['A','B','C','D'],axis=1,inplace=True)
      df2 = pd.DataFrame(lines2)

      df = pd.concat([df1,df2],axis=1)
      # df.T
  return df.T,tab

