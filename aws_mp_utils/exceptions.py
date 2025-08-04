# -*- coding: utf-8 -*-

"""AWS MP utils exceptions module."""

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


class AWSMPUtilsException(Exception):
    """Generic exception for the aws_mp_utils package."""


class AWSMPImageProductException(AWSMPUtilsException):
    """Exception for AWS marketplace catalog image product processes."""


class AWSMPContainerProductException(AWSMPUtilsException):
    """Exception for AWS marketplace catalog container product processes."""


class AWSMPOfferException(AWSMPUtilsException):
    """Exception for AWS marketplace catalog offer processes."""
