.. highlight:: Yaml
.. _bam_usage:

Pipeline usage
==============

The following describes, step by step, the process of setting up a project for mapping FASTQ reads against a reference sequence using the BAM pipeline. For a detailed description of the configuration file (makefile) used by the BAM pipeline, please refer to the section :ref:`bam_makefile`, and for a detailed description of the files generated by the pipeline, please refer to the section :ref:`bam_filestructure`.

The BAM pipeline is invoked using the `paleomix` command, which offers access to the pipelines and to other tools included with PALEOMIX (see section :ref:`other_tools`). For the purpose of these instructions, we will make use of a tiny FASTQ data set included with PALEOMIX pipeline, consisting of synthetic FASTQ reads simulated against the human mitochondrial genome. To follow along, first create a local copy of the example data-set:

.. code-block:: bash

    $ paleomix bam example .

This will create a folder named `bam_pipeline` in the current folder, which contain the example FASTQ reads and a 'makefile' showcasing various features of the BAM pipeline (`makefile.yaml`). We will make use of a subset of the data, but we will not make use of the makefile. The data we will use consists of 3 simulated ancient DNA libraries (independent amplifications), for which either one or two lanes have been simulated:

  +-------------+------+------+-----------------------------+
  | Library     | Lane | Type | Files                       |
  +-------------+------+------+-----------------------------+
  | ACGATA      |    1 |   PE | data/ACGATA\_L1\_*.fastq.gz |
  +-------------+------+------+-----------------------------+
  | GCTCTG      |    1 |   SE | data/GCTCTG\_L1\_*.fastq.gz |
  +-------------+------+------+-----------------------------+
  | TGCTCA      |    1 |   SE | data/TGCTCA\_L1\_*.fastq.gz |
  +-------------+------+------+-----------------------------+
  |             |    2 |   PE | data/TGCTCA\_L2\_*.fastq.gz |
  +-------------+------+------+-----------------------------+


.. warning::
    The BAM pipeline largely relies on the existence of final and intermediate files in order to detect if a given analytical step has been carried out. Therefore, changes made to a makefile after the pipeline has already been run (even if not run to completion) may therefore not cause analytical steps affected by these changes to be re-run. If changes are to be made at such a point, it is typically necessary to manually remove affected intermediate files before running the pipeline again. See the section :ref:`bam_filestructure` for more information about the layout of files generated by the pipeline.


Creating a makefile
-------------------

As described in the :ref:`introduction`, the BAM pipeline operates based on 'makefiles', which serve to specify the location and structure of input data (samples, libraries, lanes, etc), and which specific which tasks are to be run, and which settings to be used. The makefiles are written using the human-readable YAML format, which may be edited using any regular text editor.

For a brief introduction to the YAML format, please refer to the :ref:`yaml_intro` section, and for a detailed description of the BAM Pipeline makefile, please refer to section :ref:`bam_makefile`.

To start a new project, we must first generate a makefile template using the following command, which for the purpose of this tutorial we place in the example folder:

.. code-block:: bash

    $ cd bam_pipeline/
    $ paleomix bam makefile > makefile.yaml

Once you open the resulting file (`makefile.yaml`) in your text editor of choice, you will find that BAM pipeline makefiles are split into three major sections, representing 1) the default options; 2) the reference genomes against which reads are to be mapped; and 3) the of input files for the samples which are to be processed.

In a typical project, we will need to review the default options, add one or more reference genomes which we wish to target, and list the input data to be processed.


Default options
^^^^^^^^^^^^^^^

The makefile starts with an `Options` section, which is applied to every set of input-files in the makefile unless explicitly overwritten for a given sample (this is described in the :ref:`bam_makefile` section). For most part, the default values should be suitable for any given project, but special attention should be paid to the following options (double colons are used to separate subsections):

**Options \:\: Platform**

    The sequencing platform used to generate the sequencing data; this information is recorded in the resulting BAM file, and may be used by downstream tools. The `SAM/BAM specification`_ the valid platforms, which currently include `CAPILLARY`, `HELICOS`, `ILLUMINA`, `IONTORRENT`, `LS454`, `ONT`, `PACBIO`, and `SOLID`.

**Options \:\: QualityOffset**

    The QualityOffset option refers to the starting ASCII value used to encode `Phred quality-scores`_ in user-provided FASTQ files, with the possible values of 33, 64, and `Solexa`. For most modern data, this will be 33, corresponding to ASCII characters in the range `!` to `J`. Older data is often encoded using the offset 64, corresponding to ASCII characters in the range `@` to `h`, and more rarely using Solexa quality-scores, which represent a different scheme than Phred scores, and which occupy the range of ASCII values from `;` to `h`. For a visual representation of this, refer to the `Phred quality-scores`_ page.

