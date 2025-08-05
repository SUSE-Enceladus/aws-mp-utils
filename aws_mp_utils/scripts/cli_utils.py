import logging
import os
import sys

import click
import yaml

from collections import ChainMap, namedtuple

from aws_mp_utils.auth import get_client, get_session


default_config_file = os.path.expanduser('~/.config/aws_mp_utils/default.yaml')
default_profile = 'default'

config_defaults = {
    'config_file': default_config_file,
    'profile': default_profile,
    'log_level': logging.INFO,
    'no_color': False,
    'region': 'us-east-1'
}

aws_mp_utils_config = namedtuple(
    'aws_mp_utils_config',
    sorted(config_defaults)
)

# -----------------------------------------------------------------------------
# Shared options
shared_options = [
    click.option(
        '-C',
        '--config-file',
        type=click.Path(exists=True),
        help='AWS MP utils config file to use. Default: '
             '~/.config/aws_mp_utils/default.yaml'
    ),
    click.option(
        '--profile',
        help='The AWS profile to use.'
    ),
    click.option(
        '--no-color',
        is_flag=True,
        help='Remove ANSI color and styling from output.'
    ),
    click.option(
        '--debug',
        'log_level',
        flag_value=logging.DEBUG,
        help='Display debug level logging to console.'
    ),
    click.option(
        '--info',
        'log_level',
        flag_value=logging.INFO,
        default=True,
        help='Display logging info to console. (Default)'
    ),
    click.option(
        '--quiet',
        'log_level',
        flag_value=logging.ERROR,
        help='Display only errors to console.'
    ),
    click.option(
        '--region',
        type=click.STRING,
        help='The region to use for the image requests.'
    )
]


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options


# -------------------------------------------------
# Get Config
def get_config(cli_context):
    """
    Process Azure Image utils config.
    Use ChainMap to build config values based on
    command line args, config and defaults.
    """
    config_file_path = cli_context['config_file'] or default_config_file

    config_values = {}
    try:
        with open(config_file_path) as config_file:
            config_values = yaml.safe_load(config_file)
    except FileNotFoundError:
        echo_style(
            f'Config file: {config_file_path} not found. Using default '
            f'configuration values.',
            no_color=True
        )

    cli_values = {
        key: value for key, value in cli_context.items() if value is not None
    }
    data = ChainMap(cli_values, config_values, config_defaults)

    config_data = None
    try:
        config_data = aws_mp_utils_config(**data)
    except TypeError as e:
        echo_style(
            f'Found unknown keyword in config file {config_file_path}',
            no_color=True
        )
        echo_style(str(e), no_color=True)
        sys.exit(1)

    return config_data


# -----------------------------------------------------------------------------
# Printing options
def echo_style(message, no_color, fg='yellow'):
    """
    Echo stylized output to terminal depending on no_color.
    """
    if no_color:
        click.echo(message)
    else:
        click.secho(message, fg=fg)


# -----------------------------------------------------------------------------
# Process shared options to all commands
def process_shared_options(context_obj, kwargs):
    """
    Update context with values for shared options.
    """
    context_obj['config_file'] = kwargs.get('config_file')
    context_obj['log_level'] = kwargs.get('log_level')
    context_obj['no_color'] = kwargs.get('no_color')
    context_obj['profile'] = kwargs.get('profile')
    context_obj['region'] = kwargs.get('region')


# -----------------------------------------------------------------------------
def get_mp_client(profile, region):
    """
    Return a authenticated client given the profile and region.
    """
    session = get_session(profile_name=profile)
    return get_client(
        'marketplace-catalog',
        region,
        session
    )
