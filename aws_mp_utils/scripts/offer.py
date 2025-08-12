# -*- coding: utf-8 -*-

"""AWS marketplace catalog offer utils cli module."""

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

import click

from aws_mp_utils.changeset import start_mp_change_set
from aws_mp_utils.offer import create_update_offer_change_doc

from aws_mp_utils.scripts.cli_utils import (
    add_options,
    get_config,
    process_shared_options,
    shared_options,
    echo_style,
    get_mp_client,
    handle_errors
)


# -----------------------------------------------------------------------------
# Offer commands function
@click.group(name="offer")
def offer():
    """
    Commands for marketplace catalog offer management.
    """


# -----------------------------------------------------------------------------
@offer.command
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
    '--offer-id',
    type=click.STRING,
    required=True,
    help='The unique identifier the offer in the AWS Marketplace.'
)
@click.option(
    '--name',
    type=click.STRING,
    help='Name associated with the offer for better readability.'
)
@click.option(
    '--description',
    type=click.STRING,
    help='A description of the offer not visible to buyers.'
)
@click.option(
    '--acquisition-channel',
    type=click.Choice(['AwsMarketplace', 'External']),
    help='Indicates if the existing agreement was signed inside or '
         'outside of the AWS Marketplace.'
)
@click.option(
    '--pricing-model',
    type=click.Choice(['Contract', 'Usage', 'Byol', 'Free']),
    help='Indicates which pricing model the existing agreement uses.'
)
@add_options(shared_options)
@click.pass_context
def update_information(
    context,
    pricing_model,
    acquisition_channel,
    description,
    name,
    offer_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Starts a change set to restrict the image version based on the AMI ID

    If there is a conflicting change set the submission will be retried
    based on the wait period and max rechecks.

    If the conflicting change set is not resolved in time an exception
    is raised.
    """
    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)

    client = get_mp_client(
        config_data.profile,
        config_data.region
    )

    change_doc = create_update_offer_change_doc(
        pricing_model=pricing_model,
        acquisition_channel=acquisition_channel,
        description=description,
        name=name,
        offer_id=offer_id,
    )

    options = {
        'client': client,
        'change_set': [change_doc]
    }

    if max_rechecks:
        options['max_rechecks'] = max_rechecks
    if conflict_wait_period:
        options['conflict_wait_period'] = conflict_wait_period

    with handle_errors(config_data.log_level, config_data.no_color):
        response = start_mp_change_set(**options)

    output = f'Change set Id: {response["ChangeSetId"]}'
    echo_style(output, config_data.no_color, fg='green')
