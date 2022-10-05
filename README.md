# Supplementary information for Gul _et al._ 2022

TODO: Citation

For a detailed description of the steps carried out during read processing, genotyping and annotation, see `PIPELINE.md`.

## Genotyping pipeline

The genotyping pipeline is based on [PALEOMIX](https://github.com/MikkelSchubert/paleomix) development version 4bbc7592. This pipeline can be found in the `genotyping` folder. For more information, see `genotyping/README.md`.

### Installing the genotyping pipeline

A conda environment corresponding to the environment in which the data was processed is available in `environment.yaml` to ease replication of the methods. To use, install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) and run

```bash
conda env create -n gul2022 -f environment.yaml
```

The resulting environment may be activated and deactivated with

```bash
conda activate gul2022
conda deactivate
```

The genotyping pipeline may be installed in the conda environment as follows:

```bash
conda activate gul2022
cd genotyping
python3 setup.py install
```

### Resource bundle required for genotyping pipeline

The [GATK Resource Bundle](https://gatk.broadinstitute.org/hc/en-us/articles/360035890811-Resource-bundle) is required to run the genotyping pipeline. Files are expected to be placed in a folder named `resources` in the same folder as the pipeline configuration file (`configuration.yaml`).

If using [BWA mem2](https://github.com/bwa-mem2/bwa-mem2), the human FASTA file may be pre-indexed as follows:

```bash
bwa-mem2 index resources/Homo_sapiens_assembly38.fasta
```

This is normally handled automatically by the genotyping pipeline.

### Running the genotyping pipeline

```bash
conda activate gul2022
paleomix gul2022 run configuration.yaml
```

### Genotyping results

By defaults, resulting genotypes will be placed in `${filename}.output` where `${filename}` corresponds to the configuration filename without the `.yaml` extension. E.g. for the configuration file included in this repository, output will be placed in `configuration.output`:

* The final genotypes (VCF) for all samples can be found in `configuration.output/genotypes/`.
* Per sample alignment files (BAMs) can be found `configuration.output/alignments/`.
* Per sample haplotypes (g.VCFs) can be found in `configuration.output/haplotypes/`.
* Statistics and reports for all stages of the pipeline are located in `configuration.output/statistics/`.
* Temporary files can be found in `configuration.output/cache/`. This folder can safely be deleted once the pipeline has been run to completion.

## Annotations

The annotation pipeline is based on [AnnoVEP](https://github.com/cbmrphenomics/annovep) development version f3847ad5. The annotation pipeline is intended to be run using podman, but may used with docker docker as well. This pipeline can be found in the `annotations` folder. For more information, see `annotations/README.md`.

### Installing the annotation pipeline

The included makefile may be used to build a container image using `podman`:

```bash
cd annotations
make
```

### Resources required for annotation pipeline

The annotation pipeline makes use of the VEP and custom annotation files that must be downloaded before running the pipeline:

```bash
cd annotations
./bin/annovep setup
```

By default this will place the annotation files in `~/annovep`, but this behavior may be changed by setting the `ANNOVEP_CACHE` environmental variable (see `annotations/README.md`). Note that the `setup` step downloads approximately 350 GB of data and requires approximately 150 GB of space when done.

### Running the annotation pipeline

The pipeline takes as input a single VCF file and generated several output files using a user-supplied output prefix:

```bash
./annotations/annovep pipeline input.vcf.gz output
ls output.tsv*
output.tsv output.tsv.columns
```

If no output prefix is supplied, the resulting files will be named using the base name of the input file (e.g. `input` for `input.vcf.gz`).
