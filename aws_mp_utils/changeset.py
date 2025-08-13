# -*- coding: utf-8 -*-

"""aws-mp-utils AWS Marketplace Catalog utilities."""

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

import re
import time

import boto3
import botocore.exceptions as boto_exceptions

from aws_mp_utils.exceptions import AWSMPUtilsException


def get_change_set(client: boto3.client, change_set_id: str) -> dict:
    """
    Returns a dictionary containing changeset information
    The changeset is found based on the id.
    """
    response = client.describe_change_set(
        Catalog='AWSMarketplace',
        ChangeSetId=change_set_id
    )
    return response


def get_change_set_status(
    client: boto3.client,
    change_set_id: str
) -> str:
    """Gets the status of the changeset"""
    response = get_change_set(
        client,
        change_set_id
    )
    if response and 'Status' in response:
        # 'Status':'PREPARING'|'APPLYING'|'SUCCEEDED'|'CANCELLED'|'FAILED'
        status = response['Status'].lower()
        return status


def start_mp_change_set(
    client: boto3.client,
    change_set: list,
    max_rechecks: int = 10,
    conflict_wait_period: int = 1800
) -> dict:
    """
    Additional params included in this function:
    - max_rechecks is the maximum number of checks that are
    performed when a marketplace change cannot be applied because some resource
    is affected by some other ongoing change (and ResourceInUseException is
    raised by boto3).
    - conflict_wait_period is the period (in seconds) that is waited
    between checks for the ongoing mp change to be finished (defaults to 900s).
    """
    retries = 3
    while retries > 0:
        conflicting_changeset = False
        conflicting_error_message = ''
        try:
            response = client.start_change_set(
                Catalog='AWSMarketplace',
                ChangeSet=change_set,
            )
            return response

        except boto_exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'ResourceInUseException':
                # Conflicting changeset for some resource
                conflicting_changeset = True
                conflicting_error_message = str(error)
            else:
                raise

        if conflicting_changeset:
            conflicting_changeset = False
            time.sleep(conflict_wait_period)
            max_rechecks -= 1
            if max_rechecks <= 0:
                try:
                    ongoing_change_id = get_ongoing_change_id_from_error(
                        conflicting_error_message
                    )
                    raise AWSMPUtilsException(
                        'Unable to complete successfully the mp change.'
                        f' Timed out waiting for {ongoing_change_id}'
                        ' to finish.'
                    )
                except Exception:
                    raise
        else:
            retries -= 1

    raise AWSMPUtilsException(
        'Unable to complete successfully the mp change.'
    )


def get_ongoing_change_id_from_error(message: str) -> str:
    re_change_id = r'change sets: (\w{25})'
    match = re.search(re_change_id, message)

    if match:
        change_id = match.group(1)
        return change_id
    else:
        raise AWSMPUtilsException(
            f'Unable to extract changeset id from aws err response: {message}'
        )
