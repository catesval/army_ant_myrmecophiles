# army_ant_myrmecophiles

#### This repository contains the complete pipelines for the analysis and visualization of 16S rRNA V4 amplicon sequencing data for the publication by C. Valdivia *et al.* (in prep) with the working title *"Shared microbial symbionts among different cohabitant species"*.  
  
The starting data comprises amplicon datasets for 33 army ants and 109 myrmecophile beetles, plus negative controls. Libraries prepped in 2013-14 by Argonne National Laboratory, following Earth Microbiome Project protocols, were sequenced across five 2 x 150 bp Illumina MiSeq lanes, in multiplex with samples from other projects.

The workflow comprised 4 distinct steps. They are listed below, and either discussed in more details, or linked to further down.

1. Assembly and extraction of project-specific libraries from multiplexed sequencing datasets obtained from Argonne Nat'l Laboratory
2. Basic analysis of the amplicon data: filtering, denoising, OTU picking
3. Decontamination
4. Relative abundance calculation. 


## 1. Extraction of project-specific libraries from multiplexed sequencing datasets

For this step we need the following:
- [PEAR v0.9.11](https://www.h-its.org/software/pear-paired-end-read-merger/)
- [vsearch v2.15.2_linux_x86_64](https://github.com/torognes/vsearch)
- Python 3.7.8
- extract_samples.py 

From each lane, we obtained the following files:

- Run_R1.fastq
- Run_R2.fastq
- Run_I1.fastq
- Run_mapping.oligos

**1.1. First we need to assemble the reads (examples for one of the runs: RunA. This was repeated for all the runs):**

```
pear -f RunA_R1.fastq -r RunA_R2.fastq -o RunA -v 10 -n 251 -m 255 -q 30 -j 20 
```

We get the outputs:

- RunA.assembled.fastq  
- RunA.unassembled.forward.fastq  
- RunA.unassembled.reverse.fastq
- RunA.discarded.fastq

**1.2. Then we convert the assembled fastq file to fasta format. We only continue working with the file Run.assembled.fasta:**

```
vsearch -fastq_filter RunA.assembled.fastq -fastaout RunA_assembled.fasta -fasta_width 0
```

**1.3. We create a mapping.oligos files containing oonly our samples of interest** 
We must have a file containing a list of the names of our samples. We use it to extract the information for those samples from the Run_mapping.oligos file.

```
grep -f RunA_samples.list RunA_mapping.oligos > samples_mapping.oligos
```

**1.4. We use the custom scrip 'extract_samples.py', which will create an invdividual file for each sample.**

```
extract_samples.py RunA_assembled.fasta samples_mapping.oligos RunA_I1.fastq
```

**1.5. We create a folder for the samples and move them there:**

```
mkdir ../study_samples #to create the new folder outside the folder of the run
```
```
mv A_* ../study_samples
```
```
mv E_* ../study_samples
```
```
mv L_* ../study_samples
```
```
mv water* ../study_samples
```

(Note from the author: I did it like this because we don't want the RunA_assembled.fasta in the new folder )

**Reminder that this must be done for all the runs that contain your samples of interest**

## 2. Basic analysis of the amplicon data: filtering, denoising, OTU picking

For this step we need the following: 
- [vsearch v2.15.2_linux_x86_64](https://github.com/torognes/vsearch)
- [usearch v11.0.667_i86linux32](https://www.drive5.com/usearch/)
- Python 3.7.8
- add_seq_to_zotu.py 
- QUACK.py

We navigate to the ./study_samples folder that we created previously. All the fasta files for our samples should be there.

**2.1 We run modified LSD pipeline.**
The script only needs the path to the folder containing the fasta files as input. 
It returns OTU and zOTU tables. Original LSD pipeline and "add_seq_to_zotu.py", necessary for both the original and modified version, can be found [here](https://github.com/symPiotr/LSD)

We have used the minsize value of 1 when denoising for two primary reasons:
1. To retain information within negative control samples, needed for the contamination filtering step, but which tended to have a low total number of reads.
2. To avoid “homogenizing” potential within-sample variation that could have been due to biology.

```
./modified_LSD.py /home/cata.valdivia/army_ants_fastq_files/study_samples/
```
The outputs of this script are:
- new_zotus.fasta
- all_libraries_zotu_table.txt
- zotu_otu_relationships.txt
- zotus.fasta
- zotus.tax
- otus.fasta
- otus.tax
- zotu_table_expanded.txt
- OTU_Table.txt

We will use zotu_table_expanded and otus.tax in the following steps. 

## 3. Decontamination

For this step we need:
- Python 3.7.8
- [QUACK.py](https://github.com/MikeCollasa/QUACK)

**3.1. We run the QUACK script to remove contaminants.**
This script can also use spike-in information to obtain absolut abundance of reads, but we don't have them in our analysis, so our only input is a file containing the names of the blank libraries. 

First, the script compares the maximum relative abundance of unique genotypes in libraries representing insect samples against the maximum relative abundance of these same genotypes in blank libraries. If the ratio of these values was below the specified threshold (here, set to 10), then the genotype was classified as a contaminant and removed. 

Second, the script classifies any genotype that reaches a relative abundance threshold (here: 0.001) as “symbiont”; we conclude that the remaining microbial signal, likely a combination of rare symbiotic microbes, uncommon contaminants, and sequencing artifacts, cannot be classified reliably, but include them as “others” in relative abundance and other comparisons. 

Finally, the script classifies libraries as “heavily contaminated” and removes them from the list if the proportion of reads classified as contaminants exceedes a third threshold (here: 0.8).

>Usage: QUACK.py <count_table> <list_of_blanks> <list_of_spikeins> <otus.tax> <ThresholdA; recommended value 10> <ThresholdB; recommended value 0.001> <ThresholdC; recommended value 80>

```
QUACK.py zotu_table_expanded.txt Blanks.txt otus.tax 10 0.001 75
```

The outputs of this script are:
- **Table_with_classes.txt** - where every zOTU is assigned to Symbiont, Other, PCR or Extraction Contaminant and PCR or Extraction Spikein class
- **Statistics_table.txt** - with statistics about every library composition in terms of e.g contamination or spikein percentage 
- **Decontaminated_zOTU_table.txt** - where all contaminants and spikeins are deleted, as well as libraries that sum of those were higher than ThresholdC
- **Decontaminated_OTU_table.txt** - table based on Decontaminated zOTU table and otus.tax file

## 4. Relative abundance calculation.

For this step we need: 
- Python 3.7.8
- get_rel_abund_OTU.py
- get_zOTU_rel_abund.py

**4.1. First we calculate relative abundance for OTUs.** 

**4.1.1. We create OTU file without taxonomic annotation.**
This, because the annotation comprises several columns of different lenght for each OTU. I removed taxonomy by opening the file on excel and removing those columns. I named this new file **Decontaminated_OTU_table_no_taxa.txt**

**4.1.2. Run script that calculates relative abundance of OTU table without taxonomic annotation.**
We give the script the name of our OTU table without taxonomic annotation and an output name. I named my output file **Decontaminated_OTU_table_no_taxa_rel_abund.txt**

```
./get_rel_abund_OTU.py Decontaminated_OTU_table_no_taxa.txt Decontaminated_OTU_table_no_taxa_rel_abund.txt
```

**4.1.3. Add back the taxonomic annotation to the table and analyze the results to select the most relevant OTUs.**

This was done filtering by the following criteria, and selecting the OTUs that fulfilled at least two of them:

1. It is present with a relative abundance higher than 0.01% in at least 20 samples.
2. It is present with a relative abundance higher than 5% in at least one sample. 
3. The average abundance of the OTU is at least 1%

Then we create a file containing a list of the selected OTUs to calculate the relative abundance of the zOTUs for those OTUs. I named this **file otu_list.txt** and it contained 28 OTUs. 

**4.2. Calculate relative abundance for zOTUs.** 
Now that we have out list of selected OTUs we can get the relative abundance for the zOTUs associated to those OTUs. 

```
./get_zOTU_rel_abund.py otu_list.txt Decontaminated_zOTU_table.txt
```

This script outputs individual files named after the OTU associated to the zOTUs. They contain zOTU tables with relative abundance. Relative abundance of zOTUs was calculated with OTU abundance for each sample as the total. 

We selected the most relevant zOTUs for our study if they fulfilled the following criteria (all of them):

1. They were represented by a total of reads of at least 100. 
2. Their maximum relative abundance was at least 1%
3. They were present with a relative abundance of 5% in at least one sample.
