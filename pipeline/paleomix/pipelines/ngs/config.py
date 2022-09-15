import multiprocessing

import paleomix
import paleomix.common.logging
import paleomix.pipeline
from paleomix.common.argparse import ArgumentParser

_DEFAULT_CONFIG_FILES = [
    "/etc/paleomix/ngs_pipeline.ini",
    "~/.paleomix/ngs_pipeline.ini",
]


def build_parser():
    parser = ArgumentParser(prog="paleomix ngs")
    parser.set_defaults(command=None)

    subparsers = parser.add_subparsers()
    _build_run_parser(subparsers)
    _build_new_parser(subparsers)

    return parser


def _build_run_parser(subparsers):
    parser = subparsers.add_parser(
        "run",
        help="Run pipeline on provided project file",
        default_config_files=_DEFAULT_CONFIG_FILES,
    )
    parser.set_defaults(command="run")

    parser.add_argument(
        "project",
        help="Run pipeline on these project files",
        metavar="FILE",
    )
    parser.add_argument(
        "output",
        nargs="?",
        metavar="FOLDER",
        help="Output folder for project files; defaults to the project file with an "
        "'.output' extension.",
    )

    parser.add_argument(
        "--run-from",
        metavar="STEP",
        type=str.lower,
        choices=(
            "indexing",
            "haplotyping",
        ),
        default="indexing",
        help="Run the pipeline from and (and including) the specified analytical step",
    )

    parser.add_argument(
        "--run-until",
        metavar="STEP",
        type=str.lower,
        choices=(
            "indexing",
            "pre-trimming-qc",
            "read-trimming",
            "post-trimming-qc",
            "read-mapping",
            "pcr-duplicate-filtering",
            "base-recalibration",
            "mapping-statistics",
            "haplotyping",
            "haplotype-recalibration",
        ),
        default="haplotype-recalibration",
        help="Run the pipeline only until (and including) the specified analytical step",
    )

    parser.add_argument(
        "--bwa-algorithm",
        metavar="NAME",
        type=str.lower,
        choices=("mem", "mem2"),
        default="mem2",
        help="Mapping algorithm to use. Output should be identical, but BWA MEM2 is "
        "faster at the cost of 3x greater RAM usage",
    )

    paleomix.common.logging.add_argument_group(parser)

    group = paleomix.pipeline.add_scheduling_argument_group(parser)

    threaded_software = {
        "fastp": 4,
        "BWA": 8,
        "SAMtools": 3,
    }

    for name, max_default in threaded_software.items():
        group.add_argument(
            f"--max-threads-{name.lower()}",
            type=int,
            default=max(1, min(max_default, multiprocessing.cpu_count() // 2)),
            help=f"Max number of threads to use per {name} instance",
        )

    paleomix.pipeline.add_io_argument_group(parser)


def _build_new_parser(subparsers):
    parser = subparsers.add_parser("new")
    parser.set_defaults(command="new")
