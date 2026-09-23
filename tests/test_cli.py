import json

from unittest.mock import patch, Mock

from click.testing import CliRunner

from aws_mp_utils.scripts.cli import main


def test_client_help():
    """Confirm aws mp utils --help is successful."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'The command line interface provides ' \
           'AWS Marketplace Catalog utilities' in result.output


def test_print_license():
    runner = CliRunner()
    result = runner.invoke(main, ['--license'])
    assert result.exit_code == 0
    assert result.output == 'GPLv3+\n'


# -------------------------------------------------
@patch('aws_mp_utils.scripts.change_set.get_mp_client')
def test_describe_change_set(mock_client):
    """Confirm describe change set"""
    cs_data = {
        'ChangeSetId': '12345',
        'ChangeSetArn': 'string',
        'ChangeSetName': 'string',
        'Intent': 'APPLY',
        'StartTime': '2018-02-27T13:45:22Z',
        'EndTime': '2018-02-27T13:45:22Z',
        'Status': 'SUCCEEDED',
        'ChangeSet': [
            {
                'ChangeType': 'string',
                'Entity': {
                    'Type': 'string',
                    'Identifier': 'string'
                },
                'Details': 'string',
                'DetailsDocument': {'changeset': 'details'},
                'ChangeName': 'string'
            },
        ]
    }
    client = Mock()
    client.describe_change_set.return_value = cs_data
    mock_client.return_value = client

    args = [
        'change-set', 'describe',
        '--config-file', 'tests/data/config.yaml',
        '--change-set-id', '12345',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert json.loads(result.output)['ChangeSetId'] == '12345'

    # Simulate failure in boto3
    client.describe_change_set.side_effect = Exception('403: Auth failure!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert '403: Auth failure!' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.change_set.get_mp_client')
@patch('aws_mp_utils.scripts.change_set.get_change_set_status')
def test_get_change_set_status(mock_status, mock_client):
    """Confirm get change set status"""
    mock_status.return_value = 'success'

    args = [
        'change-set', 'status',
        '--config-file', 'tests/data/config.yaml',
        '--change-set-id', '12345',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'success' in result.output

    mock_status.return_value = 'applying'
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'applying' in result.output

    mock_status.return_value = 'failed'
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'failed' in result.output

    # Simulate failure in boto3
    mock_status.side_effect = Exception('403: Auth failure!')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert '403: Auth failure!' in result.output


# -------------------------------------------------
def test_merge_change_sets(tmp_path):
    """Confirm merge change sets"""
    file1 = tmp_path / "file1.json"
    file1.write_text('{"ChangeType": "AddDimensions"}')

    file2 = tmp_path / "file2.json"
    file2.write_text('[{"ChangeType": "UpdatePricingTerms"}]')

    args = [
        'change-set', 'merge',
        '-f', str(file1),
        '-f', str(file2),
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'AddDimensions' in result.output
    assert 'UpdatePricingTerms' in result.output

    # Test output to file with instance types and pricing terms
    types_file = tmp_path / "instance_types.json"
    types_file.write_text('["t3.medium", "m5.large"]')

    prices_file = tmp_path / "prices.json"
    prices_file.write_text('[{"Type": "UsageBasedPricingTerm"}]')

    out_file = tmp_path / "combined.json"
    args_merge = [
        'change-set', 'merge',
        '-f', str(types_file),
        '-f', str(prices_file),
        '--product-id', 'prod-12345',
        '-o', str(out_file),
        '--no-color'
    ]
    result = runner.invoke(main, args_merge)
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert 'AddInstanceTypes' in content
    assert 't3.medium' in content
    assert 'UpdatePricingTerms' in content

    # Test invalid JSON format
    file_invalid = tmp_path / "invalid.json"
    file_invalid.write_text('"just a string"')
    args_invalid = [
        'change-set', 'merge',
        '-f', str(file_invalid),
        '--no-color'
    ]
    result = runner.invoke(main, args_invalid)
    assert result.exit_code == 1
    assert 'Invalid JSON format in file' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.change_set.get_public_offer_id_for_product')
@patch('aws_mp_utils.scripts.change_set.start_mp_change_set')
@patch('aws_mp_utils.scripts.change_set.get_mp_client')
def test_submit_change_set(
    mock_client,
    mock_start_change_set,
    mock_get_offer_id
):
    """Confirm submit change set"""
    mock_get_offer_id.return_value = 'offer-12345'
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    cs_json = json.dumps([
        {"ChangeType": "AddDimensions", "Entity": {"Type": "AmiProduct@1.0"}},
        {"ChangeType": "UpdatePricingTerms", "Entity": {"Type": "Offer@1.0"}}
    ])

    args = [
        'change-set', 'submit',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', 'prod-12345',
        '--change-set', cs_json,
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Failure
    mock_start_change_set.side_effect = Exception('Some error')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Some error' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.change_set.start_mp_change_set')
@patch('aws_mp_utils.scripts.change_set.get_mp_client')
def test_submit_change_set_version_details(
    mock_client,
    mock_start_change_set,
    tmp_path
):
    """Confirm submit change set with version details file"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    version_file = tmp_path / "versions.json"
    version_file.write_text(json.dumps([
        {
            "VersionTitle": "Version 1.0",
            "ReleaseNotes": "Release notes",
            "Sources": [{
                "Image": "ami-12345678",
                "OperatingSystem": {
                    "Name": "SUSE",
                    "Version": "16.0",
                    "Username": "ec2-user"
                }
            }],
            "DeliveryOptions": [{
                "Instructions": {"Usage": "Usage instructions"},
                "Recommendations": {
                    "InstanceType": "r7i.8xlarge",
                    "SecurityGroups": [{
                        "FromPort": 22,
                        "ToPort": 22,
                        "Protocol": "tcp",
                        "CidrIps": ["0.0.0.0/0"]
                    }]
                }
            }]
        }
    ]))

    args = [
        'change-set', 'submit',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', 'prod-12345',
        '--access-role-arn', 'arn:aws:iam::12345:role/Role',
        '-f', str(version_file),
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Test error when --access-role-arn is missing
    args_no_role = [
        'change-set', 'submit',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', 'prod-12345',
        '-f', str(version_file),
        '--no-color'
    ]
    result = runner.invoke(main, args_no_role)
    assert result.exit_code == 1
    assert "Parameter '--access-role-arn' is required" in result.output


def test_submit_change_set_usage_error(tmp_path):
    """Confirm change-set submit usage error"""
    args = [
        'change-set', 'submit',
        '--product-id', 'prod-12345',
        '--offer-id', 'offer-12345'
    ]
    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Both '--product-id' and '--offer-id' cannot be provided at the same time." in result.output

    args = [
        'change-set', 'submit'
    ]
    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "One of ['--change-set-file', " in result.output

    args = [
        'change-set', 'submit',
        '--change-set', 'invalid_json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --change-set:" in result.output

    invalid_file = tmp_path / 'invalid.json'
    invalid_file.write_text('invalid_json')
    args = [
        'change-set', 'submit',
        '-f', str(invalid_file)
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided in file" in result.output
