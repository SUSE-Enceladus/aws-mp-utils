# -*- coding: utf-8 -*-

"""AWS marketplace catalog ami product utils cli module."""

# Copyright (c) 2026 SUSE LLC
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
import os

import click

from aws_mp_utils.changeset import start_mp_change_set
from aws_mp_utils.ami_product_dimensions import (
    get_available_dimensions,
    create_restrict_dimensions_change_doc,
    create_add_dimensions_change_doc
)
from aws_mp_utils.ami_product_instance_types import (
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
# Ami Product commands function
@click.group(name="ami-product")
def ami_product():
    """
    Commands for marketplace catalog Ami products management.
    """


# -----------------------------------------------------------------------------
# Ami product list-dimensions command
@ami_product.command
@click.option(
    '--product-id',
    type=click.STRING,
    required=True,
    help='The unique identifier for the product in the AWS Marketplace.'
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
    product_id,
    **kwargs
):
    """
    Lists the available dimensions for the given product.
    """

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)

    dimensions = []

    try:
        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        # list current dimentions in the provided product
        dimensions = get_available_dimensions(
            client=client,
            product_id=product_id,
            catalog=catalog
        )
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)

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


# -----------------------------------------------------------------------------
# Ami Product restrict-dimensions command
@ami_product.command
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
    '--product-id',
    type=click.STRING,
    required=True,
    help='The unique identifier for the product_id in the AWS Marketplace.'
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
    required=True,
    help=(
        'A JSON formatted string or a path to a file containing the '
        'details document for restricting the product dimensions.'
    )
)
@add_options(shared_options)
@click.pass_context
def restrict_dimensions(
    context,
    details_document,
    catalog,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Removes the provided dimensions from the given product.
    """

    try:
        if os.path.isfile(details_document):
            with open(details_document, 'r') as f:
                details_document = f.read()
    except OSError:
        pass

    try:
        details_document = json.loads(details_document)
    except json.JSONDecodeError as e:
        raise click.BadParameter(
            f"Invalid JSON provided for --details-document: {e}"
        )

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)
    response = {}

    try:

        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        change_set_doc = create_restrict_dimensions_change_doc(
                product_id=product_id,
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

    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)

    if response and 'ChangeSetId' in response:
        output = f'Change set Id: {response["ChangeSetId"]}'
        echo_style(output, config_data.no_color, fg='green')


# -----------------------------------------------------------------------------
# Ami-product add-dimensions command
@ami_product.command
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
    '--product-id',
    type=click.STRING,
    required=True,
    help='The unique identifier for the product in the AWS Marketplace.'
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
    required=True,
    help=(
        'A JSON formatted string or a path to a file containing the '
        'details document for adding the product dimensions.'
    )
)
@add_options(shared_options)
@click.pass_context
def add_dimensions(
    context,
    details_document,
    catalog,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Adds the provided dimensions to the given product.
    """

    try:
        if os.path.isfile(details_document):
            with open(details_document, 'r') as f:
                details_document = f.read()
    except OSError:
        pass

    try:
        details_document = json.loads(details_document)
    except json.JSONDecodeError as e:
        raise click.BadParameter(
            f"Invalid JSON provided for --details-document: {e}"
        )

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)
    response = {}

    try:
        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        change_set_doc = create_add_dimensions_change_doc(
                product_id=product_id,
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
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)

    if response and 'ChangeSetId' in response:
        output = f'Change set Id: {response["ChangeSetId"]}'
        echo_style(output, config_data.no_color, fg='green')


# -----------------------------------------------------------------------------
# Ami Product list-available-instance-types command
@ami_product.command
@click.option(
    '--product-id',
    type=click.STRING,
    required=True,
    help='The unique identifier for the product in the AWS Marketplace.'
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
    product_id,
    **kwargs
):
    """
    Lists the available instance types for the given product.
    """
    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)
    output = ''

    try:
        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        # list current dimentions in the provided product
        instance_types = get_available_instance_types(
            client=client,
            product_id=product_id,
            catalog=catalog
        )
        if instance_types:
            headers = f"{'Instance type':<30}"
            rows = [headers, '-' * len(headers)]
            for instance_type in instance_types:
                rows.append(f"{instance_type:<30}")
            output = '\n'.join(rows)
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)

    if output:
        echo_style(output, config_data.no_color, fg='green')
    else:
        output = ('No available instance types were found')
        echo_style(output, config_data.no_color, fg='red')


# -----------------------------------------------------------------------------
# Ami Product restrict instance types command
@ami_product.command
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
    '--product-id',
    type=click.STRING,
    required=True,
    help='The unique identifier for the product in the AWS Marketplace.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--instance-types',
    type=click.STRING,
    required=True,
    help='A comma separated list of containing the instance types that will '
         'be restricted in the product.'
)
@add_options(shared_options)
@click.pass_context
def restrict_instance_types(
    context,
    instance_types,
    catalog,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Restricts the provided instance types from the given product.
    """

    if '[' in instance_types or ']' in instance_types:
        raise click.BadParameter(
            'The "--instance-types" expected format is a string containing the'
            'instance types separated by commas.'
        )
    instance_types = instance_types.split(',')

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)
    response = {}

    try:
        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        change_set_doc = create_restrict_instance_types_change_doc(
            product_id=product_id,
            instance_types=instance_types
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
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)

    if response and 'ChangeSetId' in response:
        output = f'Change set Id: {response["ChangeSetId"]}'
        echo_style(output, config_data.no_color, fg='green')


# -----------------------------------------------------------------------------
# Ami product add-instance-types command
@ami_product.command
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
    '--product-id',
    type=click.STRING,
    required=True,
    help='The unique identifier for the product in the AWS Marketplace.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--instance-types',
    type=click.STRING,
    required=True,
    help='A comma separated list of containing the instance types that will '
         'be added to the product.'
)
@add_options(shared_options)
@click.pass_context
def add_instance_types(
    context,
    instance_types,
    catalog,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Adds the provided instance types to the given product.
    """

    if '[' in instance_types or ']' in instance_types:
        raise click.BadParameter(
            'The "--instance-types" expected format is a string containing the'
            'instance types separated by commas.'
        )
    instance_types = instance_types.split(',')

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)
    response = {}

    try:
        client = get_mp_client(
            config_data.profile,
            config_data.region
        )

        change_set_doc = create_add_instance_types_change_doc(
            product_id=product_id,
            instance_types=instance_types
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
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)

    if response and 'ChangeSetId' in response:
        output = f'Change set Id: {response["ChangeSetId"]}'
        echo_style(output, config_data.no_color, fg='green')
