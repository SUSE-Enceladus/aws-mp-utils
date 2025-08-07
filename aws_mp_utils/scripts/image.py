# -*- coding: utf-8 -*-

"""AWS marketplace catalog image utils cli module."""

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

import logging
import sys

import click

from aws_mp_utils.changeset import (
    get_image_delivery_option_id,
    create_restrict_version_change_doc,
    start_mp_change_set
)
from aws_mp_utils.scripts.cli_utils import (
    add_options,
    get_config,
    process_shared_options,
    shared_options,
    echo_style,
    get_mp_client
)


# -----------------------------------------------------------------------------
# Image commands function
@click.group(name="image")
def image():
    """
    Commands for marketplace catalog AMI product management.
    """


# -----------------------------------------------------------------------------
@image.command
@click.option(
    '--max-rechecks',
    type=click.IntRange(min=0),
    help='The maximum number of checks that are performed when a marketplace '
         'change cannot be applied because some resource is affected by some '
         'other ongoing change.'
)
@click.option(
    '--conflict-wait-period',
    type=click.IntRange(min=0),
    help='The period (in seconds) that is waited between checks for the '
         'ongoing mp change to be finished.'
)
@click.option(
    '--entity-id',
    type=click.STRING,
    required=True,
    help='The unique identifier the product in the AWS Marketplace. '
         'The expected format of the ID is a UUID.'
)
@click.option(
    '--ami-id',
    type=click.STRING,
    required=True,
    help='The EC2 image ID for the version to be restricted.'
)
@add_options(shared_options)
@click.pass_context
def restrict_version(
    context,
    ami_id,
    entity_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)

    client = get_mp_client(
        config_data.profile,
        config_data.region
    )
    try:
        delivery_option_id = get_image_delivery_option_id(
            client,
            entity_id,
            ami_id
        )
    except Exception as error:
        echo_style(
            'Unable to get delivery option id for the given product.',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(error), config_data.no_color, fg='red')
        sys.exit(1)

    change_doc = create_restrict_version_change_doc(
        entity_id,
        delivery_option_id
    )

    options = {
        'client': client,
        'change_set': [change_doc]
    }

    if max_rechecks:
        options['max_rechecks'] = max_rechecks
    if conflict_wait_period:
        options['conflict_wait_period'] = conflict_wait_period

    try:
        response = start_mp_change_set(**options)
    except Exception as error:
        echo_style(
            'Unable to start change set',
            config_data.no_color,
            fg='red'
        )
        echo_style(str(error), config_data.no_color, fg='red')
        sys.exit(1)

    output = f'Change set Id: {response["ChangeSetId"]}'
    echo_style(output, config_data.no_color, fg='green')