.. warning::

    By default, the adapter trimming software used by PALEOMIX expects quality-scores no greater than 41, corresponding to the ASCII character `J` when encoded using offset 33. If the input-data contains quality-scores higher greater than this value, then it is necessary to specify the maximum value using the `--qualitymax` command-line option. See below.

.. warning::

    Presently, quality-offsets other than 33 are not supported when using the BWA `mem` or the BWA `bwasw` algorithms. To use these algorithms with quality-offset 64 data, it is therefore necessary to first convert these data to offset 33. This can be accomplished using the `seqtk`_ tool.

**Options \:\: AdapterRemoval \:\: --adapter1** and **Options \:\: AdapterRemoval \:\: --adapter2**

These two options are used to specify the adapter sequences used to identify and trim reads that contain adapter contamination using AdapterRemoval. Thus, the sequence provided for `--adapter1` is expected to be found in the mate 1 reads, and the sequence specified for `--adapter2` is expected to be found in the mate 2 reads. In both cases, these should be specified as in the orientation that appear in these files (i.e. it should be possible to grep the files for these sequences, assuming that the reads were long enough, if you treat Ns as wildcards).


.. warning::

  It is very important that the correct adapter sequences are used. Please refer to the `AdapterRemoval documentation`_ for more information and for help identifying the adapters for paired-end reads.


**Aligners \:\: Program**

    The short read alignment program to use to map the (trimmed) reads to the reference genome. Currently, users many choose between `BWA` and `Bowtie2`, with additional options available for each program.

**Aligners \:\: \* \:\: MinQuality**

    The minimum mapping quality of hits to retain during the mapping process. If this option is set to a non-zero value, any hits with a mapping quality below this value are removed from the resulting BAM file (this option does not apply to unmapped reads). If the final BAM should contain all reads in the input files, this option must be set to 0, and the `FilterUnmappedReads` option set to `no`.

**Aligners \:\: BWA \:\: UseSeed**

    Enable/disable the use of a seed region when mapping reads using the BWA `backtrack` alignment algorithm (the default). Disabling this option may yield some improvements in the alignment of highly damaged ancient DNA, at the cost of significantly increasing the running time. As such, this option is not recommended for modern samples [Schubert2012]_.


For the purpose of the example project, we need only change a few options. Since the reads were simulated using an Phred score offset of 33, there is no need to change the `QualityOffset` option, and since the simulated adapter sequences matches the adapters that AdapterRemoval searches for by default, so we do not need to set either of `--adapter1` or `--adapter2`. We will, however, use the default mapping program (BWA) and algorithm (`backtrack`), but change the minimum mapping quality to 30 (corresponding to an error probability of 0.001). Changing the minimum quality is accomplished by locating the `Aligners` section of the makefile, and changing the `MinQuality` value from 0 to 30 (line 40):

.. code-block:: yaml
    :emphasize-lines: 12
    :linenos:
    :lineno-start: 29

    # Settings for aligners supported by the pipeline
    Aligners:
      # Choice of aligner software to use, either "BWA" or "Bowtie2"
      Program: BWA

      # Settings for mappings performed using BWA
      BWA:
        # One of "backtrack", "bwasw", or "mem"; see the BWA documentation
        # for a description of each algorithm (defaults to 'backtrack')
        Algorithm: backtrack
        # Filter aligned reads with a mapping quality (Phred) below this value
        MinQuality: 30
        # Filter reads that did not map to the reference sequence
        FilterUnmappedReads: yes
        # Post-mortem damage localizes to the 5' region, which the 'backtrack' algorithm
        # expects to contain few errors. Disabling the seed may therefore improve mapping
        # results for aDNA at the cost of increased runtime (see http://pmid.us/22574660).
        UseSeed: yes

Since the data we will be mapping represents (simulated) ancient DNA, we will furthermore set the UseSeed option to `no` (line 55), in order to recover a small additional amount of alignments during mapping (see [Schubert2012]_):

