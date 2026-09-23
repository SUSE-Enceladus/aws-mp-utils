# -*- coding: utf-8 -*-

"""AWS marketplace catalog change set utils cli module."""

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
# along with this program.  If not, see .

import json
import logging
import sys

import click

from aws_mp_utils.changeset import (
    get_change_set,
    get_change_set_status,
    start_mp_change_set
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
# Change Set commands function
@click.group(name="change-set")
def change_set():
    """
    Commands for marketplace catalog change set management.
    """


# -----------------------------------------------------------------------------
# Change Set describe command
@change_set.command(name='describe')
@click.option(
    '--change-set-id',
    type=click.STRING,
    required=True,
    help='The unique identifier for the change set that you want to describe.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@add_options(shared_options)
@click.pass_context
def describe(
    context,
    catalog,
    change_set_id,
    **kwargs
):
    """
    Returns a json dictionary with info about the given changeset.
    """
    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)

    client = get_mp_client(
        config_data.profile,
        config_data.region
    )

    with handle_errors(config_data.log_level, config_data.no_color):
        cs_info = get_change_set(client, change_set_id, catalog)

    echo_style(json.dumps(cs_info), config_data.no_color, fg='green')


# -----------------------------------------------------------------------------
# Change Set status command
@change_set.command(name='status')
@click.option(
    '--change-set-id',
    type=click.STRING,
    required=True,
    help='The unique identifier for the change set that you want to describe.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@add_options(shared_options)
@click.pass_context
def status(
    context,
    catalog,
    change_set_id,
    **kwargs
):
    """
    Returns a string value of the given change set status.

    Possible status values are:
        'PREPARING'|'APPLYING'|'SUCCEEDED'|'CANCELLED'|'FAILED'
    """
    process_shared_options(context.obj, kwargs)
    config_data = get_config(context.obj)
    logger = logging.getLogger('aws_mp_utils')
    logger.setLevel(config_data.log_level)

    client = get_mp_client(
        config_data.profile,
        config_data.region
    )

    with handle_errors(config_data.log_level, config_data.no_color):
        cs_status = get_change_set_status(client, change_set_id, catalog)

    if cs_status in ('preparing', 'applying'):
        color = 'yellow'
    elif cs_status in ('cancelled', 'failed'):
        color = 'red'
    else:
        color = 'green'

    echo_style(cs_status, config_data.no_color, fg=color)


# -----------------------------------------------------------------------------
# Change Set merge command
@change_set.command(name='merge')
@click.option(
    '-f', '--file', 'files',
    type=click.Path(exists=True),
    multiple=True,
    required=True,
    help='Paths to JSON files containing change set actions to merge.'
)
@click.option(
    '--output-file',
    '-o',
    type=click.Path(),
    default=None,
    help='Path to a file where the merged JSON output will be saved.'
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
    '--access-role-arn',
    type=click.STRING,
    default=None,
    help='The role used by AWS Marketplace to access the provided AMI.'
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
    help='The product entity type when adding dimensions or delivery options.'
)
@click.option(
    '--pricing-model',
    type=click.Choice(['Contract', 'Usage', 'Byol', 'Free']),
    default='Usage',
    help='The pricing model when updating pricing terms.'
)
@add_options(shared_options)
@click.pass_context
def merge(
    context,
    output_file,
    files,
    pricing_model,
    entity_type,
    access_role_arn,
    offer_id,
    product_id,
    **kwargs
):
    """
    Merges multiple change set JSON files into a single JSON array file.
    """
    if offer_id and product_id:
        raise click.BadParameter(
            "Both '--product-id' and '--offer-id' cannot be provided at the same time."
        )
    try:
        process_shared_options(context.obj, kwargs)
        config_data = get_config(context.obj)
        logger = logging.getLogger('aws_mp_utils')
        logger.setLevel(config_data.log_level)

        combined_raw = []
        for file_path in files:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    combined_raw.extend(data)
                elif isinstance(data, dict):
                    combined_raw.append(data)
                else:
                    raise click.BadParameter(
                        f"Invalid JSON format in file {file_path}."
                    )

        change_set_list = []
        dimensions = []
        terms = []
        instance_types = []

        for item in combined_raw:
            if isinstance(item, str):
                if item.strip():
                    instance_types.append(item.strip())
            elif isinstance(item, dict):
                if 'ChangeType' in item:
                    change_set_list.append(item)
                elif item.get('Type', '').endswith('Term'):
                    terms.append(item)
                elif 'InstanceTypes' in item:
                    types = item['InstanceTypes']
                    if isinstance(types, list):
                        instance_types.extend(
                            [str(t).strip() for t in types if str(t).strip()]
                        )
                elif 'Sources' in item and 'DeliveryOptions' in item:
                    if not access_role_arn:
                        raise click.BadParameter(
                            "Parameter '--access-role-arn' is required when "
                            "merging version details."
                        )
                    sources = item.get('Sources', [])
                    source = sources[0] if sources else {}
                    os_info = source.get('OperatingSystem', {})
                    ami_id = source.get('Image', '')
                    os_name = os_info.get('Name', '')
                    os_version = os_info.get('Version', '')
                    ssh_user = os_info.get('Username', 'ec2-user')

                    del_opts = item.get('DeliveryOptions', [])
                    del_opt = del_opts[0] if del_opts else {}
                    instructions = del_opt.get('Instructions', {})
                    usage_instructions = instructions.get('Usage', '')
                    recs = del_opt.get('Recommendations', {})
                    rec_instance_type = recs.get('InstanceType', '')
                    sec_groups_raw = recs.get('SecurityGroups', [])

                    sec_groups = []
                    for sg in sec_groups_raw:
                        ip_ranges = (
                            sg.get('IpRanges') or
                            sg.get('CidrIps') or
                            ['0.0.0.0/0']
                        )
                        sec_groups.append({
                            'FromPort': sg.get('FromPort', 22),
                            'ToPort': sg.get('ToPort', 22),
                            'IpProtocol': (
                                sg.get('Protocol') or
                                sg.get('IpProtocol') or
                                'tcp'
                            ),
                            'IpRanges': ip_ranges
                        })

                    if not sec_groups:
                        sec_groups = [{
                            'FromPort': 22,
                            'ToPort': 22,
                            'IpProtocol': 'tcp',
                            'IpRanges': ['0.0.0.0/0']
                        }]

                    add_del_opt_action = {
                        'ChangeType': 'AddDeliveryOptions',
                        'Entity': {
                            'Type': entity_type,
                            'Identifier': product_id or ''
                        },
                        'DetailsDocument': {
                            'Version': {
                                'VersionTitle': item.get('VersionTitle', ''),
                                'ReleaseNotes': item.get('ReleaseNotes', '')
                            },
                            'DeliveryOptions': [{
                                'Details': {
                                    'AmiDeliveryOptionDetails': {
                                        'UsageInstructions': (
                                            usage_instructions
                                        ),
                                        'RecommendedInstanceType': (
                                            rec_instance_type
                                        ),
                                        'AmiSource': {
                                            'AmiId': ami_id,
                                            'AccessRoleArn': access_role_arn,
                                            'UserName': ssh_user,
                                            'OperatingSystemName': os_name,
                                            'OperatingSystemVersion': (
                                                os_version
                                            )
                                        },
                                        'SecurityGroups': sec_groups
                                    }
                                }
                            }]
                        }
                    }
                    change_set_list.append(add_del_opt_action)
                elif 'Key' in item or 'Name' in item or 'Unit' in item:
                    dimensions.append(item)

        if instance_types:
            change_set_list.append({
                'ChangeType': 'AddInstanceTypes',
                'Entity': {
                    'Type': entity_type,
                    'Identifier': product_id or ''
                },
                'DetailsDocument': {
                    'InstanceTypes': instance_types
                }
            })

        if dimensions:
            change_set_list.append({
                'ChangeType': 'AddDimensions',
                'Entity': {
                    'Type': entity_type,
                    'Identifier': product_id or ''
                },
                'DetailsDocument': dimensions
            })

        if terms:
            change_set_list.append({
                'ChangeType': 'UpdatePricingTerms',
                'Entity': {
                    'Type': 'Offer@1.0',
                    'Identifier': offer_id or ''
                },
                'DetailsDocument': {
                    'PricingModel': pricing_model,
                    'Terms': terms
                }
            })

        for action in change_set_list:
            if not isinstance(action, dict):
                continue
            entity = action.setdefault('Entity', {})
            entity_type_action = entity.get('Type', '')

            if 'Offer' in entity_type_action:
                if offer_id and not entity.get('Identifier'):
                    entity['Identifier'] = offer_id
            else:
                if product_id and not entity.get('Identifier'):
                    entity['Identifier'] = product_id

        json_output = json.dumps(change_set_list, indent=4)
        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_output)
            output = f"Merged change set written to {output_file}"
            echo_style(output, config_data.no_color, fg='green')
        else:
            echo_style(json_output, config_data.no_color, fg='green')
    except Exception as e:
        output = str(e)
        no_color = kwargs.get('no_color', False)
        echo_style(output, no_color, fg='red')
        sys.exit(1)


# -----------------------------------------------------------------------------
# Change Set submit command
@change_set.command(name='submit')
@click.option(
    '--max-rechecks',
    type=click.IntRange(min=0),
    help='The maximum number of checks that are performed when a marketplace '
         'change cannot be applied because some resource is affected by '
         'some other ongoing change.'
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
    '--access-role-arn',
    type=click.STRING,
    default=None,
    help='The role used by AWS Marketplace to access the provided AMI.'
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
    help='The product entity type when adding dimensions or delivery options.'
)
@click.option(
    '--pricing-model',
    type=click.Choice(['Contract', 'Usage', 'Byol', 'Free']),
    default='Usage',
    help='The pricing model when updating pricing terms.'
)
@click.option(
    '--catalog',
    type=click.Choice(['AWSMarketplace', 'AWSMarketplace-aws-eusc']),
    default='AWSMarketplace',
    help='The catalog related to the request.'
)
@click.option(
    '--change-set',
    '--details-document',
    'change_set_doc',
    type=click.STRING,
    default=None,
    help='A JSON formatted string containing the change set actions.'
)
@click.option(
    '--change-set-file',
    '--details-document-file',
    '-f',
    'change_set_file',
    type=click.STRING,
    default=None,
    help='A path to a file containing a JSON formatted string with the '
         'change set actions.'
)
@add_options(shared_options)
@click.pass_context
def submit(
    context,
    change_set_file,
    change_set_doc,
    catalog,
    pricing_model,
    entity_type,
    access_role_arn,
    offer_id,
    product_id,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Submits a change set to the AWS Marketplace Catalog API.
    """
    if offer_id and product_id:
        raise click.BadParameter(
            "Both '--product-id' and '--offer-id' cannot be provided at the same time."
        )
    if change_set_doc is not None:
        try:
            raw_data = json.loads(change_set_doc)
        except json.JSONDecodeError as e:
            raise click.BadParameter(
                f"Invalid JSON provided for --change-set: {e}"
            )
    elif change_set_file is not None:
        try:
            with open(change_set_file, 'r') as f:
                content = f.read()
                raw_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise click.BadParameter(
                f"Invalid JSON provided in file {change_set_file}: {e}"
            )
        except FileNotFoundError as e:
            raise click.BadParameter(
                f"File --change-set-file not found: {e}"
            )
    else:
        raise click.BadParameter(
            "One of ['--change-set-file', "
            "'--change-set'] parameters is required to submit "
            "a change set."
        )

    if isinstance(raw_data, dict):
        raw_list = [raw_data]
    elif isinstance(raw_data, list):
        raw_list = raw_data
    else:
        raise click.BadParameter(
            "Change set payload must be a JSON object or a list of "
            "objects."
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

        change_set_list = []
        dimensions = []
        terms = []
        instance_types = []

        for item in raw_list:
            if isinstance(item, str):
                if item.strip():
                    instance_types.append(item.strip())
            elif isinstance(item, dict):
                if 'ChangeType' in item:
                    change_set_list.append(item)
                elif item.get('Type', '').endswith('Term'):
                    terms.append(item)
                elif 'InstanceTypes' in item:
                    types = item['InstanceTypes']
                    if isinstance(types, list):
                        instance_types.extend(
                            [str(t).strip() for t in types if str(t).strip()]
                        )
                elif 'Sources' in item and 'DeliveryOptions' in item:
                    if not access_role_arn:
                        raise click.BadParameter(
                            "Parameter '--access-role-arn' is required when "
                            "submitting version details."
                        )
                    sources = item.get('Sources', [])
                    source = sources[0] if sources else {}
                    os_info = source.get('OperatingSystem', {})
                    ami_id = source.get('Image', '')
                    os_name = os_info.get('Name', '')
                    os_version = os_info.get('Version', '')
                    ssh_user = os_info.get('Username', 'ec2-user')

                    del_opts = item.get('DeliveryOptions', [])
                    del_opt = del_opts[0] if del_opts else {}
                    instructions = del_opt.get('Instructions', {})
                    usage_instructions = instructions.get('Usage', '')
                    recs = del_opt.get('Recommendations', {})
                    rec_instance_type = recs.get('InstanceType', '')
                    sec_groups_raw = recs.get('SecurityGroups', [])

                    sec_groups = []
                    for sg in sec_groups_raw:
                        ip_ranges = (
                            sg.get('IpRanges') or
                            sg.get('CidrIps') or
                            ['0.0.0.0/0']
                        )
                        sec_groups.append({
                            'FromPort': sg.get('FromPort', 22),
                            'ToPort': sg.get('ToPort', 22),
                            'IpProtocol': (
                                sg.get('Protocol') or
                                sg.get('IpProtocol') or
                                'tcp'
                            ),
                            'IpRanges': ip_ranges
                        })

                    if not sec_groups:
                        sec_groups = [{
                            'FromPort': 22,
                            'ToPort': 22,
                            'IpProtocol': 'tcp',
                            'IpRanges': ['0.0.0.0/0']
                        }]

                    add_del_opt_action = {
                        'ChangeType': 'AddDeliveryOptions',
                        'Entity': {
                            'Type': entity_type,
                            'Identifier': product_id or ''
                        },
                        'DetailsDocument': {
                            'Version': {
                                'VersionTitle': item.get('VersionTitle', ''),
                                'ReleaseNotes': item.get('ReleaseNotes', '')
                            },
                            'DeliveryOptions': [{
                                'Details': {
                                    'AmiDeliveryOptionDetails': {
                                        'UsageInstructions': (
                                            usage_instructions
                                        ),
                                        'RecommendedInstanceType': (
                                            rec_instance_type
                                        ),
                                        'AmiSource': {
                                            'AmiId': ami_id,
                                            'AccessRoleArn': access_role_arn,
                                            'UserName': ssh_user,
                                            'OperatingSystemName': os_name,
                                            'OperatingSystemVersion': (
                                                os_version
                                            )
                                        },
                                        'SecurityGroups': sec_groups
                                    }
                                }
                            }]
                        }
                    }
                    change_set_list.append(add_del_opt_action)
                elif 'Key' in item or 'Name' in item or 'Unit' in item:
                    dimensions.append(item)

        if instance_types:
            change_set_list.append({
                'ChangeType': 'AddInstanceTypes',
                'Entity': {
                    'Type': entity_type,
                    'Identifier': product_id or ''
                },
                'DetailsDocument': {
                    'InstanceTypes': instance_types
                }
            })

        if dimensions:
            change_set_list.append({
                'ChangeType': 'AddDimensions',
                'Entity': {
                    'Type': entity_type,
                    'Identifier': product_id or ''
                },
                'DetailsDocument': dimensions
            })

        if terms:
            change_set_list.append({
                'ChangeType': 'UpdatePricingTerms',
                'Entity': {
                    'Type': 'Offer@1.0',
                    'Identifier': offer_id or ''
                },
                'DetailsDocument': {
                    'PricingModel': pricing_model,
                    'Terms': terms
                }
            })

        resolved_offer_id = offer_id
        for action in change_set_list:
            if not isinstance(action, dict):
                continue
            entity = action.setdefault('Entity', {})
            entity_type_action = entity.get('Type', '')

            if 'Offer' in entity_type_action:
                if not resolved_offer_id and product_id:
                    resolved_offer_id = get_public_offer_id_for_product(
                        client=client,
                        product_id=product_id,
                        catalog=catalog
                    )
                if resolved_offer_id:
                    entity['Identifier'] = resolved_offer_id
            else:
                if product_id and not entity.get('Identifier'):
                    entity['Identifier'] = product_id

            if not entity.get('Identifier'):
                raise click.BadParameter(
                    "One of ['--product-id', '--offer-id'] parameters "
                    "is required."
                )

        options = {
            'client': client,
            'change_set': change_set_list,
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
