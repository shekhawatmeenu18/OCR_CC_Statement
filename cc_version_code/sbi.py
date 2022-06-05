import re
import parse
import pdfplumber
from tika import parser
import pandas as pd
import numpy as np
import re
import pandas as pd

def get_sbi_statement(sbi):
  second_re = re.compile(r'(^\d{2}\s[A-Za-z]+\s)')

  with pdfplumber.open(sbi) as pdf:
    pages = pdf.pages
    for no,page in enumerate(pages):
      if no<len(pages)-5:
        # print(page)
        text = page.extract_text()
        table = page.extract_table()
        tab2 = pd.DataFrame(table)
        row_data = []

        # For all Transacitons
        for line in text.split('\n'):
          # print(line)
          if second_re.search(line):
            row_data.append(line)

    del row_data[0]
    pdf = text.replace('\n\n', '\n')
    list_items = pdf.split('\n')

    # Summary details
    keys = ['Credit Card Number','Total Amount Due','Minimum Amount Due','Available Credit Limit Available Cash Limit Payment Due Date','Credit Limit Cash Limit Statement Date']
    tab = {'Description': [], 'Pair_Value':[]}

    for key in keys:
      if key in ('Credit Card Number'):
        pb = re.compile(r'.*\n'+'Credit Card Number')
        cache = re.search(pb, pdf)
        value = re.sub(r'\n'+'Credit Card Number', '', cache[0]).rstrip('\n').strip()
        key_name = 'Customer Name'
        tab['Description'].append(key_name)
        tab['Pair_Value'].append(value)
        
        pb2 = re.compile(key + r'\n.*')
        cache = re.search(pb2, pdf)
        value2 = re.sub(key + r'\n', '', cache[0]).rstrip('\n').strip()
        tab['Description'].append(key)
        tab['Pair_Value'].append(value2)


      if key in ('Total Amount Due'):
        pb = re.compile(key + r'.*\n.*')
        cache = re.search(pb, pdf)
        value = re.sub(key + r'.*\n', '', cache[0]).rstrip('\n').strip()
        tab['Description'].append(key)
        tab['Pair_Value'].append(value)

      if key in ('Minimum Amount Due'):
        pb = re.compile(key + r'\n.*\n.*\n.*\n')
        cache = re.search(pb, pdf)
        value = re.sub(key +  r'.*\n.*\n.*\n', '', cache[0]).rstrip('\n').strip()
        tab['Description'].append(key)
        tab['Pair_Value'].append(value)

      if key in ('Credit Limit Cash Limit Statement Date'):
        key_3 = ['Credit Limit','Cash Limit','Statement Date']
        pb = re.compile('Credit Limit Cash Limit Statement Date' + r'\n.*\n.*\n.*')
        cache = re.search(pb, pdf)
        value = re.sub('Credit Limit Cash Limit Statement Date' + r'.*\n.*\n', '', cache[0]).strip('\n').strip().replace('\n',' ')
        a = value.split(" ")
        b = pd.DataFrame(a).T
        b[0] = b[0] +' '+ b[1]+' '+b[2]
        del b[1],b[2]

        for item in key_3:
          if item in ('Credit Limit'):
            tab['Description'].append(item)
            tab['Pair_Value'].append(b[3].iloc[0])

          if item in ('Cash Limit'):
            tab['Description'].append(item)
            tab['Pair_Value'].append(b[4].iloc[0])

          if item in ('Statement Date'):
            tab['Description'].append(item)
            tab['Pair_Value'].append(b[0].iloc[0])

      if key in ('Available Credit Limit Available Cash Limit Payment Due Date'):
        key_3 = ['Available Credit Limit','Payment Due Date','Available Cash Limit']
        pb = re.compile('Available Credit Limit Available Cash Limit Payment Due Date' + r'\n.*\n.*')
        cache = re.search(pb, pdf)
        value = re.sub('Available Credit Limit Available Cash Limit Payment Due Date' + r'.*\n', '', cache[0]).strip('\n').strip().replace('\n',' ')
        a = value.split(" ")
        b = pd.DataFrame(a).T
        b[1] = b[1] +' '+ b[2]+' '+b[3]
        del b[2],b[3]

        for item in key_3:
          if item in ('Available Credit Limit'):
            tab['Description'].append(item)
            tab['Pair_Value'].append(b[0].iloc[0])

          if item in ('Payment Due Date'):
            tab['Description'].append(item)
            tab['Pair_Value'].append(b[1].iloc[0])

          if item in ('Available Cash Limit'):
            tab['Description'].append(item)
            tab['Pair_Value'].append(b[4].iloc[0])

    summary = pd.DataFrame(tab)


    # Table for transactions
    pattern = [['\D+\s\D+','(\D+\s\D.+[)])']] # Normal trxn, with brackets trxn #(\D+\s\D+\d.+[)])
    date_amt_pattern = ['(\d+[.,]).+','\d{2}\s[A-Za-z]+\s\d{2}',] #Amount, Date

    trxn_desc = []
    amt_desc = []
    date_desc = []

    for item in row_data:
      for row,patt in enumerate(pattern):
        # Transaction Description
        if (len(patt)==2):
          trnx_pattern = re.compile(str(patt[0]),re.I)
          line_match = re.search(trnx_pattern, item)
          if '(' in line_match[0]:
            trnx_pattern = re.compile(str(patt[1]),re.I)
            line_match = re.search(trnx_pattern, item)
            line_match = re.search(trnx_pattern, item)
            if line_match==None:
              pass
            else:
              trxn_desc.append(line_match[0])
          else:
            trnx_pattern = re.compile(str(patt[0]),re.I)
            line_match = re.search(trnx_pattern, item)
            trxn_desc.append(line_match[0])      

      for row,patt in enumerate(date_amt_pattern):
        # Amount 
        if row==0:
          trnx_pattern = re.compile(str(patt),re.I)
          line_match = re.search(trnx_pattern, item)
          if ')' in line_match[0]:
            value = re.sub(r'.*[)]', '', line_match[0]).rstrip('\n').strip()
            amt_desc.append(value)
          else: 
            line_match[0]
            amt_desc.append(line_match[0])

        else: # Date 
          trnx_pattern = re.compile(str(patt),re.I)
          line_match = re.search(trnx_pattern, item)
          date_desc.append(line_match[0])

    trnx_table = pd.DataFrame(list(zip(date_desc, trxn_desc,amt_desc)),columns =['Date', 'Trxn Description', 'Amount'])
    
  return summary,trnx_table

