#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Mikkel Schubert <MikkelSch@gmail.com>
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
"""Factory for AtomicCmds for the various PALEOMIX commands.

Ensures that the version called corresponds to the running version, in case
multiple versions are present in the users' PATH, or that the current version
is not available from the users' PATH.
"""
import paleomix.common.versions as versions
import paleomix.main
from paleomix.common.command import AtomicCmd, AuxilleryFile
from paleomix.common.utilities import safe_coerce_to_tuple

CHECK = versions.Requirement(
    ["%(PYTHON)s", "--version"],
    regexp=r"Python (\d+\.\d+\.\d+)",
    specifiers=">=3.7",
    name="Python",
)


def new(args, **kwargs):
    """Returns AtomicCmd setup to call the tools accessible through the
    'paleomix' command-line tool. This builder adds executable / version checks
    for the specified command, but does not add any arguments. Thus, calling
    new with the argument "cat" produces the equivalent of ["paleomix", "cat"].
    """
    script = paleomix.main.__file__
    args = safe_coerce_to_tuple(args)

    requirements = list(kwargs.get("requirements", ()))
    requirements.append(CHECK)
    kwargs["requirements"] = requirements

    command = AtomicCmd(("%(PYTHON)s", script) + args, **kwargs)
    command.add_extra_files([AuxilleryFile(script)])

    return command
