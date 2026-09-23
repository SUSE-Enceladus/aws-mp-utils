# -*- coding: utf-8 -*-

"""AWS marketplace catalog product utils cli module."""

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

import click

from aws_mp_utils.changeset import start_mp_change_set
from aws_mp_utils.product import get_public_offer_id_for_product
from aws_mp_utils.product_dimensions import (
    get_available_dimensions,
    create_restrict_dimensions_change_doc,
    create_add_dimensions_change_doc
)
from aws_mp_utils.product_instance_types import (
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
# Product commands function
@click.group(name="product")
def product():
    """
    Commands for marketplace catalog product management.
    """


# -----------------------------------------------------------------------------
# Product get-offer-id command
@product.command(name='get-offer-id')
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
def get_offer_id(
    context,
    catalog,
    product_id,
    **kwargs
):
    """
    Retrieves the public offer ID for the given product ID.
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

        offer_id = get_public_offer_id_for_product(
            client=client,
            product_id=product_id,
            catalog=catalog
        )
        echo_style(offer_id, config_data.no_color, fg='green')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Product list-dimensions command
@product.command(name='list-dimensions')
@click.option(
    '--output-file',
    '-o',
    type=click.Path(),
    default=None,
    help='Path to a file where the JSON output will be saved.'
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
@add_options(shared_options)
@click.pass_context
def list_dimensions(
    context,
    output_file,
    catalog,
    product_id,
    **kwargs
):
    """
    Lists the available dimensions for the given product.
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

        dimensions = get_available_dimensions(
            client=client,
            product_id=product_id,
            catalog=catalog
        )

        json_output = json.dumps(dimensions, indent=4)
        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_output)
            output = f"Dimensions output written to {output_file}"
            echo_style(output, config_data.no_color, fg='green')
        else:
            echo_style(json_output, config_data.no_color, fg='green')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Product restrict-dimensions command
