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

import json
import logging
import sys

import click

from aws_mp_utils.changeset import start_mp_change_set
from aws_mp_utils.offer import create_update_offer_change_doc
from aws_mp_utils.offer_countries import (
    get_available_countries,
    create_update_targeting_change_doc
)
from aws_mp_utils.offer_prices import (
    get_offer_prices,
    create_update_pricing_change_doc
)
from aws_mp_utils.product import get_public_offer_id_for_product
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
    '--product-id',
    type=click.STRING,
    default=None,
    help='The unique identifier for the product in the AWS Marketplace.'
)
@click.option(
    '--offer-id',
    type=click.STRING,
    default=None,
    help='The unique identifier for the offer in the AWS Marketplace.'
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
    product_id,
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
    if not offer_id and not product_id:
        raise click.BadParameter(
            "One of ['--product-id', '--offer-id'] parameters is required."
        )

    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)

    client = get_mp_client(
        config_data.profile,
        config_data.region
    )

    with handle_errors(config_data.log_level, config_data.no_color):
        if not offer_id:
            offer_id = get_public_offer_id_for_product(
                client=client,
                product_id=product_id,
                catalog=catalog
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

        response = start_mp_change_set(**options)

    output = f'Change set Id: {response["ChangeSetId"]}'
    echo_style(output, config_data.no_color, fg='green')


# -----------------------------------------------------------------------------
# Offer list-prices command
@offer.command(name='list-prices')
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
    default=None,
    help='The unique identifier for the product in the AWS Marketplace.'
)
@click.option(
    '--offer-id',
    type=click.STRING,
    default=None,
    help='The unique identifier for the offer in the AWS Marketplace.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@add_options(shared_options)
@click.pass_context
def list_prices(
    context,
    output_file,
    catalog,
    offer_id,
    product_id,
    **kwargs
):
    """
    Lists the pricing terms for the given offer or product.
    """
    if not offer_id and not product_id:
        raise click.BadParameter(
            "One of ['--product-id', '--offer-id'] parameters is required."
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

        terms = get_offer_prices(
            client=client,
            product_id=product_id,
            offer_id=offer_id,
            catalog=catalog
        )

        json_output = json.dumps(terms, indent=4)
        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_output)
            output = f"Prices output written to {output_file}"
            echo_style(output, config_data.no_color, fg='green')
        else:
            echo_style(json_output, config_data.no_color, fg='green')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Offer update-prices command
@offer.command(name='update-prices')
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
    default=None,
    help='The unique identifier for the product in the AWS Marketplace.'
)
@click.option(
    '--offer-id',
    type=click.STRING,
    default=None,
    help='The unique identifier for the offer in the AWS Marketplace.'
)
@click.option(
    '--pricing-model',
    type=click.Choice(['Contract', 'Usage', 'Byol', 'Free']),
    default='Usage',
    help='Indicates which pricing model the offer uses.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--details-document',
    '--terms',
    'details_document',
    type=click.STRING,
    default=None,
    help='A JSON formatted string containing the pricing details or terms.'
)
@click.option(
    '--details-document-file',
    '--terms-file',
    'details_document_file',
    type=click.STRING,
    default=None,
    help='A path to a file containing a JSON formatted string with the '
         'pricing details or terms.'
)
@add_options(shared_options)
@click.pass_context
def update_prices(
    context,
    details_document_file,
    details_document,
    catalog,
    pricing_model,
    offer_id,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Updates the pricing terms for the given offer or product.
    """
    if not offer_id and not product_id:
        raise click.BadParameter(
            "One of ['--product-id', '--offer-id'] parameters is required."
        )

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
            "'--details-document'] parameters is required to update "
            "prices in an offer."
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

        if not offer_id:
            offer_id = get_public_offer_id_for_product(
                client=client,
                product_id=product_id,
                catalog=catalog
            )

        change_set_doc = create_update_pricing_change_doc(
            offer_id=offer_id,
            details_document=details_document,
            pricing_model=pricing_model
        )

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
# Offer list-countries command
@offer.command(name='list-countries')
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
    default=None,
    help='The unique identifier for the product in the AWS Marketplace.'
)
@click.option(
    '--offer-id',
    type=click.STRING,
    default=None,
    help='The unique identifier for the offer in the AWS Marketplace.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@add_options(shared_options)
@click.pass_context
def list_countries(
    context,
    output_file,
    catalog,
    offer_id,
    product_id,
    **kwargs
):
    """
    Lists the available target countries for the given offer or product.
    """
    if not offer_id and not product_id:
        raise click.BadParameter(
            "One of ['--product-id', '--offer-id'] parameters is required."
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

        countries = get_available_countries(
            client=client,
            product_id=product_id,
            offer_id=offer_id,
            catalog=catalog
        )

        if output_file:
            json_output = json.dumps(countries, indent=4)
            with open(output_file, 'w') as f:
                f.write(json_output)
            output = f"Countries output written to {output_file}"
            echo_style(output, config_data.no_color, fg='green')
        elif countries:
            country_str = ",".join(countries)
            output = f"Available Countries ({len(countries)}):\n{country_str}"
            echo_style(output, config_data.no_color, fg='green')
        else:
            output = 'No targeted country codes found for this offer.'
            echo_style(output, config_data.no_color, fg='red')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Offer update-countries command
@offer.command(name='update-countries')
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
    default=None,
    help='The unique identifier for the product in the AWS Marketplace.'
)
@click.option(
    '--offer-id',
    type=click.STRING,
    default=None,
    help='The unique identifier for the offer in the AWS Marketplace.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--details-document',
    '--countries',
    '--country-codes',
    'details_document',
    type=click.STRING,
    default=None,
    help='A JSON formatted string or comma separated list of 2-letter ISO '
         'country codes (e.g., US,DE,FR).'
)
@click.option(
    '--details-document-file',
    '--countries-file',
    'details_document_file',
    type=click.STRING,
    default=None,
    help='A path to a file containing a JSON formatted string or comma '
         'separated list of 2-letter ISO country codes.'
)
@add_options(shared_options)
@click.pass_context
def update_countries(
    context,
    details_document_file,
    details_document,
    catalog,
    offer_id,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Sets the available target countries for the given offer or product.
    """
    if not offer_id and not product_id:
        raise click.BadParameter(
            "One of ['--product-id', '--offer-id'] parameters is required."
        )

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
            "'--details-document'] parameters is required to update "
            "countries in an offer."
        )

    try:
        parsed = json.loads(raw_doc)
        if isinstance(parsed, list):
            country_list = [
                str(c).strip() for c in parsed if str(c).strip()
            ]
        elif isinstance(parsed, dict):
            codes = (
                parsed.get('PositiveTargeting', {}).get('CountryCodes')
                or parsed.get('CountryCodes')
            )
            if isinstance(codes, list):
                country_list = [
                    str(c).strip() for c in codes if str(c).strip()
                ]
            else:
                country_list = []
        elif isinstance(parsed, str):
            country_list = [
                c.strip() for c in parsed.split(',') if c.strip()
            ]
        else:
            country_list = []
    except (json.JSONDecodeError, TypeError):
        country_list = [
            c.strip() for c in raw_doc.split(',') if c.strip()
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

        if not offer_id:
            offer_id = get_public_offer_id_for_product(
                client=client,
                product_id=product_id,
                catalog=catalog
            )

        change_set_doc = create_update_targeting_change_doc(
            offer_id=offer_id,
            country_codes=country_list
        )

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
