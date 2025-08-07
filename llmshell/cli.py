"""Command-line interface for LLMShell."""

import asyncio
from typing import Optional

import click

from .config import create_default_config, get_config_paths, load_config
from .llm import create_llm_provider, test_llm_connection


@click.group()
@click.version_option(version="0.1.0")
@click.option(
    "--config", "-c", type=click.Path(exists=True), help="Path to configuration file"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """LLMShell - AI-powered Linux shell using local LLMs."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config_path"] = config


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize LLMShell configuration."""
    click.echo("🚀 Initializing LLMShell...")

    # Find config directory
    config_paths = get_config_paths()
    default_config_path = config_paths[2]  # ~/.config/llmshell/config.yaml

    if default_config_path.exists():
        click.echo(f"Configuration already exists at: {default_config_path}")
        if not click.confirm("Overwrite existing configuration?"):
            return

    try:
        create_default_config(default_config_path)
        click.echo(f"✅ Created configuration file: {default_config_path}")
        click.echo("\nNext steps:")
        click.echo("1. Start Ollama: ollama serve")
        click.echo("2. Pull a model: ollama pull llama3")
        click.echo("3. Test connection: llmshell test")
        click.echo("4. Start using: llmshell")
    except Exception as e:
        click.echo(f"❌ Failed to create configuration: {e}", err=True)


@cli.command()
@click.pass_context
def test(ctx):
    """Test LLM connection and basic functionality."""
    click.echo("🧪 Testing LLMShell connection...")

    try:
        config = load_config()
        click.echo(f"📋 Using: {config.llm.provider} ({config.llm.model})")
        click.echo(f"🔗 URL: {config.llm.base_url}")

        async def run_test():
            provider = create_llm_provider(config.llm)

            # Test connection
            if await test_llm_connection(provider):
                click.echo("✅ LLM connection successful!")

                # Test a simple translation
                response = await provider.translate("list files")
                if response.error:
                    click.echo(f"❌ Translation test failed: {response.error}")
                else:
                    click.echo(f"✅ Translation test: '{response.command}'")
            else:
                click.echo("❌ LLM connection failed!")
                click.echo("\nTroubleshooting:")
                click.echo("1. Make sure Ollama is running: ollama serve")
                click.echo(
                    f"2. Check if model exists: ollama list | grep {config.llm.model}"
                )
                click.echo(f"3. Pull model if needed: ollama pull {config.llm.model}")

            provider.close()

        asyncio.run(run_test())

    except Exception as e:
        click.echo(f"❌ Test failed: {e}", err=True)


@cli.command(name="shell")
@click.option(
    "--safe-mode/--no-safe-mode", default=None, help="Enable/disable safe mode"
)
@click.option(
    "--confirm/--no-confirm", default=None, help="Require confirmation for commands"
)
@click.pass_context
def shell_command(ctx, safe_mode: Optional[bool], confirm: Optional[bool]):
    """Start the interactive LLMShell."""
    from .core import start_interactive_shell
    from .llm import create_llm_provider, test_llm_connection

    click.echo("🚀 Starting LLMShell...")

    try:
        # Load configuration
        config = load_config()

        # Override config with command line options
        if safe_mode is not None:
            config.execution.safe_mode = safe_mode
        if confirm is not None:
            config.execution.always_confirm = confirm

        click.echo(f"📋 Using: {config.llm.provider} ({config.llm.model})")
        click.echo(f"🔗 URL: {config.llm.base_url}")

        async def run_shell():
            # Create LLM provider
            provider = create_llm_provider(config.llm)

            # Test connection
            if not await test_llm_connection(provider):
                click.echo("❌ LLM connection failed!")
                click.echo("\nTroubleshooting:")
                click.echo("1. Make sure Ollama is running: ollama serve")
                click.echo(
                    f"2. Check if model exists: ollama list | grep {config.llm.model}"
                )
                click.echo(f"3. Pull model if needed: ollama pull {config.llm.model}")
                provider.close()
                return

            # Start interactive shell
            await start_interactive_shell(config, provider)

        asyncio.run(run_shell())

    except KeyboardInterrupt:
        click.echo("\n👋 Goodbye!")
    except Exception as e:
        click.echo(f"❌ Failed to start shell: {e}", err=True)


def main():
    """Main entry point for the CLI."""
    cli()


@cli.command()
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    try:
        config = load_config()
        click.echo("📋 Current LLMShell Configuration")
        click.echo("=" * 40)
        click.echo(f"LLM Provider: {config.llm.provider}")
        click.echo(f"LLM Model: {config.llm.model}")
        click.echo(f"LLM URL: {config.llm.base_url}")
        click.echo(f"Timeout: {config.llm.timeout}s")
        click.echo(f"Temperature: {config.llm.temperature}")
        click.echo()
        click.echo(f"Safe Mode: {config.execution.safe_mode}")
        click.echo(f"Always Confirm: {config.execution.always_confirm}")
        click.echo(f"Log Level: {config.logging.level}")
        click.echo(f"Log Commands: {config.logging.log_commands}")

        # Show config file location
        for path in get_config_paths():
            if path.exists():
                click.echo(f"\nConfig file: {path}")
                break
        else:
            click.echo("\nNo config file found (using defaults)")

    except Exception as e:
        click.echo(f"❌ Failed to load configuration: {e}", err=True)


if __name__ == "__main__":
    main()
