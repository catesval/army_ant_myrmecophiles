###### Reading input count_table as a list of lists. Lists correspond to columns, and indexes to rows.
###### Row #0 - headings; Column #0 - Unique genotype names; Column #1 - Total counts for given genotype
import sys

TABLE = open(Input_count_table, 'r')
headings = TABLE.readline().strip('\t\n').split('\t')
Count_table = []

len_headings = len(headings)

for i in range(0, len(headings)):
   Count_table.append([headings[i]])

counter = 0

### storing first columns and checking for discrepancies betweenn headers and rows lenght. 
for line in TABLE: 
    line = line.strip('\t\n').split('\t')
    if len(line) != len_headings:
        print(line, "the problem is in line:", counter)
        #sys.exit()
    Count_table[0].append(line[0])
    Count_table[1].append(line[1])
    Count_table[2].append(line[2])
    for i in range(3, len(headings)):
       Count_table[i].append(int(line[i]))
    counter += 1 
 
### For each column except 0-4, calculating sum of counts from previous rows, and saving it in a newly created last row

Count_table[0].append('Sum of counts')

for column_no in range(4, len(Count_table)):
   Sum = 0
   for row_no in range(1, len(Count_table[column_no])):
      Sum += Count_table[column_no][row_no]
   Count_table[column_no].append(Sum)

### Converting counts into relative abundance
for column_no in range(4, len(Count_table)):
   for row_no in range(1, len(Count_table[column_no])-1):
      Count_table[column_no][row_no] /= Count_table[column_no][-1]

OUT = open(Output_rel_abund, 'w')
      
### printing output
for row_no in range(0, len(Count_table[0])-1):
    for column in Count_table:
        print(column[row_no], '\t', end = '', sep = '', file = OUT)
    print('\n', end = '', sep = '', file = OUT)
OUT.close()
