# Supplementary information for Gul _et al._ 2022

TODO: Citation

## Genotyping pipeline

The genotyping pipeline is based on [PALEOMIX](https://github.com/MikkelSchubert/paleomix) development version 4bbc7592. For more information, see `genotyping/README.md`.

### Installation instructions

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

### Resource bundle

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

### Results

By defaults, resulting genotypes will be placed in

```bash
configuration.output/genotypes/
```

## Annotations

The annotation pipeline is based on [AnnoVEP](https://github.com/cbmrphenomics/annovep) development version f3847ad5. The annotation pipeline is intended to be run using podman, may used with docker docker as well. For more information, see `annotations/README.md`.

### Installation instructions

```bash
cd annotations
make
./bin/annovep setup
```

Note that the `setup` step downloads approximately 350 GB of data and requires approximately 150 GB of space when done.

### Running the annotation pipeline

```bash
./annotations/annovep pipeline input.vcf.gz output
ls output.tsv*
output.tsv output.tsv.columns
```
