# import re
# import parse
# import csv
import pdfplumber
# from tika import parser
import pandas as pd
# import numpy as np
import glob
# import os
# import re
# import sys
import pathlib
import ntpath
# import matplotlib
from pandas import ExcelWriter
# import matplotlib.pyplot as plt


from cc_version_code.sbi import get_sbi_statement
from cc_version_code.amex import get_amex_statement
from cc_version_code.axis import get_axis_statement
from cc_version_code.citi import get_citi_statement
from cc_version_code.icici import get_icici_statement


# Data Location and dic for name match
input_location = pathlib.Path(r"D:\\VS Code Projects\\OCR_CC\\input_data\\ICICI\\ICICI.pdf")
keyword_callback_map = {}
axis_keyword = ['axis', 'axis bank',]
amex_keyword = ['American','American Express']
sbi_keyword = ['SBI','State Bank of India']
citi_keyword = ['citi','CITI','CITI BANK']
icici_keyword = ['ICICI','ICICI BANK']

keyword_callback_map.update(dict.fromkeys(axis_keyword, get_axis_statement))
keyword_callback_map.update(dict.fromkeys(amex_keyword, get_amex_statement))
keyword_callback_map.update(dict.fromkeys(sbi_keyword, get_sbi_statement))
keyword_callback_map.update(dict.fromkeys(citi_keyword, get_citi_statement))
keyword_callback_map.update(dict.fromkeys(icici_keyword, get_icici_statement))


# Move new not found cases here
def move_this_file(file):
  sheet = ntpath.basename(file)
  print('PDF Name:', sheet)


# Function to check keyword
def get_cc_statement(file):
  for lookup_string in list_items:
    for keyword in keyword_callback_map.keys():
      if(keyword in lookup_string):
        return keyword_callback_map[keyword](file)
      
  move_this_file(file)
  return 'File not found', None


# Run all files in loop
for doc in input_location.glob('**/*pdf'):
  print("file_loc:",doc)
  sheet = ntpath.basename(doc).rstrip('.pdf')
  with pdfplumber.open(str(doc)) as pdf:
      pages = [pdf.pages[0]]
      for no,page in enumerate(pages):
        text = page.extract_text()
        list_items = text.split('\n')

      summary, df_txn = get_cc_statement(str(doc))
      if summary.empty:
        pass
      else:
        if 'Axis' in sheet:
          with pd.ExcelWriter('E:/OCR_CC/output/final_statements/'+ sheet +'_Output.xlsx' ,date_format='DD-MM-YYYY') as writer:
            summary.to_excel(writer, sheet_name='Summary',header=False)
            df_txn.to_excel(writer, sheet_name='Transactions',index=False,header=False)
        else:
          with pd.ExcelWriter('E:/OCR_CC/output/final_statements/'+ sheet +'_Output.xlsx' ,date_format='DD-MM-YYYY') as writer:
            summary.to_excel(writer, sheet_name='Summary',index=False)
            df_txn.to_excel(writer, sheet_name='Transactions',index=False)
  # break