.. code-block:: yaml
    :emphasize-lines: 18
    :linenos:
    :lineno-start: 38

    # Settings for aligners supported by the pipeline
    Aligners:
      # Choice of aligner software to use, either "BWA" or "Bowtie2"
      Program: BWA

      # Settings for mappings performed using BWA
      BWA:
        # One of "backtrack", "bwasw", or "mem"; see the BWA documentation
        # for a description of each algorithm (defaults to 'backtrack')
        Algorithm: backtrack
        # Filter aligned reads with a mapping quality (Phred) below this value
        MinQuality: 30
        # Filter reads that did not map to the reference sequence
        FilterUnmappedReads: yes
        # May be disabled ("no") for aDNA alignments with the 'backtrack' algorithm.
        # Post-mortem damage localizes to the seed region, which BWA expects to
        # have few errors (sets "-l"). See http://pmid.us/22574660
        UseSeed: no

Once this is done, we can proceed to specify the location of the reference genome(s) that we wish to map our reads against.


Reference genomes (prefixes)
----------------------------

Mapping is carried out using one or more reference genomes (or other sequences) in the form of FASTA files, which are indexed for use in read mapping (automatically, by the pipeline) using either the `bwa index` or `bowtie2-build` commands. Since sequence alignment index are generated at the location of these files, reference genomes are also referred to as "prefixes" in the documentation. In other words, using BWA as an example, the PALEOMIX pipeline will generate a index (prefix) of the reference genome using a command corresponding to the following, for BWA:

.. code-block:: bash

    $ bwa index prefixes/my_genome.fasta

In addition to the BWA / Bowtie2 index, several other related files are also automatically generated, including a FASTA index file (`.fai`), which are required for various operations of the pipeline. These are similarly located at the same folder as the reference FASTA file. For a more detailed description, please refer to the :ref:`bam_filestructure` section.

.. warning::
    Since the pipeline automatically carries out indexing of the FASTA files, it therefore requires write-access to the folder containing the FASTA files. If this is not possible, one may simply create a local folder containing symbolic links to the original FASTA file(s), and point the makefile to this location. All automatically generated files will then be placed in this location.

Specifying which FASTA file to align sequences is accomplished by listing these in the `Prefixes` section in the makefile. For example, assuming that we had a FASTA file named `my\_genome.fasta` which is located in the `my\_prefixes` folder, the following might be used::

    Prefixes:
      my_genome:
        Path: my_prefixes/my_genome.fasta

The name of the prefix (here `my\_genome`) will be used to name the resulting files and in various tables that are generated by the pipeline. Typical names include `hg19`, `EquCab20`, and other standard abbreviations for reference genomes, accession numbers, and the like. Multiple prefixes can be specified, but each name MUST be unique::

    Prefixes:
      my_genome:
        Path: my_prefixes/my_genome.fasta
      my_other_genome:
        Path: my_prefixes/my_other_genome.fasta

In the case of this example project, we will be mapping our data against the revised Cambridge Reference Sequence (rCRS) for the human mitochondrial genome, which is included in examples folder under `prefixes`, as a file named `rCRS.fasta`. To add it to the makefile, locate the `Prefixes` section located below the `Options` section, and update it as described above (lines 115 and 119):

.. code-block:: yaml
    :emphasize-lines: 6,10
    :linenos:
    :lineno-start: 110

    # Map of prefixes by name, each having a Path, which specifies the location of the
    # BWA/Bowtie2 index, and optional regions for which additional statistics are produced.
    Prefixes:
      # Replace 'NAME_OF_PREFIX' with name of the prefix; this name is used in summary
      # statistics and as part of output filenames.
      rCRS:
        # Replace 'PATH_TO_PREFIX' with the path to .fasta file containing the references
        # against which reads are to be mapped. Using the same name as filename is strongly
        # recommended (e.g. /path/to/Human_g1k_v37.fasta should be named 'Human_g1k_v37').
        Path: prefixes/rCRS.fasta

Once this is done, we may specify the input data that we want the pipeline to process.


Specifying read data
--------------------

A single makefile may be used to process one or more samples, to generate one or more BAM files and supplementary statistics. In this project we will only deal with a single sample, which we accomplish by adding creating our own section at the end of the makefile. The first step is to determine the name for the files generated by the BAM pipeline. Specifically, we will specify a name which is prefixed to all output generated for our sample (here named `MyFilename`), by adding the following line to the end of the makefile:

.. code-block:: yaml
    :linenos:
    :lineno-start: 129

    # You can also add comments like these to document your experiment
    MyFilename:


This first name, or grouping, is referred to as the target, and typically corresponds to the name of the sample being processes, though any name may do. The actual sample-name is specified next (it is possible, but uncommon, for a single target to contain multiple samples), and is used both in tables of summary statistics, and recorded in the resulting BAM files. This is accomplished by adding another line below the target name:

