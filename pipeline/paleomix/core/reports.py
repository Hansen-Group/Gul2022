#!/usr/bin/python3
#
# Copyright (c) 2021 Mikkel Schubert <MikkelSch@gmail.com>
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
import os
import sys
from typing import IO, Dict, Iterable, Set, Tuple, Union

from paleomix.common.versions import RequirementError
from paleomix.node import Node
from paleomix.nodegraph import FileStatusCache, NodeGraph

from humanfriendly.terminal import ansi_wrap, terminal_supports_colors


def input_files(nodes: Iterable[Node], file: IO[str] = sys.stdout) -> int:
    input_files: Set[str] = set()
    output_files: Set[str] = set()
    graph, _ = _create_graph(nodes)
    for node in graph.iterflat():
        for filename in node.input_files:
            input_files.add(os.path.abspath(filename))

        for filename in node.output_files:
            output_files.add(os.path.abspath(filename))

    for filename in sorted(input_files - output_files):
        print(filename, file=file)

    return 0


def output_files(nodes: Iterable[Node], file: IO[str] = sys.stdout) -> int:
    output_files: Dict[str, str] = {}
    graph, cache = _create_graph(nodes)

    def _set_output_file_state(filenames: Iterable[str], state: str):
        for filename in filenames:
            output_files[os.path.abspath(filename)] = state

    for node in graph.iterflat():
        state = graph.get_node_state(node)
        if state == NodeGraph.DONE:
            _set_output_file_state(node.output_files, "Ready      ")
            continue

        # Pending/queued nodes may have outdated output files
        missing_files = frozenset(cache.missing_files(node.output_files))
        _set_output_file_state(missing_files, "Missing    ")
        _set_output_file_state(node.output_files - missing_files, "Outdated   ")

    for filename, state in sorted(output_files.items()):
        print(state, filename, file=file)

    return 0


def required_executables(nodes: Iterable[Node], file: IO[str] = sys.stdout) -> int:
    graph, _ = _create_graph(nodes)

    template = "  {: <20s} {: <11s} {}"
    print(template.format("Executable", "Version", "Required version"), file=file)
    for requirement in sorted(graph.requirements, key=lambda it: it.name.lower()):
        try:
            version = requirement.version_str()
        except RequirementError:
            version = "ERROR"

        print(
            template.format(requirement.name, version, requirement.specifiers),
            file=file,
        )

    return 0


def pipeline_tasks(tasks: Iterable[Node], file: IO[str] = sys.stdout) -> int:
    graph, _ = _create_graph(tasks)
    top_tasks = []
    for task, rev_deps in graph._reverse_dependencies.items():
        if not rev_deps:
            top_tasks.append(task)

    # Sort by negative ID to prevent leaf tasks created in the middle of a pipeline
    # from being shown first. These tasks typically generate reports/files for the user.
    top_tasks.sort(key=lambda task: -task.id)

    printer = _TaskPrinter(graph, file)

    cache = set()
    for task in top_tasks:
        printer.print(task)

    return 0


class _TaskPrinter:
    def __init__(self, graph: NodeGraph, file: IO[str]) -> None:
        self._cache = set()
        self._graph = graph
        self._file = file
        self.supports_colors = terminal_supports_colors()

    def print(self, task: Node, indent: int = 0) -> None:
        text = "{}+ {}".format(" " * indent, task)
        if self._is_task_done(task):
            text = self._color_done(text)

        print(text, file=self._file)

        self._cache.add(task)
        skipped_tasks = 0
        skipped_tasks_done = True
        for subtask in task.dependencies:
            if subtask in self._cache:
                skipped_tasks += 1
                skipped_tasks_done &= self._is_task_done(subtask)

                continue

            self.print(subtask, indent + 4)

        if skipped_tasks:
            text = "{}+ {} sub-task(s) ...".format(" " * (indent + 4), skipped_tasks)
            if skipped_tasks_done:
                text = self._color_done(text)

            print(text, file=self._file)

    def _is_task_done(self, task: Node) -> bool:
        return self._graph.get_node_state(task) == self._graph.DONE

    def _color_done(self, value: Union[str, Node]) -> str:
        if self.supports_colors:
            return ansi_wrap(str(value), color="black", bold=True)

        return str(value)


def _create_graph(nodes: Iterable[Node]) -> Tuple[NodeGraph, FileStatusCache]:
    cache = FileStatusCache()
    graph = NodeGraph(
        nodes=nodes,
        implicit_dependencies=True,
        cache_factory=lambda: cache,
    )

    return graph, cache
