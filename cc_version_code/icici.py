import re
import parse
import pdfplumber
import pandas as pd
from collections import namedtuple
import numpy as np


def get_icici_statement(file):
  tobe_removed = ['`','(cid:235)(cid:173)(cid:201)(cid:201)(cid:201)(cid:173)(cid:235)(cid:108)(cid:213)(cid:230)(cid:109)(cid:176)(cid:205)(cid:190)(cid:229)(cid:216)(cid:225)(cid:118)(cid:127)(cid:130)(cid:111)(cid:206)(cid:203)(cid:168)(cid:135)(cid:132)(cid:217)(cid:120)(cid:233)(cid:108)(cid:235)(cid:173)(cid:201)(cid:201)(cid:201)(cid:173)(cid:235)',
                '(cid:204)(cid:140)(cid:140)(cid:140)(cid:140)(cid:140)(cid:204)(cid:108)(cid:140)(cid:108)(cid:108)(cid:140)(cid:204)(cid:204)(cid:108)(cid:172)(cid:140)(cid:140)(cid:140)(cid:172)(cid:108)(cid:140)(cid:140)(cid:172)(cid:140)(cid:172)(cid:140)(cid:204)(cid:108)(cid:204)(cid:140)(cid:140)(cid:204)(cid:172)(cid:204)(cid:140)(cid:140)',
                'Interest will be charged if your','total amount due is not paid','All communications are being sent to your registered e-mail ID and mobile number',
                'l To update mobile number, visit the nearest ATM or branch Scan to Pay using (cid:170)(cid:217)(cid:134)(cid:225)(cid:158)(cid:108)(cid:145)(cid:161)(cid:112)(cid:139)(cid:158)(cid:177)(cid:150)(cid:193)(cid:146)(cid:135)(cid:190)(cid:220)(cid:212)(cid:195)(cid:186)(cid:222)(cid:109)(cid:117)(cid:194)(cid:173)(cid:231)(cid:233)(cid:215)(cid:233)(cid:158)(cid:111)(cid:185)(cid:111)(cid:135)(cid:131)(cid:162)(cid:117)(cid:119)(cid:213)(cid:200)(cid:178)(cid:139)(cid:178)(cid:140)(cid:137)(cid:215)(cid:111)(cid:116)(cid:119)(cid:114)(cid:188)(cid:218)(cid:180)(cid:179)(cid:112)(cid:169)(cid:109)(cid:120)(cid:153)(cid:151)(cid:214)(cid:127)(cid:115)(cid:119)(cid:111)(cid:148)(cid:225)(cid:115)(cid:200)(cid:141)(cid:169)(cid:143)(cid:168)']

  def clean_text(list_val):
    for remove_val in tobe_removed:
      # print(str(remove_val))
      try:
        list_val = [item.replace(str(remove_val), "") for item in list_val]
      except ValueError:
        pass

    while('' in list_val) :
        list_val.remove('')

    while(' ' in list_val) :
        list_val.remove(' ')

    return list_val

  second_re = re.compile(r'\d{2}[/]\d{2}[/]\d{4}\s\d+\s[A-Za-z\s.:,//-]+')

  with pdfplumber.open(file) as pdf:
      pages = pdf.pages
      row_data = []
      summary_row_data = []
      for no,page in enumerate(pages):
        text = page.extract_text()
        table = page.extract_table()
        pdfs = text.replace('\n\n', '\n')
        summary_row_data.append(pdfs)

        for line in text.split('\n'):
          if second_re.search(line):
            row_data.append(line)

  pdf = ''.join(summary_row_data)
  list_items = pdf.split('\n')
  data_list = clean_text(list_items)
  pdf2 = '\n'.join(data_list)

  # Summary details
  keys = ['CREDIT CARD STATEMENT','STATEMENT DATE ','PAYMENT DUE DATE  branch ','Minimum Amount due CREDIT SUMMARY',]
  tab = {'Description': [], 'Pair_Value':[]}

  for key in keys:
    if key in ('CREDIT CARD STATEMENT'):
      pb = re.compile(key + r'\n.*\n.*\n.*')
      cache = re.search(pb, pdf)
      pb2 = re.compile(r'.cid.*')
      cache2 = re.search(pb2,pdf)
      value = re.sub(key + r'\n.*\n.*', '', cache[0]).rstrip('\n').strip(cache2[0]).strip(' Download the iMobile app to -').strip()
      tab['Description'].append('Customer Name')
      tab['Pair_Value'].append(value)

    if key in ('STATEMENT DATE '):
      pb = re.compile(key+ r'\n.*')
      cache = re.search(pb, pdf2)
      value = re.sub(key + r'\n', '', cache[0]).rstrip('\n').strip()
      tab['Description'].append('Statement Date')
      tab['Pair_Value'].append(value)

    if key in ('PAYMENT DUE DATE  branch '):
      pb = re.compile(key+ r'\n.*')
      cache = re.search(pb, pdf2)
      value = re.sub(key + r'\n', '', cache[0]).rstrip('\n').strip()
      tab['Description'].append('Payment Due Date')
      tab['Pair_Value'].append(value)

    if key in ('Minimum Amount due CREDIT SUMMARY'):
      pb = re.compile(r'.*\n.*\n'+key)
      cache = re.search(pb, pdf2)
      value = re.sub( r'\n.*\n'+key, '', cache[0]).rstrip('\n').strip(' = + + -').strip()
      tab['Description'].append('Total Amount due')
      tab['Pair_Value'].append(value)

    if key in ('Minimum Amount due CREDIT SUMMARY'):
      pb = re.compile(key+ r'\n.*')
      cache = re.search(pb, pdf2)
      value = re.sub(key + r'\n', '', cache[0]).rstrip('\n').strip()
      tab['Description'].append('Minimum Amount due')
      tab['Pair_Value'].append(value)

    if key in ('Minimum Amount due CREDIT SUMMARY'):
      pb = re.compile(key + r'\n.*\n.*\n.*')
      cache = re.search(pb, pdf2)
      value = re.sub(key + r'\n.*\n.*', '', cache[0]).rstrip('\n').strip().split(' ')
      mapping = ['Credit Limit','Available Credit Limit','Cash Limit','Available Cash Limit']
      for map,val in zip(mapping,value[:]):
        tab['Description'].append(map)
        tab['Pair_Value'].append(val)

  summary = pd.DataFrame(tab)

  # Table for transactions
  pattern = ['\d{2}[/]\d{2}[/]\d{4}','\s[A-Za-z://,.-].+'] #'\d\s\d+\s'
  ddesp_pattern = ['\d+\s[\d+,.]+'] #'\s[A-Za-z://,.-]+'

  date_desc = []
  trxn_desc = []
  amt_desc = []

  for item in row_data:
    for row,patt in enumerate(pattern):
      # Date 
      if row==0:
        trnx_pattern = re.compile(str(patt),re.I)
        line_match = re.search(trnx_pattern, item)
        date_desc.append(line_match[0])

      # Transaction Description
      if row==1:
        trnx_pattern = re.compile(str(patt),re.I)
        line_match = re.search(trnx_pattern, item)
        value = re.sub(r'\d+\s[\d+,.]+', '', line_match[0])
        trxn_desc.append(value)

        # Amount
        for num,desp in enumerate(ddesp_pattern):
          trnx_pattern3 = re.compile(str(desp),re.I)
          line_match3 = re.search(trnx_pattern3, line_match[0])
          value = line_match3[0].split(' ')
          del value[0]
          amt_desc.append(''.join(value))

  trnx_table = pd.DataFrame(list(zip(date_desc, trxn_desc,amt_desc)),columns =['Date', 'Trxn Description', 'Amount'])
  return summary,trnx_table