@product.command
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
    '--entity-type',
    type=click.Choice([
        'AmiProduct@1.0',
        'SaaSProduct@1.0',
        'ContainerProduct@1.0',
        'Product@1.0'
    ]),
    default='AmiProduct@1.0',
    help='The entity type of the product.'
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
        'restricting the product dimensions.'
    )
)
@click.option(
    '--details-document-file',
    type=click.STRING,
    default=None,
    help='A path to a file containing a JSON formatted string with the '
         'details document for restricting the product dimensions.'
)
@add_options(shared_options)
@click.pass_context
def restrict_dimensions(
    context,
    details_document_file,
    details_document,
    catalog,
    entity_type,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Removes the provided dimensions from the given product.

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
            "dimensions in a product."
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
            product_id=product_id,
            details_document=details_document,
            entity_type=entity_type
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
# Product add-dimensions command
@product.command
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
    '--entity-type',
    type=click.Choice([
        'AmiProduct@1.0',
        'SaaSProduct@1.0',
        'ContainerProduct@1.0',
        'Product@1.0'
    ]),
    default='AmiProduct@1.0',
    help='The entity type of the product.'
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
         'adding the product dimensions.'
)
@click.option(
    '--details-document-file',
    type=click.STRING,
    default=None,
    help=(
        'A path to a file containing a JSON formatted string with the '
        'details document for adding the product dimensions.'
    )
)
@add_options(shared_options)
@click.pass_context
def add_dimensions(
    context,
    details_document_file,
    details_document,
    catalog,
    entity_type,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Adds the provided dimensions to the given product.

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
            "dimensions in a product."
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
            product_id=product_id,
            details_document=details_document,
            entity_type=entity_type
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
# Product list-instance-types command
@product.command(name='list-instance-types')
@click.option(
    '--output-file',
    '-o',
    type=click.Path(),
    default=None,
    help='Path to a file where the JSON output will be saved.'
)
@click.option(
    '--json',
    'json_output_flag',
    is_flag=True,
    default=False,
    help='Output the result as a formatted JSON string.'
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
@add_options(shared_options)
@click.pass_context
def list_instance_types(
    context,
    json_output_flag,
    output_file,
    catalog,
    product_id,
    **kwargs
):
    """
    Lists the available instance types for the given product.

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

        instance_types = get_available_instance_types(
            client=client,
            product_id=product_id,
            catalog=catalog
        )

        if output_file:
            json_output = json.dumps(instance_types, indent=4)
            with open(output_file, 'w') as f:
                f.write(json_output)
            output = f"Instance types output written to {output_file}"
            echo_style(output, config_data.no_color, fg='green')
        elif json_output_flag:
            json_output = json.dumps(instance_types, indent=4)
            echo_style(json_output, config_data.no_color, fg='green')
        elif instance_types:
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
# Product restrict instance types command
@product.command(name='restrict-instance-types')
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
    '--entity-type',
    type=click.Choice([
        'AmiProduct@1.0',
        'SaaSProduct@1.0',
        'ContainerProduct@1.0',
        'Product@1.0'
    ]),
    default='AmiProduct@1.0',
    help='The entity type of the product.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--details-document',
    '--instance-types',
    'details_document',
    type=click.STRING,
    default=None,
    help='A JSON formatted string or comma separated list of instance types '
         'to be restricted.'
)
@click.option(
    '--details-document-file',
    '--instance-types-file',
    'details_document_file',
    type=click.STRING,
    default=None,
    help='A path to a file containing a JSON formatted string or comma '
         'separated list of instance types.'
)
@add_options(shared_options)
@click.pass_context
def restrict_instance_types(
    context,
    details_document_file,
    details_document,
    catalog,
    entity_type,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Restricts the provided instance types from the given product.

    """
    if details_document is not None:
        if details_document.strip().startswith(('{', '[')):
            try:
                json.loads(details_document)
            except json.JSONDecodeError as e:
                raise click.BadParameter(
                    f"Invalid JSON provided for --details-document: {e}"
                )
        raw_doc = details_document
    elif details_document_file is not None:
        try:
            with open(details_document_file, 'r') as f:
                raw_doc = f.read()
                if (
                    raw_doc.strip().startswith(('{', '['))
                    or details_document_file.endswith('.json')
                ):
                    json.loads(raw_doc)
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
            "instance types in a product."
        )

    try:
        parsed = json.loads(raw_doc)
        if isinstance(parsed, list):
            instance_types = [
                str(i).strip() for i in parsed if str(i).strip()
            ]
        elif isinstance(parsed, dict):
            types_list = (
                parsed.get('InstanceTypes')
                or parsed.get(
                    'Compatibility', {}
                ).get('AvailableInstanceTypes')
            )
            if isinstance(types_list, list):
                instance_types = [
                    str(i).strip() for i in types_list if str(i).strip()
                ]
            else:
                instance_types = []
        elif isinstance(parsed, str):
            instance_types = [
                i.strip() for i in parsed.split(',') if i.strip()
            ]
        else:
            instance_types = []
    except (json.JSONDecodeError, TypeError):
        instance_types = [
            i.strip() for i in raw_doc.split(',') if i.strip()
        ]

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
            product_id=product_id,
            instance_types=instance_types,
            entity_type=entity_type
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
# Product add-instance-types command
@product.command(name='add-instance-types')
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
    '--entity-type',
    type=click.Choice([
        'AmiProduct@1.0',
        'SaaSProduct@1.0',
        'ContainerProduct@1.0',
        'Product@1.0'
    ]),
    default='AmiProduct@1.0',
    help='The entity type of the product.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--details-document',
    '--instance-types',
    'details_document',
    type=click.STRING,
    default=None,
    help='A JSON formatted string or comma separated list of instance types '
         'to be added.'
)
@click.option(
    '--details-document-file',
    '--instance-types-file',
    'details_document_file',
    type=click.STRING,
    default=None,
    help='A path to a file containing a JSON formatted string or comma '
         'separated list of instance types.'
)
@add_options(shared_options)
@click.pass_context
def add_instance_types(
    context,
    details_document_file,
    details_document,
    catalog,
    entity_type,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Adds the provided instance types to the given product.

    """
    if details_document is not None:
        if details_document.strip().startswith(('{', '[')):
            try:
                json.loads(details_document)
            except json.JSONDecodeError as e:
                raise click.BadParameter(
                    f"Invalid JSON provided for --details-document: {e}"
                )
        raw_doc = details_document
    elif details_document_file is not None:
        try:
            with open(details_document_file, 'r') as f:
                raw_doc = f.read()
                if (
                    raw_doc.strip().startswith(('{', '['))
                    or details_document_file.endswith('.json')
                ):
                    json.loads(raw_doc)
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
            "instance types in a product."
        )

    try:
        parsed = json.loads(raw_doc)
        if isinstance(parsed, list):
            instance_types = [
                str(i).strip() for i in parsed if str(i).strip()
            ]
        elif isinstance(parsed, dict):
            types_list = (
                parsed.get('InstanceTypes')
                or parsed.get(
                    'Compatibility', {}
                ).get('AvailableInstanceTypes')
            )
            if isinstance(types_list, list):
                instance_types = [
                    str(i).strip() for i in types_list if str(i).strip()
                ]
            else:
                instance_types = []
        elif isinstance(parsed, str):
            instance_types = [
                i.strip() for i in parsed.split(',') if i.strip()
            ]
        else:
            instance_types = []
    except (json.JSONDecodeError, TypeError):
        instance_types = [
            i.strip() for i in raw_doc.split(',') if i.strip()
        ]

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
            product_id=product_id,
            instance_types=instance_types,
            entity_type=entity_type
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
