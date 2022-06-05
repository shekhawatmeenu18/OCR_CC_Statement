import re
import parse
import pdfplumber
from tika import parser
import pandas as pd
import numpy as np
import re
import pandas as pd

def get_amex_statement(amex):
  second_re = re.compile(r'(.*[a-zA-Z\s]) ([0-9]{1}.+) ([A-Za-z\s].*) ([0-9].*)')
  bank_name_re = re.compile(r'^Statement')

  with pdfplumber.open(amex) as pdf:
      pages = pdf.pages
      row_data = []
      summary_row_data = []
      for no,page in enumerate(pages):
        text = page.extract_text()
        table = page.extract_table()
        pdfs = text.replace('\n\n', '\n')
        summary_row_data.append(pdfs)

        for line in text.split('\n'):
          if bank_name_re.search(line):
                continue
          elif second_re.search(line):
            row_data.append(line)
  
  pdf = ''.join(summary_row_data)
  list_items = pdf.split('\n')

  # Table for transactions
  pattern = ['\D+\s\D+|GST/IGST@18%','(\d+[.,]).+','[A-Za-z]+\s\d{1}.[A-Z|\s]',] # Normal trxn, with brackets trxn #[A-Za-z]+\s\d{2}\s

  trxn_desc = []
  amt_desc = []
  date_desc = []
  CrDr = []

  for item in row_data:
    for row,patt in enumerate(pattern):
      # Transaction Description
      if row==0:    
        trnx_pattern = re.compile(r'(\d+[.,]).+')
        line_match = re.search(trnx_pattern, item)
        pb2 = re.compile(r'[A-Za-z]+\s\d{1}.[A-Z|\s]')
        cache2 = re.search(pb2,item)
        value = item.strip(line_match[0]).strip(cache2[0]).strip()
        trxn_desc.append(value)
        if ('THANK YOU' in value or 'Thank you' in value):
          CrDr.append('CR')
        else:
          CrDr.append('DR')

      # Amount 
      elif row==1:
        trnx_pattern = re.compile(str(patt),re.I)
        line_match = re.search(trnx_pattern, item)
        amt_desc.append(line_match[0])

      else: # Date 
        trnx_pattern = re.compile(str(patt),re.I)
        line_match = re.search(trnx_pattern, item)
        date_desc.append(line_match[0][:-1])

  trnx_table = pd.DataFrame(list(zip(date_desc, trxn_desc,amt_desc,CrDr)),
                columns =['Date', 'Trxn Description', 'Amount','CrDr'])


  # Summary details
  keys = ['Bank','Prepared for Membership Number Date','Opening Balance NewCredits','CreditSummary CreditLimitRs AvailableCreditLimitRs','Minimum Payment Due',]
  tab = {'Description': [], 'Pair_Value':[]}

  for key in keys:
    if key in ('Bank'):
      tab['Description'].append('Bank Name')
      tab['Pair_Value'].append('American Express Credit Card')

    if key in ('Prepared for Membership Number Date'):
      pb = re.compile(key + r'\n.*')
      cache = re.search(pb, pdf)
      patt = '[XXXX-XXXXXX-]+\d+\s[\d/]+'
      pb2 = re.compile(str(patt)+ r'.*')
      cache2 = re.search(pb2,pdf)
      value = re.sub(key + r'\n', '', cache[0]).rstrip('\n').strip(cache2[0])
      # print(value)
      tab['Description'].append('Customer Name')
      tab['Pair_Value'].append(value)

    if key in ('Opening Balance NewCredits'):
      pb = re.compile(r'Opening Balance.*\n.*\n.*')
      cache = re.search(pb, pdf)
      value = re.sub(r'.*\n', '', cache[0]).rstrip('\n').strip().replace('-','').replace('+','').replace('=','').split(' ')
      value = [x for x in value if x]
      mapping = ['Opening Balance','New Credits','New Debits','Closing Balance','Min Payment Due']
      for map, val in zip(mapping,value[:-1]):
        tab['Description'].append(map)
        tab['Pair_Value'].append(val)

    if key in ('CreditSummary CreditLimitRs AvailableCreditLimitRs'):
      pb = re.compile(key + r'\n.*')
      cache = re.search(pb, pdf)
      value = re.sub(key+ r'\n', '', cache[0]).rstrip('\n').strip().split(' ')
      mapping = ['Credit Limit','Available Credit Limit']
      for map,val in zip(mapping,value[1:]):
        tab['Description'].append(map)
        tab['Pair_Value'].append(val)

      pb2 = re.compile(r'.*\n'+ key)
      cache2 = re.search(pb2, pdf)
      value2 = re.sub(r'\n'+key, '', cache2[0]).rstrip('\n').strip()
      value3 = re.sub('StatementPeriod From', '', value2).rstrip('\n').strip()
      tab['Description'].append('Statement Period')
      tab['Pair_Value'].append(value3)

    if key in ('Minimum Payment Due'):
      pb = re.compile(key + r'\n.*')
      cache = re.search(pb, pdf)
      value = re.sub(key+ r'\n', '', cache[0]).rstrip('\n').strip()
      tab['Description'].append('Payment Due Date')
      tab['Pair_Value'].append(value)


  return pd.DataFrame(tab),trnx_table