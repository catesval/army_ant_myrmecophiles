#! /usr/bin/env python3

import sys, os, re

if len(sys.argv) != 2:
    sys.exit("""ERROR! CHECK YOUR INPUT PARAMETERS!
Please provide the path to the directory with assembled fasta files for each sample:
/home/cata.valdivia/army_ants_fastq_files/study_samples/""")
Script, path_to_your_raw_data = sys.argv

print("Dereplicating data..................... ", end="")
os.system("""for file in *.fasta; do
    SampleName=`basename $file .fasta`
    vsearch -derep_fulllength $SampleName.fasta -output "$SampleName".derep.fasta -sizeout -uc "$SampleName".derep_info.txt
done""")

os.system("mkdir derep && mv *derep.fasta derep/")
os.chdir("derep")

###Dereplicating data - picking representative sequences:
os.system("""for file in *derep.fasta; do
    SampleName=`basename $file .derep.fasta`
    vsearch -sortbysize $SampleName.derep.fasta --output $SampleName.sorted.fasta -minsize 2
done""")

os.system("mkdir sorted && mv *sorted.fasta sorted/")
os.chdir("sorted")
print("OK!") 

print("Denoising..................... ", end="")

###Denoising:
### You can use -minsize option for example if you have very low number of reads in your libraries
os.system("""for file in *sorted.fasta; do
    SampleName=`basename $file .sorted.fasta`
    usearch -unoise3 $SampleName.sorted.fasta -zotus $SampleName.zotus.fasta -tabbedout $SampleName.denoising.summary.txt -minsize 1
done""")

os.system("mkdir denoising_summary && mv *denoising.summary.txt denoising_summary/")

os.system("""for file in *.fasta; do
    SampleName=`basename $file .zotus.fasta`
    usearch -otutab ../../"$SampleName".fasta -zotus $SampleName.zotus.fasta -otutabout "$SampleName"_zotu_table.txt -threads 60
done""")
print("OK!") 

print("Joining data from all the libraries into one table..................... ", end="")

###Adding sequence to zOTU_table with add_seq_to_zotu.py:
os.system("mkdir zOTUs && mv *zotu* zOTUs/")
os.chdir("zOTUs/")
os.system("""for file in *.fasta; do
    SampleName=`basename $file .zotus.fasta`
    ../../../../../add_seq_to_zotu.py "$SampleName"_zotu_table.txt "$SampleName".zotus.fasta "$SampleName"_zotu_table_with_seq.txt
done""")

os.system("mkdir raw_zotu && mv *_zotu_table.txt raw_zotu && mv *zotus.fasta raw_zotu")
os.system("mkdir zotu_tables_with_sequences && mv *zotu_table_with_seq.txt zotu_tables_with_sequences")



###Creating a dictionary with sequences as keys and nested dictionary as values. Nested dictionary uses names of libraries as keys and number of reads as values:

seq_dict = {}

def get_headings(file):
   global headings
   headings = file.readline().strip('\t\n').split('\t')
   
def get_lib_name(heading):
    global lib_name
    for i in range(0, len(headings)):
       lib_name = headings[2]

def create_library(Lib_info):
   global lib_dict
   for line in Lib_info:
        LINE = line.strip('\t\n').split('\t')
        key = LINE[1]
        counts = LINE[-1]
        if not key in seq_dict.keys():
        #Creating nested dictionary with library names as keys and counts as values
            seq_dict[key] = {lib_name : counts}
        else:
            seq_dict[key].update({lib_name : counts})

#Changing working directory to one with our zotu_tables_with_sequences
os.chdir(path_to_your_raw_data + "derep/sorted/zOTUs/zotu_tables_with_sequences")
cwd = os.getcwd()  # Get the current working directory (cwd)
files = os.listdir(cwd)

for filename in files:
   with open(filename, "r") as Lib_info:
       get_headings(Lib_info)
       get_lib_name(headings)
       create_library(Lib_info)

os.chdir(path_to_your_raw_data)

# Creating a list with the names of the libraries
libs = []
for k1 in seq_dict.keys():
    libs += [lib for lib in seq_dict[k1] if lib not in libs] #List comprehension
    
### Creating an empty list which will be our final table
data = []
index = 0 #index of a table in data, basically 0 will raw with the first key, 1 - with the second ect
for seq in seq_dict.keys():
    data.append(["",seq, 0]) ### append  empty zotu_ID, sequence, total (which is zero at the beginning)
    for lib in libs: #For every library in our list
        data[index].append(0 if lib not in seq_dict[seq].keys() else seq_dict[seq][lib]) #append 0 if library is not in keys of nested dictionary for given sequence
        if lib in seq_dict[seq].keys(): ### summing Total for every library in the keys of sequence
            data[index][2] += int(seq_dict[seq][lib])
    index += 1 #increase index of one and go to the next sequence
 

