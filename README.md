# army_ant_myrmecophiles
#Analysis pipeline used for the analysis of army ant and myrmecophile microbiomes.

We started with samples scattered through five different files (five different sequencing runs). For each run we have the following files:

Run_R1.fastq
Run_R2.fastq
Run_I1.fastq
Run_mapping.oligos


#First we need to assemble the reads (examples for one of the runs: RunA. This was repeated for all the runs):

pear -f RunA_R1.fastq -r RunA_R2.fastq -o RunA -v 10 -n 251 -m 255 -q 30 -j 20 

#We get outputs:

RunA.assembled.fastq  
RunA.unassembled.forward.fastq  
RunA.unassembled.reverse.fastq
RunA.discarded.fastq

#Then convert the assembled fastq file to fasta format. We only continue working with the file Run.assembled.fastq:

vsearch -fastq_filter RunA.assembled.fastq -fastaout RunA_assembled.fasta -fasta_width 0

#Then we need to extract the samples from the assembled fasta file. For this, first we need to create a Run_mapping.oligos file that only contains the samples for our analysis, since the runs also have samples from other projects. We have a file with a list containing the names of our samples, and we use it to extract the information for those samples from the Run_mapping.oligos file. 

grep -f RunA_samples.list RunA_mapping.oligos > samples_mapping.oligos

#Then we use the custom scrip 'extract_samples.py', which will create an invdividual file for each sample. 

extract_samples.py RunA_assembled.fasta samples_mapping.oligos RunA_I1.fastq

#We create a folder for the samples and move them there:

mkdir study_samples
mv A_*
mv E_*
mv L_*
mv water*

#We run modified LSD pipeline. The script only needs the path to the folder containing the fasta files as input. It returns OTU and zOTU tables. Original LSD pipeline and "add_seq_to_zotu.py", necessary for both the original and modified version, can be found here: https://github.com/symPiotr/LSD

./modified_LSD.py /home/cata.valdivia/army_ants_fastq_files/study_samples/

#Then we run the QUACK script to remove contaminants: https://github.com/MikeCollasa/QUACK. This script can also use spike-in information to obtain absolut abundance of reads, but we don't have them in our analysis, so our only input is a file containing the names of the blank libraries. 

Usage: QUACK.py <count_table> <list_of_blanks> <list_of_spikeins> <otus.tax> <ThresholdA; recommended value 10> <ThresholdB; recommended value 0.001> <ThresholdC; recommended value 80>

QUACK.py zotu_table_expanded.txt Blanks.txt otus.tax 10 0.001 75

#Then we calculate relative abundance for OTUs. For this, first we create a new file in which we remove the taxonomic annotation. This, because the annotation comprises several columns of different lenght for each OTU. I removed taxonomy by opening the file on excel and removing those columns.

./get_rel_abund_OTU.py Decontaminated_OTU_table_no_taxa.txt Decontaminated_OTU_table_no_taxa_rel_abund.txt

#We added back the taxonomy to the table and analyze the results to select the most relevant OTUs. 
#We did this filtering by the following criteria,, and selected the OTUs that fulfilled at least two of them:

#1. It is present with a relative abundance higher than 0.01% in at least 20 samples.
#2. It is present with a relative abundance higher than 5% in at least one sample. 
#3. The average abundance of the OTU is at least 1%

#This can be found in Supplemental table 1, sheet names "Decontaminated_OTU".

#Then we created a file containing a list of the selected OTUs to calculate the relative abundance of the zOTUs for those OTUs. 

./get_zOTU_rel_abund.py otu_list.txt Decontaminated_zOTU_table_separate.txt

#This script outputs individual files named after the OTU associated to the zOTUs. They contain zOTU tables with relative abundance. Relative abundance of zOTUs was calculated with OTU abundance for each sample as the total. 
#zOTUs were selected if they fulfilled the following criteria (all of them):

#1. They were represented by a total of reads of at least 100. 
#2. Their maximum relative abundance was at least 1%
#3. They were present with a relative abundance of 5% in at least one sample.
