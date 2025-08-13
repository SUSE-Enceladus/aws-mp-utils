# -*- coding: utf-8 -*-

"""AWS marketplace catalog container utils cli module."""

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

from aws_mp_utils.container import (
    gen_add_delivery_options_changeset,
    gen_update_delivery_options_changeset
)
from aws_mp_utils.changeset import start_mp_change_set
from aws_mp_utils.scripts.cli_utils import (
    add_options,
    get_config,
    process_shared_options,
    shared_options,
    echo_style,
    get_mp_client,
    handle_errors,
    override_parameters_repl
)


# -----------------------------------------------------------------------------
# Offer commands function
@click.group(name="container")
def container():
    """
    Commands for marketplace catalog container product management.
    """


# -----------------------------------------------------------------------------
@container.command
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
    '--add-override-parameters',
    is_flag=True,
    help='Add parameters that will be used in the Helm commands '
         'that launch the application.'
)
@click.option(
    '--namespace',
    type=click.STRING,
    help='The Kubernetes namespace where the Helm chart will be installed.'
)
@click.option(
    '--release-name',
    type=click.STRING,
    help='The name for the Helm release provided to the helm install command.',
    required=True
)
@click.option(
    '--marketplace-service-account-name',
    type=click.STRING,
    help='The name of the Kubernetes service account.',
    required=True
)
@click.option(
    '--quick-launch-enabled',
    is_flag=True,
    help='If buyers can use QuickLaunch to launch the software.'
)
@click.option(
    '--usage-instructions',
    type=click.STRING,
    help='Instructions for using the AMI, '
         'or a link to more information about the AMI.',
    required=True
)
@click.option(
    '--helm-chart-description',
    type=click.STRING,
    help='A longer description of the delivery option to give '
         'details to your buyer',
    required=True
)
@click.option(
    '--helm-chart-uri',
    type=click.STRING,
    help='The URL to the Helm chart hosted in Amazon ECR.',
    required=True
)
@click.option(
    '--container-image',
    'container_images',
    multiple=True,
    type=click.STRING,
    help='Container image URLs used by this version.',
    required=True
)
@click.option(
    '--compatible-service',
    'compatible_services',
    type=click.Choice(['ECS', 'EKS']),
    help='Services that the release is compatible with. '
         'Valid options are ECS and EKS.',
    required=True
)
@click.option(
    '--delivery-option-title',
    type=click.STRING,
    help='A short description that allows your buyer to '
         'choose between your delivery options',
    required=True
)
@click.option(
    '--release-notes',
    type=click.STRING,
    help='Notes for buyers to tell them about changes from '
         'one version to the next.',
    required=True
)
@click.option(
    '--version-title',
    type=click.STRING,
    help='The title to be displayed for the version.',
    required=True
)
@click.option(
    '--entity-id',
    type=click.STRING,
    help='The unique identifier the product in the AWS Marketplace. '
         'The expected format of the ID is a UUID.',
    required=True
)
@add_options(shared_options)
@click.pass_context
def add_version(
    context,
    entity_id,
    version_title,
    release_notes,
    delivery_option_title,
    compatible_services,
    container_images,
    helm_chart_uri,
    helm_chart_description,
    usage_instructions,
    quick_launch_enabled,
    marketplace_service_account_name,
    release_name,
    namespace,
    add_override_parameters,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Starts a change set to include the helm chart in the container product

    A new version change set is submitted with the provided arguments
    for the given entity.

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

    override_parameters = {}
    if add_override_parameters:
        override_parameters = override_parameters_repl(
            quick_launch_enabled,
            config_data.no_color
        )

    change_doc = gen_add_delivery_options_changeset(
        entity_id=entity_id,
        version_title=version_title,
        release_notes=release_notes,
        delivery_option_title=delivery_option_title,
        compatible_services=compatible_services,
        container_images=container_images,
        helm_chart_uri=helm_chart_uri,
        helm_chart_description=helm_chart_description,
        usage_instructions=usage_instructions,
        quick_launch_enabled=quick_launch_enabled,
        marketplace_service_account_name=marketplace_service_account_name,
        release_name=release_name,
        namespace=namespace,
        override_parameters=override_parameters
    )

    start_cs_options = {
        'client': client,
        'change_set': [change_doc]
    }
    if max_rechecks:
        start_cs_options['max_rechecks'] = max_rechecks

    if conflict_wait_period:
        start_cs_options['conflict_wait_period'] = conflict_wait_period

    with handle_errors(config_data.log_level, config_data.no_color):
        response = start_mp_change_set(**start_cs_options)

    output = f'Change set Id: {response["ChangeSetId"]}'
    echo_style(output, config_data.no_color, fg='green')


# -----------------------------------------------------------------------------
@container.command
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
    '--add-override-parameters',
    is_flag=True,
    help='Add parameters that will be used in the Helm commands '
         'that launch the application.'
)
@click.option(
    '--delivery-option-id',
    type=click.STRING,
    help='Unique identifier for the DeliveryOption.',
    required=True
)
@click.option(
    '--namespace',
    type=click.STRING,
    help='The Kubernetes namespace where the Helm chart will be installed.'
)
@click.option(
    '--release-name',
    type=click.STRING,
    help='The name for the Helm release provided to the helm install command.',
    required=True
)
@click.option(
    '--marketplace-service-account-name',
    type=click.STRING,
    help='The name of the Kubernetes service account.',
    required=True
)
@click.option(
    '--quick-launch-enabled',
    is_flag=True,
    help='If buyers can use QuickLaunch to launch the software.'
)
@click.option(
    '--usage-instructions',
    type=click.STRING,
    help='Instructions for using the AMI, '
         'or a link to more information about the AMI.',
    required=True
)
@click.option(
    '--helm-chart-description',
    type=click.STRING,
    help='A longer description of the delivery option to give '
         'details to your buyer',
    required=True
)
@click.option(
    '--helm-chart-uri',
    type=click.STRING,
    help='The URL to the Helm chart hosted in Amazon ECR.',
    required=True
)
@click.option(
    '--container-image',
    'container_images',
    multiple=True,
    type=click.STRING,
    help='Container image URLs used by this version.',
    required=True
)
@click.option(
    '--compatible-service',
    'compatible_services',
    multiple=True,
    type=click.Choice(['ECS', 'EKS']),
    help='Services that the release is compatible with. '
         'Valid options are ECS and EKS.',
    required=True
)
@click.option(
    '--delivery-option-title',
    type=click.STRING,
    help='A short description that allows your buyer to '
         'choose between your delivery options',
    required=True
)
@click.option(
    '--release-notes',
    type=click.STRING,
    help='Notes for buyers to tell them about changes from '
         'one version to the next.',
    required=True
)
@click.option(
    '--version-title',
    type=click.STRING,
    help='The title to be displayed for the version.',
    required=True
)
@click.option(
    '--entity-id',
    type=click.STRING,
    help='The unique identifier the product in the AWS Marketplace. '
         'The expected format of the ID is a UUID.',
    required=True
)
@add_options(shared_options)
@click.pass_context
def update_version(
    context,
    entity_id,
    version_title,
    release_notes,
    delivery_option_title,
    compatible_services,
    container_images,
    helm_chart_uri,
    helm_chart_description,
    usage_instructions,
    quick_launch_enabled,
    marketplace_service_account_name,
    release_name,
    namespace,
    delivery_option_id,
    add_override_parameters,
    conflict_wait_period,
    max_rechecks,
    **kwargs
):
    """
    Starts a change set to update the helm chart version in the product

    An update version change set is submitted with the provided arguments
    for the given entity.

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

    override_parameters = {}
    if add_override_parameters:
        override_parameters = override_parameters_repl(
            quick_launch_enabled,
            config_data.no_color
        )

    change_doc = gen_update_delivery_options_changeset(
        entity_id=entity_id,
        version_title=version_title,
        release_notes=release_notes,
        delivery_option_title=delivery_option_title,
        compatible_services=compatible_services,
        container_images=container_images,
        helm_chart_uri=helm_chart_uri,
        helm_chart_description=helm_chart_description,
        usage_instructions=usage_instructions,
        quick_launch_enabled=quick_launch_enabled,
        marketplace_service_account_name=marketplace_service_account_name,
        release_name=release_name,
        namespace=namespace,
        delivery_option_id=delivery_option_id,
        override_parameters=override_parameters
    )

    start_cs_options = {
        'client': client,
        'change_set': [change_doc]
    }
    if max_rechecks:
        start_cs_options['max_rechecks'] = max_rechecks

    if conflict_wait_period:
        start_cs_options['conflict_wait_period'] = conflict_wait_period

    with handle_errors(config_data.log_level, config_data.no_color):
        response = start_mp_change_set(**start_cs_options)

    output = f'Change set Id: {response["ChangeSetId"]}'
    echo_style(output, config_data.no_color, fg='green')