.. code-block:: yaml
    :linenos:
    :lineno-start: 129

    # You can also add comments like these to document your experiment
    MyFilename:
      MySample:

Similarly, we need to specify the name of each library in our data set. By convention, I often use the index used to construct the library as the library name (which allows for easy identification), but any name may be used for a library, provided that it unique to that sample. As described near the start of this document, we are dealing with 3 libraries:

  +-------------+------+------+-----------------------------+
  | Library     | Lane | Type | Files                       |
  +-------------+------+------+-----------------------------+
  | ACGATA      |    1 |   PE | data/ACGATA\_L1\_*.fastq.gz |
  +-------------+------+------+-----------------------------+
  | GCTCTG      |    1 |   SE | data/GCTCTG\_L1\_*.fastq.gz |
  +-------------+------+------+-----------------------------+
  | TGCTCA      |    1 |   SE | data/TGCTCA\_L1\_*.fastq.gz |
  +-------------+------+------+-----------------------------+
  |             |    2 |   PE | data/TGCTCA\_L2\_*.fastq.gz |
  +-------------+------+------+-----------------------------+

It is important to correctly specify the libraries, since the pipeline will not only use this information for summary statistics and record it in the resulting BAM files, but will also carry out filtering of PCR duplicates (and other analyses) on a per-library basis. Wrongly grouping together data will therefore result in a loss of useful alignments wrongly identified as PCR duplicates, or, similarly, in the inclusion of reads that should have been filtered as PCR duplicates. The library names are added below the name of the sample (`MySample`), in a similar manner to the sample itself:

.. code-block:: yaml
    :linenos:
    :lineno-start: 129

    # You can also add comments like these to document your experiment
    MyFilename:
      MySample:
        ACGATA:

        GCTCTG:

        TGCTCA:

The final step involves specifying the location of the raw FASTQ reads that should be processed for each library, and consists of specifying one or more "lanes" of reads, each of which must be given a unique name. For single-end reads, this is accomplished simply by providing a path (with optional wildcards) to the location of the file(s). For example, for lane 1 of library ACGATA, the files are located at `data/ACGATA\_L1\_*.fastq.gz`:

.. code-block:: bash

    $ ls data/GCTCTG_L1_*.fastq.gz
    data/GCTCTG_L1_R1_01.fastq.gz
    data/GCTCTG_L1_R1_02.fastq.gz
    data/GCTCTG_L1_R1_03.fastq.gz

We simply specify these paths for each of the single-end lanes, here using the lane number to name these (similar to the above, this name is used to tag the data in the resulting BAM file):

.. code-block:: yaml
    :linenos:
    :lineno-start: 129

    # You can also add comments like these to document your experiment
    MyFilename:
      MySample:
        ACGATA:

        GCTCTG:
          Lane_1: data/GCTCTG_L1_*.fastq.gz

        TGCTCA:
          Lane_1: data/TGCTCA_L1_*.fastq.gz

Specifying the location of paired-end data is slightly more complex, since the pipeline needs to be able to locate both files in a pair. This is accomplished by making the assumption that paired-end files are numbered as either mate 1 or mate 2, as shown here for 4 pairs of files with the common _R1 and _R2 labels:

.. code-block:: bash

    $ ls data/ACGATA_L1_*.fastq.gz
    data/ACGATA_L1_R1_01.fastq.gz
    data/ACGATA_L1_R1_02.fastq.gz
    data/ACGATA_L1_R1_03.fastq.gz
    data/ACGATA_L1_R1_04.fastq.gz
    data/ACGATA_L1_R2_01.fastq.gz
    data/ACGATA_L1_R2_02.fastq.gz
    data/ACGATA_L1_R2_03.fastq.gz
    data/ACGATA_L1_R2_04.fastq.gz

Knowing how that the files contain a number specifying which file in a pair they correspond to, we can then construct a path that includes the keyword `{Pair}` in place of that number. For the above example, that path would therefore be `data/ACGATA\_L1\_R{Pair}_*.fastq.gz` (corresponding to `data/ACGATA\_L1\_R[12]_*.fastq.gz`):

.. code-block:: yaml
    :linenos:
    :lineno-start: 129

    # You can also add comments like these to document your experiment
    MyFilename:
      MySample:
        ACGATA:
          Lane_1: data/ACGATA_L1_R{Pair}_*.fastq.gz

        GCTCTG:
          Lane_1: data/GCTCTG_L1_*.fastq.gz

        TGCTCA:
          Lane_1: data/TGCTCA_L1_*.fastq.gz
          Lane_2: data/TGCTCA_L2_R{Pair}_*.fastq.gz

