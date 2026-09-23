from unittest.mock import patch

from click.testing import CliRunner

from aws_mp_utils.scripts.cli import main


# -------------------------------------------------
@patch('aws_mp_utils.scripts.product.get_public_offer_id_for_product')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_get_offer_id(
    mock_client,
    mock_get_offer_id
):
    """Confirm get public offer id for product"""
    mock_get_offer_id.return_value = 'offer-123456789'

    args = [
        'product', 'get-offer-id',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'offer-123456789' in result.output

    # Failure
    mock_get_offer_id.side_effect = Exception('Some error')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Some error' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.product.get_available_dimensions')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_list_dimensions(
    mock_client,
    mock_get_available_dimensions,
    tmp_path
):
    """Confirm list product dimensions"""
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
        'product', 'list-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 't3.medium' in result.output
    assert 'u-3tb1.56xlarge' in result.output

    # Test output to file
    out_file = tmp_path / "dimensions.json"
    args_file = args + ['--output-file', str(out_file)]
    result = runner.invoke(main, args_file)
    assert result.exit_code == 0
    assert out_file.exists()
    assert 't3.medium' in out_file.read_text()

    # Failure
    mock_get_available_dimensions.side_effect = Exception('Some error')
    result = runner.invoke(main, args)
    assert result.exit_code == 1
    assert 'Some error' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.product.start_mp_change_set')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_restrict_dimensions(
    mock_client,
    mock_start_change_set
):
    """Confirm restrict product dimensions"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'product', 'restrict-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--entity-type', 'SaaSProduct@1.0',
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
@patch('aws_mp_utils.scripts.product.start_mp_change_set')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_add_dimensions(
    mock_client,
    mock_start_change_set
):
    """Confirm add product dimensions"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'product', 'add-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--entity-type', 'AmiProduct@1.0',
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
@patch('aws_mp_utils.scripts.product.start_mp_change_set')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_restrict_dimensions_with_file(
    mock_client,
    mock_start_change_set,
    tmp_path
):
    """Confirm restrict product dimensions with a file"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    doc_file = tmp_path / "details.json"
    doc_file.write_text('{"Restrictions": ["t2.micro", "t2.small"]}')

    args = [
        'product', 'restrict-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--details-document-file', str(doc_file),
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.product.start_mp_change_set')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_add_dimensions_with_file(
    mock_client,
    mock_start_change_set,
    tmp_path
):
    """Confirm add product dimensions with a file"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    doc_file = tmp_path / "details.json"
    doc_file.write_text('[{"Key": "t2.micro", "Name": "t2.micro"}]')

    args = [
        'product', 'add-dimensions',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--details-document-file', str(doc_file),
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output


def test_dimensions_usage_error(tmp_path):
    """Confirm product dimensions usage error"""
    args = [
        'product', 'restrict-dimensions',
        '--product-id', '123456789'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--details-document-file', "
        "'--details-document'] parameters is required to restrict "
        "dimensions in a product."
    ) in result.output

    args = [
        'product', 'restrict-dimensions',
        '--product-id', '123456789',
        '--details-document', 'invalid_json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output

    args = [
        'product', 'restrict-dimensions',
        '--product-id', '123456789',
        '--details-document-file', 'non_existing_file.json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "File --details-document-file not found:" in result.output

    invalid_file = tmp_path / 'invalid.json'
    invalid_file.write_text('invalid_json')
    args = [
        'product', 'restrict-dimensions',
        '--product-id', '123456789',
        '--details-document-file', str(invalid_file)
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided in file --details-document-file:" \
        in result.output

    args = [
        'product', 'add-dimensions',
        '--product-id', '123456789'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--details-document-file', "
        "'--details-document'] parameters is required to add "
        "dimensions in a product."
    ) in result.output

    args = [
        'product', 'add-dimensions',
        '--product-id', '123456789',
        '--details-document', 'invalid_json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output

    args = [
        'product', 'add-dimensions',
        '--product-id', '123456789',
        '--details-document-file', 'non_existing_file.json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "File --details-document-file not found:" in result.output

    args = [
        'product', 'add-dimensions',
        '--product-id', '123456789',
        '--details-document-file', str(invalid_file)
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided in file --details-document-file:" \
        in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.product.get_available_instance_types')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_list_instance_types(
    mock_client,
    mock_get_available_instance_types,
    tmp_path
):
    """Confirm list available instance types"""
    mock_get_available_instance_types.return_value = [
        "t3.medium",
        "u-3tb1.56xlarge"
    ]

    args = [
        'product', 'list-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 't3.medium' in result.output
    assert 'u-3tb1.56xlarge' in result.output

    # Test JSON output to stdout
    args_json = args + ['--json']
    result = runner.invoke(main, args_json)
    assert result.exit_code == 0
    assert '"t3.medium"' in result.output

    # Test JSON output to file via --output-file
    out_file = tmp_path / "instance_types.json"
    args_file = args + ['--output-file', str(out_file)]
    result = runner.invoke(main, args_file)
    assert result.exit_code == 0
    assert out_file.exists()
    assert '"t3.medium"' in out_file.read_text()

    # Test JSON output to file via -o short option
    out_file_short = tmp_path / "instance_types_short.json"
    args_file_short = args + ['-o', str(out_file_short)]
    result = runner.invoke(main, args_file_short)
    assert result.exit_code == 0
    assert out_file_short.exists()
    assert '"t3.medium"' in out_file_short.read_text()

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
@patch('aws_mp_utils.scripts.product.start_mp_change_set')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_restrict_instance_types(
    mock_client,
    mock_start_change_set
):
    """Confirm restrict product instance types"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'product', 'restrict-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--instance-types', 't2.micro,t2.small',
        '--entity-type', 'AmiProduct@1.0',
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Check that AmiProduct@1.0 was passed as Entity Type
    call_kwargs = mock_start_change_set.call_args.kwargs
    cs_doc = call_kwargs['change_set'][0]
    assert cs_doc['Entity']['Type'] == 'AmiProduct@1.0'

    # Test with --details-document
    args_doc = [
        'product', 'restrict-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--details-document', '["t2.micro", "t2.small"]',
        '--no-color'
    ]
    result = runner.invoke(main, args_doc)
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
@patch('aws_mp_utils.scripts.product.start_mp_change_set')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_add_instance_types(
    mock_client,
    mock_start_change_set
):
    """Confirm add product instance types"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'product', 'add-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--instance-types', 't2.micro,t2.small',
        '--entity-type', 'AmiProduct@1.0',
        '--max-rechecks', '10',
        '--conflict-wait-period', '300',
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Check that AmiProduct@1.0 was passed as Entity Type
    call_kwargs = mock_start_change_set.call_args.kwargs
    cs_doc = call_kwargs['change_set'][0]
    assert cs_doc['Entity']['Type'] == 'AmiProduct@1.0'

    # Test with --details-document
    args_doc = [
        'product', 'add-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--details-document', '["t2.micro", "t2.small"]',
        '--no-color'
    ]
    result = runner.invoke(main, args_doc)
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
@patch('aws_mp_utils.scripts.product.start_mp_change_set')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_restrict_instance_types_with_file(
    mock_client,
    mock_start_change_set,
    tmp_path
):
    """Confirm restrict product instance types with a file"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    doc_file = tmp_path / "types.json"
    doc_file.write_text('["t2.micro", "t2.small"]')

    args = [
        'product', 'restrict-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--details-document-file', str(doc_file),
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Test with --instance-types-file
    txt_file = tmp_path / "types.txt"
    txt_file.write_text('t2.micro, t2.small')

    args_txt = [
        'product', 'restrict-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--instance-types-file', str(txt_file),
        '--no-color'
    ]
    result = runner.invoke(main, args_txt)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.product.start_mp_change_set')
@patch('aws_mp_utils.scripts.product.get_mp_client')
def test_add_instance_types_with_file(
    mock_client,
    mock_start_change_set,
    tmp_path
):
    """Confirm add product instance types with a file"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    doc_file = tmp_path / "types.json"
    doc_file.write_text('["t2.micro", "t2.small"]')

    args = [
        'product', 'add-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--details-document-file', str(doc_file),
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Test with --instance-types-file
    txt_file = tmp_path / "types.txt"
    txt_file.write_text('t2.micro, t2.small')

    args_txt = [
        'product', 'add-instance-types',
        '--config-file', 'tests/data/config.yaml',
        '--product-id', '123456789',
        '--instance-types-file', str(txt_file),
        '--no-color'
    ]
    result = runner.invoke(main, args_txt)
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output


def test_instance_types_usage_error(tmp_path):
    """Confirm product instance types usage error"""
    args = [
        'product', 'restrict-instance-types'
    ]
    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--details-document-file', "
        "'--details-document'] parameters is required to restrict "
        "instance types in a product."
    ) in result.output

    args = [
        'product', 'add-instance-types',
        '--product-id', '123456789'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert (
        "One of ['--details-document-file', "
        "'--details-document'] parameters is required to add "
        "instance types in a product."
    ) in result.output

    args = [
        'product', 'restrict-instance-types',
        '--product-id', '123456789',
        '--details-document', '{"invalid":'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "Invalid JSON provided for --details-document:" in result.output

    args = [
        'product', 'restrict-instance-types',
        '--product-id', '123456789',
        '--details-document-file', 'non_existing_file.json'
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert "File --details-document-file not found:" in result.output

    invalid_file = tmp_path / 'invalid.json'
    invalid_file.write_text('{"invalid":')
    args = [
        'product', 'restrict-instance-types',
        '--product-id', '123456789',
        '--details-document-file', str(invalid_file)
    ]
    result = runner.invoke(main, args)
    assert result.exit_code == 2
    assert ("Invalid JSON provided in file "
            "--details-document-file:") in result.output        
