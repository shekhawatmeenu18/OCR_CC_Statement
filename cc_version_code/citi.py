import re
import parse
import pdfplumber
import tika
from tika import parser
import pandas as pd
import numpy as np
import re
import pandas as pd
import urllib.parse

def get_citi_statement(file):
  content_pattern = re.compile(r'\d{2}[/]\d{2}\s\d{5}.*')
  line_pattern = re.compile(r'[A-Za-z].+',re.I)
  trnx = {'Date': [] ,'Reference No': [] ,'Transaction Details': [],'Amount': []}

  keys = ['Customer Name','Statement Date','Total Amount Due','Minimum Amount Due','Due Date','Credit Limit','Available Credit Limit','Available Cash Limit ','Previous balance','Current Purchases & Other Charges','Current Cash Advance','Last Payments Received']
  tab = {'Description': [], 'Pair_Value':[]}

  content_match = []
  parsedPDF = parser.from_file(file)

  pdf = parsedPDF["content"]
  pdf = pdf.replace('\n\n', '\n')
  df = pdf.split('\n')
  
  # Extract transaction details 
  for pdf_content in df:
    content = re.search(content_pattern, pdf_content)
    if content==None:
      continue
    else:
      content = content[0]
      content_match.append(content)

  # Table from extracted transactions
  for row,item in enumerate(content_match):
      line_match = re.search(line_pattern, item)
      a = line_match[0].split(' ')
      b = item.split(' ')
      Date = ' '.join(b[:1])
      Ref = ' '.join(b[1:2])
      Amt = a[-1]
      Trxn_Des = ' '.join(a).rstrip(Amt)
      trnx['Date'].append(Date)
      trnx['Reference No'].append(Ref)
      trnx['Transaction Details'].append(Trxn_Des)
      trnx['Amount'].append(Amt)

  # Summary details
  for key in keys:
    pb = re.compile(key + r'.*\n.*\n')
    cache = re.search(pb, pdf)
    value = re.sub(key + r'.*\n', '', cache[0]).rstrip('\n').strip()
    tab['Description'].append(key)
    tab['Pair_Value'].append(value)

  summary = pd.DataFrame(tab)
  df_txn = pd.DataFrame(trnx)
  return summary,df_txn


# file = r"E:/OCR_CC/input_data/citi/citi4.pdf"
# summary,df_txn = get_citi_statement(file)

# print(summary)