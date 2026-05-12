from unittest.mock import patch

from click.testing import CliRunner

from aws_mp_utils.scripts.cli import main


# -------------------------------------------------
@patch('aws_mp_utils.scripts.ami_product.get_available_dimensions')
@patch('aws_mp_utils.scripts.ami_product.get_mp_client')
def test_list_dimensions(mock_client, mock_get_available_dimensions):
    """Confirm list ami product dimensions"""
    mock_get_available_dimensions.return_value = [
        {
            "Key": "t3.medium",
            "Unit": "Hrs",
            "Types": ["Metered"]
        },
        {
            "Key": "u-3tb1.56xlarge",
            "Unit": "Hrs",
            "Types": ["Metered"]
        }
    ]

    args = [
        'ami-product', 'list-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 't3.medium' in result.output
    assert 'u-3tb1.56xlarge' in result.output

    # No dimensions found
    mock_get_available_dimensions.return_value = []
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'No dimensions were found' in result.output

    # Failure
    mock_get_available_dimensions.side_effect = Exception('Some error')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Some error' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.ami_product.start_mp_change_set')
@patch('aws_mp_utils.scripts.ami_product.get_mp_client')
def test_restrict_dimensions(
    mock_client,
    mock_start_change_set
):
    """Confirm restrict ami product dimensions"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'ami-product', 'restrict-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--details-document', '{"Restrictions": ["t2.micro", "t2.small"]}',
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Failure to start changeset
    mock_start_change_set.side_effect = Exception('Invalid change set!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Invalid change set!' in result.output

    # Simulate failure in boto3 (outer exception block)
    mock_client.side_effect = Exception('403: Auth failure!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert '403: Auth failure!' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.ami_product.start_mp_change_set')
@patch('aws_mp_utils.scripts.ami_product.get_mp_client')
def test_add_dimensions(
    mock_client,
    mock_start_change_set
):
    """Confirm add ami product dimensions"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'ami-product', 'add-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--details-document', '[{"Key": "t2.micro", "Name": "t2.micro"}]',
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Failure to start changeset
    mock_start_change_set.side_effect = Exception('Invalid change set!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Invalid change set!' in result.output

    # Simulate failure in boto3 (outer exception block)
    mock_client.side_effect = Exception('403: Auth failure!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert '403: Auth failure!' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.ami_product.start_mp_change_set')
@patch('aws_mp_utils.scripts.ami_product.get_mp_client')
def test_restrict_dimensions_with_file(
    mock_client,
    mock_start_change_set,
    tmp_path
):
    """Confirm restrict ami product dimensions with a file"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    doc_file = tmp_path / "details.json"
    doc_file.write_text('{"Restrictions": ["t2.micro", "t2.small"]}')

    args = [
        'ami-product', 'restrict-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--details-document', str(doc_file),
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.ami_product.start_mp_change_set')
@patch('aws_mp_utils.scripts.ami_product.get_mp_client')
def test_add_dimensions_with_file(
    mock_client,
    mock_start_change_set,
    tmp_path
):
    """Confirm add ami product dimensions with a file"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    doc_file = tmp_path / "details.json"
    doc_file.write_text('[{"Key": "t2.micro", "Name": "t2.micro"}]')

    args = [
        'ami-product', 'add-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--details-document', str(doc_file),
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output


def test_dimensions_usage_error(tmp_path):
    """Confirm ami product dimensions usage error"""
    args = [
        'ami-product', 'restrict-dimensions',
        '--product-id', '123456789'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Missing option '--details-document'" in result.output

    args = [
        'ami-product', 'restrict-dimensions',
        '--product-id', '123456789',
        '--details-document', 'invalid_json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output

    invalid_file = tmp_path / 'invalid.json'
    invalid_file.write_text('invalid_json')
    args = [
        'ami-product', 'restrict-dimensions',
        '--product-id', '123456789',
        '--details-document', str(invalid_file)
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output

    args = [
        'ami-product', 'add-dimensions',
        '--product-id', '123456789'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Missing option '--details-document'" in result.output

    args = [
        'ami-product', 'add-dimensions',
        '--product-id', '123456789',
        '--details-document', 'invalid_json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output

    args = [
        'ami-product', 'add-dimensions',
        '--product-id', '123456789',
        '--details-document', str(invalid_file)
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.ami_product.get_available_instance_types')
@patch('aws_mp_utils.scripts.ami_product.get_mp_client')
def test_list_available_instance_types(
    mock_client,
    mock_get_available_instance_types
):
    """Confirm list available instance types"""
    mock_get_available_instance_types.return_value = [
        "t3.medium",
        "u-3tb1.56xlarge"
    ]

    args = [
        'ami-product', 'list-available-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 't3.medium' in result.output
    assert 'u-3tb1.56xlarge' in result.output

    # No available instance types found
    mock_get_available_instance_types.return_value = []
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'No available instance types were found' in result.output

    # Failure
    mock_get_available_instance_types.side_effect = Exception('Some error')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Some error' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.ami_product.start_mp_change_set')
@patch('aws_mp_utils.scripts.ami_product.get_mp_client')
def test_restrict_instance_types(
    mock_client,
    mock_start_change_set
):
    """Confirm restrict offer instance types"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'ami-product', 'restrict-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--instance-types', 't2.micro,t2.small',
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Failure to start changeset
    mock_start_change_set.side_effect = Exception('Invalid change set!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Invalid change set!' in result.output

    # Simulate failure in boto3 (outer exception block)
    mock_client.side_effect = Exception('403: Auth failure!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert '403: Auth failure!' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.ami_product.start_mp_change_set')
@patch('aws_mp_utils.scripts.ami_product.get_mp_client')
def test_add_instance_types(
    mock_client,
    mock_start_change_set
):
    """Confirm add offer instance types"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'ami-product', 'add-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--instance-types', 't2.micro,t2.small',
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Failure to start changeset
    mock_start_change_set.side_effect = Exception('Invalid change set!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Invalid change set!' in result.output

    # Simulate failure in boto3 (outer exception block)
    mock_client.side_effect = Exception('403: Auth failure!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert '403: Auth failure!' in result.output


def test_instance_types_usage_error():
    """Confirm offer instance types usage error"""
    args = [
        'ami-product', 'restrict-instance-types',
        '--product-id', '123456789'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert " Missing option '--instance-types'" in result.output

    args = [
        'ami-product', 'add-instance-types',
        '--product-id', '123456789', '--instance-types',
        '["t2.micro", "t2.small"]'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert 'The "--instance-types" expected format is a string containing' \
        in result.output

    args = [
        'ami-product', 'restrict-instance-types',
        '--product-id', '123456789', '--instance-types',
        '["t2.micro", "t2.small"]'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert 'The "--instance-types" expected format is a string containing' \
        in result.output