.. note::
    Note that while the paths given here are relative to the location of where the pipeline is run, it is also possible to provide absolute paths, should the files be located in an entirely different location.

.. note::
    At the time of writing, the PALEOMIX pipeline supports uncompressed, gzipped, and bzipped FASTQ reads. It is not necessary to use any particular file extension for these, as the compression method (if any) is detected automatically.


The final makefile
------------------

Once we've completed the steps described above, the resulting makefile should look like the following, shown here with the modifications that we've made highlighted:

.. code-block:: yaml
    :emphasize-lines: 40,46,115,119,129-
    :linenos:

    # -*- mode: Yaml; -*-
    # Default options.
    # Can also be specific for a set of samples, libraries, and lanes,
    # by including the "Options" hierarchy at the same level as those
    # samples, libraries, or lanes below.
    Options:
      # Sequencing platform, see SAM/BAM reference for valid values
      Platform: Illumina
      # Quality offset for Phred scores, either 33 (Sanger/Illumina 1.8+)
      # or 64 (Illumina 1.3+ / 1.5+). For Bowtie2 it is also possible to
      # specify 'Solexa', to handle reads on the Solexa scale. This is
      # used during adapter-trimming and sequence alignment
      QualityOffset: 33

      # Settings for trimming of reads, see AdapterRemoval man-page
      AdapterRemoval:
        # Set and uncomment to override defaults adapter sequences
    #     --adapter1: AGATCGGAAGAGCACACGTCTGAACTCCAGTCACNNNNNNATCTCGTATGCCGTCTTCTGCTTG
    #     --adapter2: AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTAGATCTCGGTGGTCGCCGTATCATT
        # Some BAM pipeline defaults differ from AR defaults;
        # To override, change these value(s):
        --mm: 3
        --minlength: 25
        # Extra features enabled by default; change 'yes' to 'no' to disable
        --collapse: yes
        --trimns: yes
        --trimqualities: yes

      # Settings for aligners supported by the pipeline
      Aligners:
        # Choice of aligner software to use, either "BWA" or "Bowtie2"
        Program: BWA

        # Settings for mappings performed using BWA
        BWA:
          # One of "backtrack", "bwasw", or "mem"; see the BWA documentation
          # for a description of each algorithm (defaults to 'backtrack')
          Algorithm: backtrack
          # Filter aligned reads with a mapping quality (Phred) below this value
          MinQuality: 30
          # Filter reads that did not map to the reference sequence
          FilterUnmappedReads: yes
          # Post-mortem damage localizes to the 5' region, which the 'backtrack' algorithm
          # expects to contain few errors. Disabling the seed may therefore improve mapping
          # results for aDNA at the cost of increased runtime (see http://pmid.us/22574660).
          UseSeed: no
          # Additional command-line options may be specified below. For 'backtrack' these
          # are applied to "bwa aln" calls. See Bowtie2 for more examples.
    #      -n: 0.04

        # Settings for mappings performed using Bowtie2
        Bowtie2:
          # Filter aligned reads with a mapping quality (Phred) below this value
          MinQuality: 0
          # Filter reads that did not map to the reference sequence
          FilterUnmappedReads: yes
          # Examples of how to add additional command-line options
    #      --trim5: 5
    #      --trim3: 5
          # Note that the colon is required, even if no value is specified
          --very-sensitive:
          # Example of how to specify multiple values for an option
    #      --rg:
    #        - CN:SequencingCenterNameHere
    #        - DS:DescriptionOfReadGroup

      # Command-line options for mapDamage; use long-form options(--length not -l):
      mapDamage:
        # By default, the pipeline will downsample the input to 100k hits
        # when running mapDamage; remove to use all hits
        --downsample: 100000

      # Set to 'yes' exclude a type of trimmed reads from alignment / analysis;
      # possible read-types reflect the output of AdapterRemoval
      ExcludeReads:
        # Exclude single-end reads (yes / no)?
        Single: no
        # Exclude non-collapsed paired-end reads (yes / no)?
        Paired: no
        # Exclude paired-end reads for which the mate was discarded (yes / no)?
        Singleton: no
        # Exclude overlapping paired-ended reads collapsed into a single sequence
        # by AdapterRemoval (yes / no)?
        Collapsed: no
        # Like 'Collapsed', but only for collapsed reads truncated due to the
        # presence of ambiguous or low quality bases at read termini (yes / no).
        CollapsedTruncated: no

      # Optional steps to perform during processing.
      Features:
        # If set to 'filter', PCR duplicates are removed from the output files; if set to
        # 'mark', PCR duplicates are flagged with bit 0x400, and not removed from the
        # output files; if set to 'no', the reads are assumed to not have been amplified.
        PCRDuplicates: filter
        # Set to 'no' to disable mapDamage; set to 'plots' to build basic mapDamage plots;
        # set to 'model' to build plots and post-mortem damage models; and set to 'rescale'
        # to build plots, models, and BAMs with rescaled quality scores. All analyses are
        # carried out per library.
        mapDamage: plot
        # Generate coverage information for the final BAM and for each 'RegionsOfInterest'
        # specified in 'Prefixes' (yes / no).
        Coverage: yes
        # Generate histograms of number of sites with a given read-depth, from 0 to 200,
        # for each BAM and for each 'RegionsOfInterest' specified in 'Prefixes' (yes / no).
        Depths: yes
        # Generate summary table for each target (yes / no)
        Summary: yes


    # Map of prefixes by name, each having a Path, which specifies the location of the
    # BWA/Bowtie2 index, and optional regions for which additional statistics are produced.
    Prefixes:
      # Replace 'NAME_OF_PREFIX' with name of the prefix; this name is used in summary
      # statistics and as part of output filenames.
      rCRS:
        # Replace 'PATH_TO_PREFIX' with the path to .fasta file containing the references
        # against which reads are to be mapped. Using the same name as filename is strongly
        # recommended (e.g. /path/to/Human_g1k_v37.fasta should be named 'Human_g1k_v37').
        Path: prefixes/rCRS.fasta

        # (Optional) Uncomment and replace 'PATH_TO_BEDFILE' with the path to a .bed file
        # listing extra regions for which coverage / depth statistics should be calculated;
        # if no names are specified for the BED records, results are named after the
        # chromosome / contig. Replace 'NAME' with the desired name for these regions.
    #    RegionsOfInterest:
    #      NAME: PATH_TO_BEDFILE


    # You can also add comments like these to document your experiment
    MyFilename:
      MySample:
        ACGATA:
          Lane_1: data/ACGATA_L1_R{Pair}_*.fastq.gz

        GCTCTG:
          Lane_1: data/GCTCTG_L1_*.fastq.gz

        TGCTCA:
          Lane_1: data/TGCTCA_L1_*.fastq.gz
          Lane_2: data/TGCTCA_L2_R{Pair}_*.fastq.gz


