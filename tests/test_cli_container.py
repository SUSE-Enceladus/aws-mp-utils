from unittest.mock import patch

from click.testing import CliRunner

from aws_mp_utils.scripts.cli import main


# -------------------------------------------------
@patch('aws_mp_utils.scripts.container.start_mp_change_set')
@patch('aws_mp_utils.scripts.container.get_mp_client')
def test_add_helm_version(
    mock_client,
    mock_start_change_set
):
    """Confirm add helm version"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'container', 'add-version',
        '--config-file', 'tests/data/config.yaml',
        '--add-override-parameters',
        '--namespace', 'test',
        '--release-name', 'Helm Product 1.2.3',
        '--marketplace-service-account-name', 'account1',
        '--quick-launch-enabled',
        '--usage-instructions', 'Easy to use AMI',
        '--helm-chart-description', 'A Helm description',
        '--helm-chart-uri', 'https://path.to.chart',
        '--container-image', 'image1',
        '--container-image', 'image2',
        '--compatible-service', 'EKS',
        '--compatible-service', 'ECS',
        '--delivery-option-title', 'Helm Product 1.2.3',
        '--release-notes', 'My release notes',
        '--version-title', 'My new title!',
        '--entity-id', '00000000-0000-4000-8000-000000000001',
        '--max-rechecks', 10,
        '--conflict-wait-period', 300,
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(
        main,
        args,
        input='y\n'
              'override.example.key\n'
              'value1\n'
              'key label\n'
              'key description\n'
              'y\n'
              'n\n'
    )
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Failure to start changeset
    mock_start_change_set.side_effect = Exception('Invalid change set!')
    result = runner.invoke(
        main,
        args,
        input='y\n'
              'override.example.key\n'
              'value1\n'
              'key label\n'
              'key description\n'
              'y\n'
              'n\n'
    )
    assert result.exit_code == 1
    assert 'Invalid change set!' in result.output


# -------------------------------------------------
@patch('aws_mp_utils.scripts.container.start_mp_change_set')
@patch('aws_mp_utils.scripts.container.get_mp_client')
def test_update_helm_version(
    mock_client,
    mock_start_change_set
):
    """Confirm update helm version"""
    mock_start_change_set.return_value = {
        'ChangeSetId': '123456789'
    }

    args = [
        'container', 'update-version',
        '--config-file', 'tests/data/config.yaml',
        '--add-override-parameters',
        '--delivery-option-id', '123456789',
        '--namespace', 'test',
        '--release-name', 'Helm Product 1.2.3',
        '--marketplace-service-account-name', 'account1',
        '--quick-launch-enabled',
        '--usage-instructions', 'Easy to use AMI',
        '--helm-chart-description', 'A Helm description',
        '--helm-chart-uri', 'https://path.to.chart',
        '--container-image', 'image1',
        '--container-image', 'image2',
        '--compatible-service', 'EKS',
        '--compatible-service', 'ECS',
        '--delivery-option-title', 'Helm Product 1.2.3',
        '--release-notes', 'My release notes',
        '--version-title', 'My new title!',
        '--entity-id', '00000000-0000-4000-8000-000000000001',
        '--max-rechecks', 10,
        '--conflict-wait-period', 300,
        '--no-color'
    ]

    runner = CliRunner()
    result = runner.invoke(
        main,
        args,
        input='y\n'
              'override.example.key\n'
              'value1\n'
              'key label\n'
              'key description\n'
              'y\n'
              'n\n'
    )
    assert result.exit_code == 0
    assert 'Change set Id: 123456789' in result.output

    # Failure to start changeset
    mock_start_change_set.side_effect = Exception('Invalid change set!')
    result = runner.invoke(
        main,
        args,
        input='y\n'
              'override.example.key\n'
              'value1\n'
              'key label\n'
              'key description\n'
              'y\n'
              'n\n'
    )
    assert result.exit_code == 1
    assert 'Invalid change set!' in result.output
