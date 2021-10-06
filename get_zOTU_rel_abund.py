#! /usr/bin/env python3

import sys
if len(sys.argv) != 3:
   sys.exit('This script calculates relative abundance for zOTUs given an OTU list, and creates a new file with the OTU as file name containing all zOTUs for that OTU. It needs the following inputs: otu_list.txt, Decontaminated_zOTU.table\n'
             'Usage: ./get_zOTU_rel_abund.py <otu_list.txt> <Decontaminated_zOTU.table>\n')

Script, InputFileName1, InputFileName2 = sys.argv


## Creating dictionary where the key is OTUs. 

count_dict = {}
with open('otu_list_separate.txt', 'r') as OTU_LIST:
   for line in OTU_LIST:
       LINE = line.strip('\t\n')
       count_dict[LINE] = []
   OTU_LIST.close()
   
with open('Decontaminated_zOTU_table_separate.txt', 'r') as COUNT_TABLE:
   headings = COUNT_TABLE.readline().strip('\t\n').split('\t')
   for line in COUNT_TABLE:
       LINE = line.strip('\t\n').split('\t')
       check_count = LINE[1] in count_dict
       if check_count is True:
           count_dict[LINE[1]].append(LINE)
   COUNT_TABLE.close()
   
## creating one file for each OTU. 
 
for key in count_dict.keys():
   for list in count_dict[key]:
       OUT = open(key + '.txt', 'w')
       print(headings, '\n', *list, file = OUT)
       
for key in count_dict.keys():
   OUT = open(key + '.txt', 'w')
   print(*headings, file = OUT)
   for list in count_dict[key]:
       print(*list, file = OUT)
   OUT.close()

## Calculating relative abundance, get table format. 

def get_headings():
   global Count_table
   Count_table = []
   headings = TABLE.readline().strip('\t\n').split()
   for i in range(0, len(headings)):
       Count_table.append([headings[i]])
   for line in TABLE: 
       line = line.strip('\t\n').split()
       Count_table[0].append(line[0])
       Count_table[1].append(line[1])
       Count_table[2].append(line[2])
       Count_table[3].append(line[3])
       Count_table[4].append(line[4])
       Count_table[-1].append(line[-1])
       for i in range(5, len(headings)-1):
           Count_table[i].append(int(line[i]))

def str_columns(): 
   global Count_table
   Count_table[0].append('Sum of counts')
   Count_table[1].append('NA')
   Count_table[2].append('NA')
   Count_table[3].append('NA')
   Count_table[4].append('NA')
   Count_table[-1].append('NA')

def sum_columns():
   global Count_table
   for column_no in range(5, len(Count_table)-1):
       Sum = 0
       for row_no in range(1, len(Count_table[column_no])):
           Sum += Count_table[column_no][row_no]
       Count_table[column_no].append(Sum)

def rel_ab():
   global Count_table
   for column_no in range(5, len(Count_table)-1):
       for row_no in range(1, len(Count_table[column_no])-1):
           if Count_table[column_no][-1] > 0:
               Count_table[column_no][row_no] /= Count_table[column_no][-1]
       

## Create one file for each OTU.

for key in count_dict.keys():
   with open(key + '.txt', 'r') as TABLE:
       get_headings()
       TABLE.close()
   str_columns()
   sum_columns()
   rel_ab()
   OUT = open(key + '_rel_abund.txt', 'w')
   for row_no in range(0, len(Count_table[0])-1):
       for column in Count_table:
           print(column[row_no], '\t', end = '', sep = '', file = OUT)
       print('\n', end = '', sep = '', file = OUT)
   OUT.close()
