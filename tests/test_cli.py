import pytest
from click.testing import CliRunner
from plexomatic.cli import cli, scan_command, preview_command, apply_command, rollback_command

@pytest.fixture
def runner():
    """Fixture that creates a CLI runner for testing commands."""
    return CliRunner()

def test_cli_entrypoint(runner):
    """Test that the CLI entrypoint runs without error."""
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Plex-o-matic: Media file organization tool for Plex' in result.output

def test_scan_command(runner, tmp_path):
    """Test that the scan command runs without error."""
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    
    # Create a test media file
    test_file = media_dir / "test_show.S01E01.mp4"
    test_file.write_text("dummy content")
    
    result = runner.invoke(cli, ['scan', '--path', str(media_dir)])
    assert result.exit_code == 0
    assert 'Scanning directory' in result.output
    assert str(media_dir) in result.output
    assert 'Found 1 media files' in result.output

def test_preview_command(runner):
    """Test that the preview command runs without error."""
    result = runner.invoke(cli, ['preview'])
    assert result.exit_code == 0
    assert 'Previewing changes' in result.output

def test_apply_command(runner):
    """Test that the apply command runs without error."""
    # Use input='y\n' to confirm the prompt
    result = runner.invoke(cli, ['apply'], input='y\n')
    assert result.exit_code == 0
    assert 'Applying changes' in result.output

def test_rollback_command(runner):
    """Test that the rollback command runs without error."""
    # Use input='y\n' to confirm the prompt
    result = runner.invoke(cli, ['rollback'], input='y\n')
    assert result.exit_code == 0
    assert 'Rolling back changes' in result.output

def test_version_flag(runner):
    """Test that the version flag shows version info."""
    result = runner.invoke(cli, ['--version'])
    assert result.exit_code == 0
    assert 'plex-o-matic, version' in result.output

def test_scan_with_verbose_flag(runner, tmp_path):
    """Test that the verbose flag increases output detail."""
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    
    result = runner.invoke(cli, ['scan', '--path', str(media_dir), '--verbose'])
    assert result.exit_code == 0
    assert 'Verbose mode enabled' in result.output 