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
import sys
import json

import click

from aws_mp_utils.changeset import start_mp_change_set
from aws_mp_utils.offer import create_update_offer_change_doc
from aws_mp_utils.offer_dimensions import (
    get_available_dimensions,
    create_restrict_dimensions_change_doc,
    create_add_dimensions_change_doc
)
from aws_mp_utils.offer_instance_types import (
    get_available_instance_types,
    create_add_instance_types_change_doc,
    create_restrict_instance_types_change_doc
)
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
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@add_options(shared_options)
@click.pass_context
def update_information(
    context,
    catalog,
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
    Updates information in an offer.

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
        'change_set': [change_doc],
        'catalog': catalog
    }

    if max_rechecks:
        options['max_rechecks'] = max_rechecks
    if conflict_wait_period:
        options['conflict_wait_period'] = conflict_wait_period

    with handle_errors(config_data.log_level, config_data.no_color):
        response = start_mp_change_set(**options)

    output = f'Change set Id: {response["ChangeSetId"]}'
    echo_style(output, config_data.no_color, fg='green')


# -----------------------------------------------------------------------------
# Offer list-dimensions command
@offer.command
@click.option(
    '--offer-id',
    type=click.STRING,
    required=True,
    help='The unique identifier the offer in the AWS Marketplace.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@add_options(shared_options)
@click.pass_context
def list_dimensions(
    context,
    catalog,
    offer_id,
    **kwargs
):
    """
    Lists the available dimensions for the given offer.

    """

    try:
        process_shared_options(context.obj, kwargs)
        config_data = get_config(context.obj)
        logger = logging.getLogger('aws_mp_utils')
        logger.setLevel(config_data.log_level)

        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        # list current dimentions in the provided offer
        dimensions = get_available_dimensions(
            client=client,
            offer_id=offer_id,
            catalog=catalog
        )
        if dimensions:
            headers = f"{'Key':<30} | {'Unit':<10} | {'Types':<20}"
            rows = [headers, '-' * len(headers)]
            for dim in dimensions:
                key = dim.get('Key', '')
                unit = dim.get('Unit', '')
                types = ', '.join(dim.get('Types', []))
                rows.append(f"{key:<30} | {unit:<10} | {types:<20}")
            output = '\n'.join(rows)
            echo_style(output, config_data.no_color, fg='green')
        else:
            output = ('No dimensions were found')
            echo_style(output, config_data.no_color, fg='red')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Offer restrict-dimensions command
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
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--details-document',
    type=click.STRING,
    default=None,
    help=(
        'A JSON formatted string containing the details document for'
        'restricting the offer dimensions.'
    )
)
@click.option(
    '--details-document-file',
    type=click.STRING,
    default=None,
    help='A path to a file containing a JSON formatted string with the '
         'details document for restricting the offer dimensions.'
)
@add_options(shared_options)
@click.pass_context
def restrict_dimensions(
    context,
    details_document_file,
    details_document,
    catalog,
    offer_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Removes the provided dimensions from the given offer.

    """

    if details_document is not None:
        try:
            json.loads(details_document)
        except json.JSONDecodeError as e:
            raise click.BadParameter(
                f"Invalid JSON provided for --details-document: {e}"
            )
    elif details_document_file is not None:
        try:
            with open(details_document_file, 'r') as f:
                details_document = f.read()
                json.loads(details_document)
        except json.JSONDecodeError as e:
            raise click.BadParameter(
                f"Invalid JSON provided in file --details-document-file: {e}"
            )
        except FileNotFoundError as e:
            raise click.BadParameter(
                f"File --details-document-file not found: {e}"
            )
    else:
        raise click.BadParameter(
            "One of ['--details-document-file', "
            "'--details-document'] parameters is required to restrict "
            "dimensions in an offer."
        )

    try:
        process_shared_options(context.obj, kwargs)
        config_data = get_config(context.obj)
        logger = logging.getLogger('aws_mp_utils')
        logger.setLevel(config_data.log_level)

        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        change_set_doc = create_restrict_dimensions_change_doc(
                offer_id=offer_id,
                details_document=details_document
            )

        # Change set submission
        options = {
            'client': client,
            'change_set': [change_set_doc],
            'catalog': catalog
        }

        if max_rechecks:
            options['max_rechecks'] = max_rechecks
        if conflict_wait_period:
            options['conflict_wait_period'] = conflict_wait_period
        with handle_errors(config_data.log_level, config_data.no_color):
            response = start_mp_change_set(**options)

        output = f'Change set Id: {response["ChangeSetId"]}'
        echo_style(output, config_data.no_color, fg='green')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Offer add-dimensions command
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
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--details-document',
    type=click.STRING,
    default=None,
    help='A JSON formatted string containing the details document for'
         'adding the offer dimensions.'
)
@click.option(
    '--details-document-file',
    type=click.STRING,
    default=None,
    help=(
        'A path to a file containing a JSON formatted string with the '
        'details document for adding the offer dimensions.'
    )
)
@add_options(shared_options)
@click.pass_context
def add_dimensions(
    context,
    details_document_file,
    details_document,
    catalog,
    offer_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Adds the provided dimensions to the given offer.

    """

    if details_document is not None:
        try:
            json.loads(details_document)
        except json.JSONDecodeError as e:
            raise click.BadParameter(
                f"Invalid JSON provided for --details-document: {e}"
            )
    elif details_document_file is not None:
        try:
            with open(details_document_file, 'r') as f:
                details_document = f.read()
                json.loads(details_document)
        except json.JSONDecodeError as e:
            raise click.BadParameter(
                f"Invalid JSON provided in file --details-document-file: {e}"
            )
        except FileNotFoundError as e:
            raise click.BadParameter(
                f"File --details-document-file not found: {e}"
            )
    else:
        raise click.BadParameter(
            "One of ['--details-document-file', "
            "'--details-document'] parameters is required to add "
            "dimensions in an offer."
        )

    try:
        process_shared_options(context.obj, kwargs)
        config_data = get_config(context.obj)
        logger = logging.getLogger('aws_mp_utils')
        logger.setLevel(config_data.log_level)

        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        change_set_doc = create_add_dimensions_change_doc(
                offer_id=offer_id,
                details_document=details_document
            )

        # Change set submission
        options = {
            'client': client,
            'change_set': [change_set_doc],
            'catalog': catalog
        }

        if max_rechecks:
            options['max_rechecks'] = max_rechecks
        if conflict_wait_period:
            options['conflict_wait_period'] = conflict_wait_period
        with handle_errors(config_data.log_level, config_data.no_color):
            response = start_mp_change_set(**options)

        output = f'Change set Id: {response["ChangeSetId"]}'
        echo_style(output, config_data.no_color, fg='green')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Offer list-available-instance-types command
@offer.command
@click.option(
    '--offer-id',
    type=click.STRING,
    required=True,
    help='The unique identifier the offer in the AWS Marketplace.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@add_options(shared_options)
@click.pass_context
def list_available_instance_types(
    context,
    catalog,
    offer_id,
    **kwargs
):
    """
    Lists the available instance types for the given offer.

    """

    try:
        process_shared_options(context.obj, kwargs)
        config_data = get_config(context.obj)
        logger = logging.getLogger('aws_mp_utils')
        logger.setLevel(config_data.log_level)

        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        # list current dimentions in the provided offer
        instance_types = get_available_instance_types(
            client=client,
            offer_id=offer_id,
            catalog=catalog
        )
        if instance_types:
            headers = f"{'Instance type':<30}"
            rows = [headers, '-' * len(headers)]
            for instance_type in instance_types:
                rows.append(f"{instance_type:<30}")
            output = '\n'.join(rows)
            echo_style(output, config_data.no_color, fg='green')
        else:
            output = ('No available instance types were found')
            echo_style(output, config_data.no_color, fg='red')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Offer restrict instance types command
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
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--details-document',
    type=click.STRING,
    default=None,
    help=(
        'A JSON formatted string containing the details document for'
        'restricting the offer instance types.'
    )
)
@click.option(
    '--details-document-file',
    type=click.STRING,
    default=None,
    help='A path to a file containing a JSON formatted string with the '
         'details document for restricting the offer instance types.'
)
@add_options(shared_options)
@click.pass_context
def restrict_instance_types(
    context,
    details_document_file,
    details_document,
    catalog,
    offer_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Restricts the provided instance types from the given offer.

    """

    if details_document is not None:
        try:
            json.loads(details_document)
        except json.JSONDecodeError as e:
            raise click.BadParameter(
                f"Invalid JSON provided for --details-document: {e}"
            )
    elif details_document_file is not None:
        try:
            with open(details_document_file, 'r') as f:
                details_document = f.read()
                json.loads(details_document)
        except json.JSONDecodeError as e:
            raise click.BadParameter(
                f"Invalid JSON provided in file --details-document-file: {e}"
            )
        except FileNotFoundError as e:
            raise click.BadParameter(
                f"File --details-document-file not found: {e}"
            )
    else:
        raise click.BadParameter(
            "One of ['--details-document-file', "
            "'--details-document'] parameters is required to restrict "
            "instance types in an offer."
        )

    try:
        process_shared_options(context.obj, kwargs)
        config_data = get_config(context.obj)
        logger = logging.getLogger('aws_mp_utils')
        logger.setLevel(config_data.log_level)

        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        change_set_doc = create_restrict_instance_types_change_doc(
                offer_id=offer_id,
                details_document=details_document
            )

        # Change set submission
        options = {
            'client': client,
            'change_set': [change_set_doc],
            'catalog': catalog
        }

        if max_rechecks:
            options['max_rechecks'] = max_rechecks
        if conflict_wait_period:
            options['conflict_wait_period'] = conflict_wait_period
        with handle_errors(config_data.log_level, config_data.no_color):
            response = start_mp_change_set(**options)

        output = f'Change set Id: {response["ChangeSetId"]}'
        echo_style(output, config_data.no_color, fg='green')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Offer add-instance-types command
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
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--details-document',
    type=click.STRING,
    default=None,
    help='A JSON formatted string containing the details document for'
         'adding the instance types to the offer.'
)
@click.option(
    '--details-document-file',
    type=click.STRING,
    default=None,
    help=(
        'A path to a file containing a JSON formatted string with the '
        'details document for adding the offer instance types.'
    )
)
@add_options(shared_options)
@click.pass_context
def add_instance_types(
    context,
    details_document_file,
    details_document,
    catalog,
    offer_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Adds the provided instance types to the given offer.

    """

    if details_document is not None:
        try:
            json.loads(details_document)
        except json.JSONDecodeError as e:
            raise click.BadParameter(
                f"Invalid JSON provided for --details-document: {e}"
            )
    elif details_document_file is not None:
        try:
            with open(details_document_file, 'r') as f:
                details_document = f.read()
                json.loads(details_document)
        except json.JSONDecodeError as e:
            raise click.BadParameter(
                f"Invalid JSON provided in file --details-document-file: {e}"
            )
        except FileNotFoundError as e:
            raise click.BadParameter(
                f"File --details-document-file not found: {e}"
            )
    else:
        raise click.BadParameter(
            "One of ['--details-document-file', "
            "'--details-document'] parameters is required to add "
            "dimensions in an offer."
        )

    try:
        process_shared_options(context.obj, kwargs)
        config_data = get_config(context.obj)
        logger = logging.getLogger('aws_mp_utils')
        logger.setLevel(config_data.log_level)

        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        change_set_doc = create_add_instance_types_change_doc(
                offer_id=offer_id,
                details_document=details_document
            )

        # Change set submission
        options = {
            'client': client,
            'change_set': [change_set_doc],
            'catalog': catalog
        }

        if max_rechecks:
            options['max_rechecks'] = max_rechecks
        if conflict_wait_period:
            options['conflict_wait_period'] = conflict_wait_period
        with handle_errors(config_data.log_level, config_data.no_color):
            response = start_mp_change_set(**options)

        output = f'Change set Id: {response["ChangeSetId"]}'
        echo_style(output, config_data.no_color, fg='green')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)