#!/usr/bin/python3
#
# Copyright (c) 2012 Mikkel Schubert <MikkelSch@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import logging
import os

import paleomix.common.logging
import paleomix.pipelines.phylo.example as example
import paleomix.pipelines.phylo.parts.genotype as genotype
import paleomix.pipelines.phylo.parts.msa as msa
import paleomix.pipelines.phylo.parts.phylo as phylo

from paleomix import resources
from paleomix.common.yaml import YAMLError
from paleomix.pipeline import Pypeline
from paleomix.pipelines.phylo.config import build_parser
from paleomix.pipelines.phylo.makefile import MakefileError, read_makefiles


_COMMANDS = {
    "genotype": genotype.chain,
    "msa": msa.chain,
    "phylogeny": phylo.chain_examl,
}


def main(argv):
    commands = [it.lower().strip() for it in argv[0].split("+")] if argv else []
    if "example" in commands:
        return example.main(argv[1:])

    parser = build_parser()
    config = parser.parse_args(argv)
    config.commands = commands
    if "help" in config.commands:
        parser.print_help()
        return 0
    elif any(key in config.commands for key in ("new", "makefile", "mkfile")):
        return _main_template(config)

    return _main_pipeline(config)


def _main_pipeline(config):
    log = logging.getLogger(__name__)

    commands = []
    for key in config.commands:
        func = _COMMANDS.get(key)
        if func is None:
            log.error("unknown command %r", key)
            return 1

        commands.append((key, func))

    paleomix.common.logging.initialize(
        log_level=config.log_level,
        log_file=config.log_file,
        auto_log_file=os.path.join(config.temp_root, "phylo_pipeline"),
    )

    if not os.path.exists(config.temp_root):
        try:
            os.makedirs(config.temp_root)
        except OSError as error:
            log.error("Could not create temp root:\n\t%s", error)
            return 1

    if not os.access(config.temp_root, os.R_OK | os.W_OK | os.X_OK):
        log.error("Insufficient permissions for temp root: %r", config.temp_root)
        return 1

    try:
        makefiles = read_makefiles(config, commands)
    except (MakefileError, YAMLError, IOError) as error:
        log.error("Error reading makefiles:\n%s", error)
        return 1

    for (command_key, command_func) in commands:
        log.info("Building %s pipeline", command_key)
        command_func(config, makefiles)

    nodes = []
    for makefile in makefiles:
        nodes.extend(makefile.get("Nodes", ()))

    pipeline = Pypeline(
        nodes=nodes,
        temp_root=config.temp_root,
        max_threads=config.max_threads,
    )

    return pipeline.run(config.pipeline_mode)


def _main_template(_config):
    print(resources.template("phylo.yaml"))

    return 0
