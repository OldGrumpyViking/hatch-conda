# SPDX-FileCopyrightText: 2021-present Ofek Lev <oss@ofek.dev>
#
# SPDX-License-Identifier: MIT
from hatchling.plugin import hookimpl

from .plugin import CondaEnvironment


@hookimpl
def hatch_register_environment():
    return CondaEnvironment
