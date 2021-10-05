#! /usr/bin/env python3

import sys
if len(sys.argv) != 4:
    sys.exit('This script finds sequences for samples of interest, given the sample names and index sequence in a mapping_oligos file. It needs the following inputs: input.fasta, mapping.oligos, input_I1.fastq\n'
             'Usage: ./my_script.py <Input.fasta> <mapping.oligos> <input_I1.fastq>\n')

Script, InputFileName1, InputFileName2, InputFileName3 = sys.argv

FASTA = open(InputFileName1, "r")
MAPPING_OLIGOS = open(InputFileName2, "r")
FASTQ = open(InputFileName3, "r").readlines()
FASTQ  = [line[:-1] for line in FASTQ]

#creating dictionary

FASTA_dict = {}
key = ""

#filling dictionary with sequence id and sequence


for line in FASTA:
    LINE = line.strip()
    if LINE.startswith(">"):
        key = LINE.strip(">")
    else:
        FASTA_dict[key] = LINE

#creating dictionary with mapping oligo sequence as key and sample id as values within a list

parts = ""
MAP_OLIS = {}

for row in MAPPING_OLIGOS:
    parts = row.split()
    for cols in parts:
        MAP_OLIS[parts[2]] = [parts[3]]

#adding sequences IDs to MAP_OLIS dictionary

index_check = ""
index_seq = ""

for seq in MAP_OLIS.keys():
    index_seq = seq[1:]
    for line_no in range(0,len(FASTQ),4):
        index_check = index_seq in FASTQ[line_no+1]
        if index_check is True:
            MAP_OLIS[seq].append(FASTQ[line_no])

#Create output file with sample name. Add as sequence name sample name plus sequence number (from 1 to X, X = number of sequences for the sample), add fasta sequence. 
SeqID = ""
SampleID = ""
Seq_check = ""

for seq_list in MAP_OLIS.values():
    for index_no in range(1, len(seq_list)):
        SampleID = seq_list[0]
        SeqID = seq_list[index_no]
        OUTPUT = open(SampleID + ".fasta", "a")
        Seq_check = SeqID.strip('@') in FASTA_dict
        if Seq_check is True:
            print(">", SampleID, "._", index_no, "\n", FASTA_dict[SeqID.strip('@')], sep = "", file = OUTPUT)