def byTotal(Total): ###  Function which will indicate what to sort by
    return Total[2]

headers = ["#OTU_ID"] + libs ### Creating a list with headers
with open("all_libraries_zotu_table.txt", 'w') as bigFile:
    element = ""
    for header in headers:
         element += header + "\t" 
    bigFile.write(element[:-1] + '\n')
    data.sort(key=byTotal, reverse = True)
    counter = 1
    for zotu in data:
         zotu[0] = "Zotu" + str(counter) 
         counter += 1
    for zotu in data:
        line = "" ###creating an empty string
        newData = [zotu[0]] + zotu[3:] ### adding ZOTU_ID and all the libraries to the list
        for element in newData:
            line += str(element) + "\t"
        bigFile.write(line[:-1] + '\n')

###Creating fasta file with sorted sequences of zOTUs:   
with open ("zotus.fasta", 'w') as fasta:
    for zotu in data:
        seq = ">" + zotu[0] + ";size=" + str(zotu[2]) + '\n' + zotu[1] + '\n'
        fasta.write(seq)
print("OK!") 

print("OTU picking and chimeras assignment..................... ", end="")
###OTU picking and chimeras removal using ASV as an input:
os.system("usearch -cluster_otus zotus.fasta -otus otus.fasta -relabel OTU -uparseout zotu_otu_relationships.txt -threads 60")
print("OK!") 

### Creating a new fasta file of zOTUs without information about the size:
os.system("sed -E 's/;size=[0-9].{0,}//g' zotus.fasta > new_zotus.fasta")

print("Assigning taxonomy..................... ", end="")
###Assigning taxonomy:
#Please pay attention to what cutoff value you want to use!
os.system("""vsearch --sintax new_zotus.fasta -db /mnt/matrix/symbio/db/SILVA_138/SILVA_endo_spikeins_RDP.fasta -tabbedout zotus.tax -strand both -sintax_cutoff 0.8
vsearch --sintax otus.fasta -db /mnt/matrix/symbio/db/SILVA_138/SILVA_endo_spikeins_RDP.fasta -tabbedout otus.tax -strand both -sintax_cutoff 0.8""")    
    
###Removing redundant info from out taxonomy files:
os.system("""sed -i 's/[dpcofgs]\://g' zotus.tax
sed -i 's/[dpcofgs]\://g' otus.tax""")
print("OK!") 

print("Outputting OTU and zOTU Tables..................... ", end="")

##### Setting names of output files
Output_table = "zotu_table_expanded.txt"

##### Setting up the key arrays --- LIST for keeping sequences in order, and DICT for managing sequence info
zOTU_list = []
zOTU_dict = {}


##### Opening zOTU table

COUNTS = open("all_libraries_zotu_table.txt", "r")

for line in COUNTS:
    if line.startswith("#"):
        COUNT_headings = line.strip().split()[1:]    ### Keeping the names of libraries
    else:
        LINE = line.strip().split()
        zOTU_list.append(LINE[0])
        zOTU_dict[LINE[0]] = [LINE[1:]]

COUNTS.close()


##### Adding taxonomy info to DICT

TAX = open("zotus.tax", "r")

for line in TAX:
    LINE = line.strip().split()
    if LINE[0] in zOTU_list:
        if len(LINE) > 1:
            zOTU_dict[LINE[0]].append(LINE[1])
        else:
            zOTU_dict[LINE[0]].append("unassigned")
    else:
        print('FATAL ERROR! Taxonomy file contains zOTUs that are not in zOTU count table! ---', LINE[0])
        sys.exit()

TAX.close()

##### Adding sequences from the FASTA file to DICT
FASTA = open("new_zotus.fasta", "r")
Sequence = ''
Seq_heading = FASTA.readline().strip().strip(">")

for line in FASTA:
    if line.startswith('>'):
        if Seq_heading not in zOTU_list and Seq_heading != "":     
             print('FATAL ERROR! Fasta file contains zOTUs that are not in zOTU count table! ---', Seq_heading)
             sys.exit()    
        zOTU_dict[Seq_heading].append(Sequence)
        Sequence = ''
        Seq_heading = line.strip().strip(">")
    else:
        Sequence = Sequence + line.strip().upper()
        
zOTU_dict[Seq_heading].append(Sequence) # Saves the final sequence (Seq_heading and Sequence) to a list

FASTA.close()

##### Adding zOTU - OTU relationship info to DICT

RELS = open("zotu_otu_relationships.txt", "r")

