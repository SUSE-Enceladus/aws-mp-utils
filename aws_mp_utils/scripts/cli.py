# -*- coding: utf-8 -*-

"""AWS MP utils cli module."""

# Copyright (c) 2025 SUSE LLC
#
# This file is part of aws_mp_utils. aws_mp_utils provides an
# api and command line utilities for handling marketplace catalog API
# in the AWS Cloud.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import click

from aws_mp_utils.cli.container import container
from aws_mp_utils.cli.image import image
from aws_mp_utils.cli.offer import offer


# -----------------------------------------------------------------------------
# license function
def print_license(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('GPLv3+')
    ctx.exit()


# -----------------------------------------------------------------------------
# Main function
@click.group()
@click.version_option()
@click.option(
    '--license',
    is_flag=True,
    callback=print_license,
    expose_value=False,
    is_eager=True,
    help='Show license information.'
)
@click.pass_context
def main(context):
    """
    The command line interface provides AWS Marketplace Catalog utilities.

    This includes handling changesets for images, containers and offers.
    """
    if context.obj is None:
        context.obj = {}
    pass


main.add_command(image)
main.add_command(container)
main.add_command(offer)
