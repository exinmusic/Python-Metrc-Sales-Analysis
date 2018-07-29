#!/usr/bin/env python2

#import pandas lib
import pandas as pd
import difflib
import matplotlib.pyplot as plt

#load METRC inventory xlsx file
xl = pd.ExcelFile('<METRC ACTIVE PACKAGES .xlsx>')
metrc_inv = xl.parse('Sheet1')
#load POS sales csv file
pos_sales = pd.read_csv('<POS SALES .csv>')
#rename abbreviated columns
metrc_inv.rename(columns = {"<abbr title='Received'>Rcv'd</abbr>":"Rcv",
							"<abbr title='Production Batch'>P.B.</abbr>":"Batch",
							"<abbr title='Production Batch'>P.B.</abbr> No.":"Batch No.",
							"<abbr title='Administrative Hold'>A.H.</abbr>":"A.H",
							"<abbr title='Packaged Date'>Date</abbr>":"Package Date"}, inplace = True)

# In pos_sales, check length of tag
tag_counter = [len(str(x)) for x in pos_sales['tag']]
pos_sales['tag size'] = pd.Series(tag_counter).values


pos_sales_wrongsize = pos_sales[pos_sales['tag size'] != 24]
pos_sales_badtag = pos_sales_wrongsize[pos_sales_wrongsize['tag size'] != 3]
pos_sales_notag = pos_sales_wrongsize[pos_sales_wrongsize['tag size'] == 3]


fixedtags =[]
for malformed_tag in pos_sales_badtag.tag.values:
	try:
		layer1 = difflib.get_close_matches(malformed_tag, metrc_inv.Tag.values)[0]
		if layer1[-4:] == malformed_tag[-4:]:
			fixedtags.append(layer1)
		else:
			fixedtags.append(False)  
	except:
		fixedtags.append(False)

pos_sales_badtag['tag suggestion'] = pd.Series(fixedtags).values
pos_sales_badtag = pos_sales_badtag[pos_sales_badtag['tag suggestion']!=False]

# Plot of tags with the wrong size
pos_sales_wrongsize.set_index(pd.DatetimeIndex(pos_sales_wrongsize.time), inplace=True)
missingplot = pos_sales_wrongsize.groupby(pos_sales_wrongsize.index.date).time.count().plot()
missingplot.set_xlabel('Daily reports')
missingplot.set_ylabel('Items sold with wrong-size/missing tags')
# Plot of tags fixed
pos_sales_badtag_ndx = pos_sales_badtag.set_index(pd.DatetimeIndex(pos_sales_badtag.time))
fixedplot = pos_sales_badtag_ndx.groupby(pos_sales_badtag_ndx.index.date).time.count().plot()
fixedplot.set_xlabel('Reports')
fixedplot.set_ylabel('Items retagged for reporting')
# format
if 'tag suggestion' in pos_sales_badtag.columns:
	pos_sales_badtag['tag'] = pos_sales_badtag['tag suggestion'].values
	del pos_sales_badtag['tag suggestion']
	del pos_sales_badtag['tag size']
pos_sales_badtag.head()
# check for patient info
patientReport = pos_sales_badtag[(pos_sales_badtag['Unnamed: 2'].notnull())&(pos_sales_badtag.client == 'Patient')]
consumerReport = pos_sales_badtag[pos_sales_badtag.client != 'Patient'] 
patientEntropy = str(pos_sales_badtag.client.count()-(consumerReport.client.count()+patientReport.client.count()))
print '{0} rows removed due to missing patient ID\'s.'.format(patientEntropy)

corrections = pd.concat([patientReport,consumerReport])
corrections.sort_index(inplace=True)

filename = str(corrections.tag.count())+'_sales_from_2017_length_errors.csv'
corrections.to_csv(filename, index=False, header=0)
print('Saved report as {0}'.format(filename))