for line in RELS:
    LINE = line.strip().split()
    zOTU = re.search("^Zotu\d+", LINE[0])[0]
    if zOTU not in zOTU_list:
        print('FATAL ERROR! Relationship file contains zOTUs that are not in zOTU count table! --- ', zOTU)
        sys.exit()
    if LINE[1].startswith("otu"):
        zOTU_dict[zOTU].append(LINE[1])
    elif  LINE[1] == "noisy_chimera" or LINE[1] == "perfect_chimera" or LINE[1] == "match_chimera" or re.search("Chimera", LINE[2]) != None:
        zOTU_dict[zOTU].append("Chimera")
    elif (LINE[1] == "match" or LINE[1] == "perfect") and re.search("OTU\d+", LINE[2]) != None:
        OTU_ID = re.search("OTU\d+", LINE[2])[0].lower()
        zOTU_dict[zOTU].append(OTU_ID)    
    else:
        print("Relationship file contains a term that I have not considered")
        sys.exit()

RELS.close()

##### Outputting the Expanded Count Table
OUTPUT_TABLE = open(Output_table, "w")

print("OTU_ID", "OTU_assignment", "Taxonomy", "Sequence", "Total", sep = "\t", end = "\t", file = OUTPUT_TABLE)

for item in COUNT_headings:
    print(item, end = "\t", file = OUTPUT_TABLE)

print("", file = OUTPUT_TABLE)

for zOTU in zOTU_list:
    Total = 0
    for no in zOTU_dict[zOTU][0]:
        Total += int(no) 
    # Terms in DICT: 'Zotu32': [['0', '1', '100'], 'd:Bacteria(1.00)...', 'TACGT...', 'otu8']
    # I want to export: "OTU_ID", "OTU_assignment"[3], "Taxonomy"[1], "Sequence"[2], "Total"
    print(zOTU, zOTU_dict[zOTU][3], zOTU_dict[zOTU][1], zOTU_dict[zOTU][2], Total, sep = "\t", end = "\t", file = OUTPUT_TABLE)
    for no in zOTU_dict[zOTU][0]:
        print(no, end = "\t", file = OUTPUT_TABLE) 
    print("", file = OUTPUT_TABLE)

OUTPUT_TABLE.close()

print("zOTU_Table_expanded has been created!")

### Creating OTU_Table:

OTU = open("zotu_table_expanded.txt", "r")
OTU_TABLE = []

for line in OTU:
    LINE = line.strip().split()
    if line.startswith("OTU_ID"):
        COUNT_headings = line.strip().split()[4:]    ### Keeping the names of libraries
    else:
        OTU_TABLE.append(LINE)
        
OTU.close()

otu_dict = {}

for row_no in range(0, len(OTU_TABLE)):
    otu_key = OTU_TABLE[row_no][1]
    if not otu_key in otu_dict.keys():
         otu_dict[otu_key] = OTU_TABLE[row_no][4:]
    else:
        otu_dict[otu_key] = [sum(map(int, i)) for i in list(zip(otu_dict[otu_key], OTU_TABLE[row_no][4:]))]

##### Adding taxonomy info to DICT
TAX = open("otus.tax", "r")
OTU_TAX = []

for line in TAX:
    LINE = line.strip().split()
    OTU_TAX.append(LINE)

### Lowering the #OTU in Taxonomy file:
for list in OTU_TAX:
    list[0] = list[0].lower()
        

for row_no in range(0, len(OTU_TAX)):   
    if OTU_TAX[row_no][0] in otu_dict.keys():
        if len(OTU_TAX[row_no]) > 1:
            otu_dict[OTU_TAX[row_no][0]].append(OTU_TAX[row_no][1])
        else:
            otu_dict[OTU_TAX[row_no][0]].append("unassigned")

TAX.close()
                
###We are adding 1 to the end of our dictionary to reassign OTU numbers.
for row_no in range(0, len(OTU_TABLE)):
    if otu_dict[OTU_TABLE[row_no][1]][-1] != 1 and OTU_TABLE[row_no][1] in otu_dict.keys():
        otu_dict[OTU_TABLE[row_no][1]].append(OTU_TABLE[row_no][3])
        otu_dict[OTU_TABLE[row_no][1]].append(1)

                
COUNT_headings.insert(0,"#OTU")
COUNT_headings.insert(1,"Taxonomy")
COUNT_headings.insert(2,"Sequence")
data = []
data.append(COUNT_headings)      
for otu in otu_dict.keys():
    data.append([otu] + [otu_dict[otu][-3]] + [otu_dict[otu][-2]] + otu_dict[otu][:-3])
 


with open("OTU_Table.txt", "w") as bigFile:
    for LINE in data:
        for item in LINE[:-1]:
            print(item, end="\t", file = bigFile)
        for item in LINE [-1:]:
            print(item, end='\n',file = bigFile)

bigFile.close()

print("OTU_Table has been created!")


print("Symbio® Na zdrowie! Salud! Gānbēi (干杯)! Skål!")
