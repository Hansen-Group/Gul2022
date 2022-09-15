import os

import logging

import paleomix.node
import paleomix.common.logging

from paleomix.common.fileutils import swap_ext
from paleomix.common.yaml import YAMLError

from paleomix.pipeline import Pypeline
from paleomix.pipelines.ngs.config import build_parser
from paleomix.pipelines.ngs.project import load_project, MakefileError
from paleomix.pipelines.ngs.pipeline import build_pipeline
from paleomix import resources


def main(argv):
    parser = build_parser()
    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)
    if args.command == "run":
        return _main_run(args)
    elif args.command == "new":
        return _main_new(args)

    parser.print_help()
    return 0


def _main_run(args):
    if args.output is None:
        args.output = swap_ext(args.project, ".output")
    # FIXME: Add cli option
    args.temp_root = os.path.join(args.output, "cache", "temp")

    # FIXME: Place logs in output folder
    paleomix.common.logging.initialize(
        log_level=args.log_level,
        log_file=args.log_file,
        auto_log_file=os.path.join(args.output, "cache", "logs", "pipeline"),
    )

    logger = logging.getLogger(__name__)

    try:
        logger.info("Reading project from %r", args.project)
        project = load_project(args.project)
    except (MakefileError, YAMLError, IOError) as error:
        logger.error("Error reading project: %s", error)
        return 1

    try:
        logger.info("Building pipeline for project")
        nodes = build_pipeline(args, project)
    except paleomix.node.NodeError as error:
        logger.error("Error while building pipeline: %s", error)
        return 1

    pipeline = Pypeline(
        nodes=nodes,
        temp_root=args.temp_root,
        max_threads=args.max_threads,
        implicit_dependencies=True,
    )

    return pipeline.run(args.pipeline_mode)


def _main_new(args):
    print(resources.template("ngs.yaml"))

    return 0