With this makefile in hand, the pipeline may be executed using the following command:

.. code-block:: bash

    $ paleomix bam run makefile.yaml

The pipeline will run as many simultaneous processes as there are cores in the current system, but this behavior may be changed by using the `--max-threads` command-line option. Use the `--help` command-line option to view additional options available when running the pipeline. By default, output files are placed in the same folder as the makefile, but this behavior may be changed by setting the `--destination` command-line option. For this projects, these files include the following:

.. code-block:: bash

    $ ls -d MyFilename*
    MyFilename
    MyFilename.rCRS.coverage
    MyFilename.rCRS.depths
    MyFilename.rCRS.mapDamage
    MyFilename.summary

The files include a table of the average coverage, a histogram of the per-site coverage (depths), a folder containing one set of mapDamage plots per library, and the final BAM file and its index (the `.bai` file), as well as a table summarizing the entire analysis. For a more detailed description of the files generated by the pipeline, please refer to the :ref:`bam_filestructure` section; should problems occur during the execution of the pipeline, then please verify that the makefile is correctly filled out as described above, and refer to the :ref:`troubleshooting_bam` section.

.. note::
    The first item, `MyFilename`, is a folder containing intermediate files generated while running the pipeline, required due to the many steps involved in a typical analyses, and which also allows for the pipeline to resume should the process be interrupted. This folder will typically take up 3-4x the disk-space used by the final BAM file(s), and can safely be removed once the pipeline has run to completion, in order to reduce disk-usage.


.. _SAM/BAM specification: http://samtools.sourceforge.net/SAM1.pdf
.. _seqtk: https://github.com/lh3/seqtk
.. _Phred quality-scores: https://en.wikipedia.org/wiki/FASTQ_format#Quality
.. _AdapterRemoval documentation: https://github.com/MikkelSchubert/adapterremoval