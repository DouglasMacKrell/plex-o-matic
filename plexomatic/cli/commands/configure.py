"""Command to configure API keys and application settings."""

import logging
from pathlib import Path

import click
from rich.console import Console

from plexomatic.config.config_manager import ConfigManager

@click.command()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
@click.pass_context
def configure_command(ctx: click.Context, verbose: bool) -> None:
    """Configure API keys and application settings.

    This command provides an interactive interface to set up API keys
    for TVDB, TMDB, AniDB, and configure the local LLM.
    """
    logger = logging.getLogger("plexomatic")
    console = Console()

    if verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")
        console.print("[info]Verbose mode enabled[/info]")

    console.print("Configuration: Set up API keys and application settings")

    # Load config
    config = ConfigManager()
    
    # Use existing config as a base
    config_data = config.config

    # Initialize API section if it doesn't exist
    if "api" not in config_data:
        config_data["api"] = {}

    api_config = config_data["api"]

    # TVDB API configuration
    if "tvdb" not in api_config:
        api_config["tvdb"] = {"api_key": "", "auto_retry": True, "pin": ""}

    current_tvdb_key = api_config["tvdb"].get("api_key", "")
    tvdb_key = click.prompt(
        f"Enter your TVDB API key [{current_tvdb_key}]",
        default=current_tvdb_key,
        show_default=False,
    )
    api_config["tvdb"]["api_key"] = tvdb_key

    # Add TVDB PIN configuration for v4 API
    current_tvdb_pin = api_config["tvdb"].get("pin", "")
    tvdb_pin = click.prompt(
        f"Enter your TVDB subscriber PIN (for v4 API) [{current_tvdb_pin}]",
        default=current_tvdb_pin,
        show_default=False,
    )
    api_config["tvdb"]["pin"] = tvdb_pin

    # TMDB API configuration
    if "tmdb" not in api_config:
        api_config["tmdb"] = {"api_key": ""}

    current_tmdb_key = api_config["tmdb"].get("api_key", "")
    tmdb_key = click.prompt(
        f"Enter your TMDB API key [{current_tmdb_key}]",
        default=current_tmdb_key,
        show_default=False,
    )
    api_config["tmdb"]["api_key"] = tmdb_key

    # AniDB configuration
    if "anidb" not in api_config:
        api_config["anidb"] = {
            "username": "",
            "password": "",
            "client_name": "plexomatic",
            "client_version": 1,
            "rate_limit_wait": 2.5,
        }

    configure_anidb = click.confirm("Do you want to configure AniDB credentials?", default=False)
    if configure_anidb:
        current_anidb_user = api_config["anidb"].get("username", "")
        anidb_user = click.prompt(
            f"Enter your AniDB username [{current_anidb_user}]",
            default=current_anidb_user,
            show_default=False,
        )
        api_config["anidb"]["username"] = anidb_user

        anidb_pass = click.prompt(
            "Enter your AniDB password", hide_input=True, default="", show_default=False
        )
        if anidb_pass:
            api_config["anidb"]["password"] = anidb_pass

    # TVMaze configuration (doesn't require API key)
    if "tvmaze" not in api_config:
        api_config["tvmaze"] = {"cache_size": 100}

    # LLM configuration
    if "llm" not in api_config:
        api_config["llm"] = {"model_name": "deepseek-r1:8b", "base_url": "http://localhost:11434"}

    configure_llm = click.confirm(
        "Do you want to configure local LLM settings (Ollama with Deepseek R1)?", default=True
    )
    if configure_llm:
        current_llm_url = api_config["llm"].get("base_url", "http://localhost:11434")
        llm_url = click.prompt(
            f"Enter Ollama base URL [{current_llm_url}]",
            default=current_llm_url,
            show_default=False,
        )
        api_config["llm"]["base_url"] = llm_url

        current_llm_model = api_config["llm"].get("model_name", "deepseek-r1:8b")
        llm_model = click.prompt(
            f"Enter LLM model name [{current_llm_model}]",
            default=current_llm_model,
            show_default=False,
        )
        api_config["llm"]["model_name"] = llm_model

    # Update the config with our changes
    config.config = config_data

    # Save the updated configuration
    if verbose:
        console.print("[info]Saving configuration...[/info]")
    config.save()
    console.print("[success]Configuration saved successfully.[/success]")

    # Display API connection status if verbose
    if verbose:
        console.print("\n[bold]API connection status:[/bold]")

        if api_config["tvdb"]["api_key"]:
            console.print("[success]TVDB API key is set[/success]")
            if api_config["tvdb"]["pin"]:
                console.print("[success]TVDB subscriber PIN is set[/success]")
            else:
                console.print(
                    "[warning]TVDB subscriber PIN is not set (may be required for v4 API)[/warning]"
                )
        else:
            console.print("[error]TVDB API key is not set[/error]")

        if api_config["tmdb"]["api_key"]:
            console.print("[success]TMDB API key is set[/success]")
        else:
            console.print("[error]TMDB API key is not set[/error]")

        if api_config["anidb"]["username"] and api_config["anidb"]["password"]:
            console.print("[success]AniDB credentials are set[/success]")
        else:
            console.print("[warning]AniDB credentials are not fully set[/warning]")

        console.print("[success]TVMaze API does not require authentication[/success]")

        console.print(
            f"[success]LLM configured to use {api_config['llm']['model_name']} at {api_config['llm']['base_url']}[/success]"
        ) 