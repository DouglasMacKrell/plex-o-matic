"""Tests for the name utilities."""
import pytest
from pathlib import Path
from plexomatic.utils.name_utils import (
    sanitize_filename,
    extract_show_info,
    generate_tv_filename,
    generate_movie_filename,
    get_preview_rename
)

def test_sanitize_filename():
    """Test that sanitize_filename properly handles invalid characters."""
    # Test with invalid characters
    assert sanitize_filename('test<>:"/\\|?*test') == 'test_________test'
    
    # Test with valid characters
    assert sanitize_filename('test123.mp4') == 'test123.mp4'

def test_extract_show_info_tv_show():
    """Test extracting information from TV show filenames."""
    # Standard TV show format
    info = extract_show_info('The.Show.S01E02.Episode.Title.mp4')
    assert info['show_name'] == 'The Show'
    assert info['season'] == '01'
    assert info['episode'] == '02'
    assert 'Title' in info['title']
    
    # Different separator format
    info = extract_show_info('The_Show_S01E02_Episode_Title.mp4')
    assert info['show_name'] == 'The Show'
    assert info['season'] == '01'
    assert info['episode'] == '02'
    
    # Multi-episode format
    info = extract_show_info('The.Show.S01E02E03.Episode.Title.mp4')
    assert info['show_name'] == 'The Show'
    assert info['season'] == '01'
    assert info['episode'] == '02'

def test_extract_show_info_movie():
    """Test extracting information from movie filenames."""
    # Standard movie format
    info = extract_show_info('The.Movie.2020.mp4')
    assert info['movie_name'] == 'The Movie'
    assert info['year'] == '2020'
    
    # With additional info
    info = extract_show_info('The.Movie.2020.1080p.mp4')
    assert info['movie_name'] == 'The Movie'
    assert info['year'] == '2020'
    assert 'info' in info

def test_extract_show_info_unrecognized():
    """Test extracting information from unrecognized filenames."""
    # Unrecognized format
    info = extract_show_info('random_file.mp4')
    assert info['name'] == 'random_file'
    assert info['show_name'] is None
    assert info['movie_name'] is None

def test_generate_tv_filename():
    """Test generating standardized TV show filenames."""
    # Basic test
    filename = generate_tv_filename("The Show", 1, 2, extension='.mp4')
    assert filename == "The.Show.S01E02.mp4"
    
    # With title
    filename = generate_tv_filename("The Show", 1, 2, "Episode Title", '.mp4')
    assert filename == "The.Show.S01E02.Episode.Title.mp4"
    
    # With spaces in name
    filename = generate_tv_filename("The Amazing Show", 1, 2, extension='.mkv')
    assert filename == "The.Amazing.Show.S01E02.mkv"
    
    # With invalid characters
    filename = generate_tv_filename("The Show: Part 2", 1, 2, extension='.mp4')
    assert filename == "The.Show_.Part.2.S01E02.mp4"

def test_generate_movie_filename():
    """Test generating standardized movie filenames."""
    # Basic test
    filename = generate_movie_filename("The Movie", 2020, extension='.mp4')
    assert filename == "The.Movie.2020.mp4"
    
    # With spaces in name
    filename = generate_movie_filename("The Amazing Movie", 2020, extension='.mkv')
    assert filename == "The.Amazing.Movie.2020.mkv"
    
    # With invalid characters
    filename = generate_movie_filename("The Movie: Part 2", 2020, extension='.mp4')
    assert filename == "The.Movie_.Part.2.2020.mp4"

def test_get_preview_rename():
    """Test generating preview renames."""
    # TV show that needs renaming
    original = Path("/tmp/The Show S1E2 Episode.mp4")
    original_path, new_path = get_preview_rename(original)
    assert original_path == original
    assert new_path is not None
    assert new_path.name == "The.Show.S01E02.Episode.mp4"
    
    # Movie that needs renaming
    original = Path("/tmp/The Movie 2020 1080p.mp4")
    original_path, new_path = get_preview_rename(original)
    assert original_path == original
    assert new_path is not None
    assert new_path.name == "The.Movie.2020.mp4"
    
    # File that doesn't need renaming
    original = Path("/tmp/The.Show.S01E02.mp4")
    original_path, new_path = get_preview_rename(original)
    assert original_path == original
    assert new_path is None
    
    # Unrecognized file
    original = Path("/tmp/random_file.mp4")
    original_path, new_path = get_preview_rename(original)
    assert original_path == original
    assert new_path is None 