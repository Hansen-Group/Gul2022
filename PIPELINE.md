# Detailed description of pipeline

The following gives a detailed summary of the steps carried out by the pipeline used in Gul et al. 2022. The pipeline is implemented in `genotyping/paleomix/pipelines/ngs/pipeline.py` with most parameters specified in `configuration.yaml`. Unless otherwise specified, programs cited below were run with default parameters.

Mapping and genotyping is performed using the hg38 human reference genome, including alternative and decoy contigs, and other resource files distributed as part of the GATK (McKenna et al. 2010) [resource bundle](<https://gatk.broadinstitute.org/hc/en-us/articles/360035890811-Resource-bundle>).

See `README.md` for a description of how to run the pipeline.

## 1. Pre-processing of reference data

The human reference genome is validated by the pipeline, and then indexed using `samtools faidx` ([samtools](https://github.com/samtools/samtools) v1.11; Danecek et al. 2021), using the `gatk CreateSequenceDictionary`, and using `bwa-mem2 index` ([BWA mem2](https://github.com/bwa-mem2/bwa-mem2) v2.2.1). The reference genome is additionally split into 10 equally sized intervals using `gatk SplitIntervals`. Resource files in VCF format are indexed using `tabix` ([tabix](https://github.com/tabixio/tabix); Li 2011).

## 2. Pre-processing of FASTQ files

Pre-analyses quality assurance of FASTQ files is performed using `fastqc` ([FastQC](https://www.bioinformatics.babraham.ac.uk/projects/fastqc/) v0.11.9) and reports are merged using `multiqc` ([MultiQC](https://multiqc.info/) v1.10; Ewels et al. 2016). Verification of adapters and stringent validation of FASTQ reads is performed using `AdapterRemoval --identify-adapters` ([AdapterRemoval](https://github.com/MikkelSchubert/adapterremoval) v2.3.2; Schubert et al. 2016).

FASTQ files are trimmed using `fastp` ([fastp](https://github.com/OpenGene/fastp) v0.20.1; Chen et al. 2018) with options `--merge --correction --low_complexity_filter --overlap_len_require 11 --adapter_sequence AAGTCGGAGGCCAAGCGGTCTTAGGAAGACAA --adapter_sequence_r2 AGTCGGATCGTAGCCATGTCGTTCTGTGAGCCAAGGAGTTG`. Discarded FASTQ reads and orphaned paired reads are converted to unmapped BAM alignments and tagged with read-group information using `gatk FastqToSam`. Reads are subsequently analyzed using FastQC and reports from FastQC and fastp were merged using MultiQC.

## 3. Mapping of trimmed reads

Mapping of each sample is carried out using `bwa-mem2` using the `-M` and the `-Y` options. Mapped reads are tagged with read-group information, BAM tags are normalized according to the SAM/BAM specification to maximize downstream compatibility, alternative alignments are post-processed using the `bwa-postalt.js` script ([BWA-kit](https://github.com/lh3/bwa/tree/master/bwakit)), mate information is corrected and mate-quality tags are added using `samtools fixmate` with the `-m` option, the alignments are sorted using `samtool sort`, and `MD` and `NM` tags are updated using `samtools calmd`. Finally, PCR duplicates are marked in paired alignments using `samtools markdup` and in merged reads using `paleomix rmdup_collapsed`.

The resulting BAMs are merged using `samtools merge`. Unmapped reads, secondary alignments, QC failed reads, PCR duplicates, supplementary alignments, reads with unmapped or filtered mates, and improper pairs are removed and the resulting BAM alignments are indexed using `samtools index`. The filtered BAMs are analyzed using `gatk BaseRecalibrator` using dbSNP 151 from the GATK resource pack for known sites and recalibrated using `gatk ApplyBQSR`. The resulting BAMs are analyzed using `samtools idxstats`, `samtools bamstats`, FastQC, and reports are merged using MultiQC.

## 4. Genotyping of samples

Haplotypes are called for each BAM using `gatk HaplotypeCaller` with the `--emit-ref-confidence GVCF` option, and merged GVCFs are generated per interval using `gatk CombineGVCFs`, genotyped using `gatk GenotypeGVCFs`, and combined into a single VCF using `gatk GatherVcfs`. The resulting VCF is indexed using tabix.

Variant recalibrartion of SNPs is carried out using 'gatk VariantRecalibrator' using annotations `ExcessHet`, `DP`, `MQ`, `QD`, `SOR`, `FS`, `ReadPosRankSum`, `MQRankSum`, and `BaseQRankSum`, and using the tranches listed in `configuration.yaml`. Resource options were `known=false,training=true,truth=true,prior=15.0` for [HapMap](https://www.sanger.ac.uk/resources/downloads/human/hapmap3.html) v3.3, `known=false,training=true,truth=true,prior=12.0` for OMNI 2.5 genotypes for 1000 Genomes samples, `known=false,training=true,truth=false,prior=10.0` for 1000 Genomes phase 1 high confidence SNPs, and `known=true,training=false,truth=false,prior=2.0` for dbSNP release 151, all from the GATK resource pack.

Variant recalibration of indels is carried out using annotations `ExcessHet`, `DP`, `MQ`, `QD`, `SOR`, `FS`, `ReadPosRankSum`, and `MQRankSum`, and using the same truth sensitivity tranches as above. Resource options were `known=false,training=true,truth=true,prior=12.0` for the Mills and 1000G gold standard set of indels and `known=true,training=false,truth=false,prior=2.0` for dbSNP release 151, both from the GATK resource pack.

The models are applied using `gatk ApplyVQSR` with option `--truth-sensitivity-filter-level 99.6` for SNPs and `--truth-sensitivity-filter-level 98.0` for indels. Tranche plots are created using a modified version of the R-script included with GATK (`genotyping/paleomix/resources/rscripts/ngs/tranches.r`).

## 5. Annotation of variants

The resulting VCFs are annotated using VEP v104 (McLaren et al. 2016) and using the Ancestral Allele, ExACpLI, GERP Conservation Scores, and [LOFTEE](https://github.com/konradjk/loftee) v1.0.3 (Karczewski et al. 2020) plugins.

Custom annotation was additionally derived 1000 Genomes phased haplotypes (20201028), ClinVar release 20210821, dbSNP release 155, Ensemble GTF features release 104, GnomAD coverage summary release 3.0.1, and GnomAD sites release 3.0.

This is implemented in the `annovep` script described in `README.md` and located in the `annotation` folder.
