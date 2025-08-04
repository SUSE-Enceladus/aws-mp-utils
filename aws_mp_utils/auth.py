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

import boto3

from aws_mp_utils.exceptions import AWSMPUtilsException


def get_session(
    access_key_id: str = None,
    secret_access_key: str = None,
    profile_name: str = None
) -> boto3.Session:
    """
    Return session using the given credentials and region.
    """
    kwargs = {}

    if access_key_id and secret_access_key:
        kwargs['access_key_id'] = access_key_id
        kwargs['secret_access_key'] = secret_access_key
    elif profile_name:
        kwargs['profile_name'] = profile_name
    else:
        raise AWSMPUtilsException(
            'Either access_key_id and secret_access_key or profile_name are '
            'required to create a boto3 session.'
        )

    return boto3.Session(**kwargs)


def get_client(
    service_name: str,
    region_name: str,
    session: boto3.Session
) -> boto3.client:
    """
    Return client for the given session and service.
    """
    return session.client(
        service_name=service_name,
        region_name=region_name
    )
