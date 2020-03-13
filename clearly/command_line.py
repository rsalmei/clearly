import logging

import click

from clearly.server import start_server

logger = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def clearly():
    """Clearly command line tools."""
    pass


@clearly.group(invoke_without_command=True)
@click.pass_context
@click.option("--port", '-p', default=12223)
@click.option("--host", default="localhost")
def client(ctx, host, port):
    from clearly.client import ClearlyClient
    cli = ClearlyClient(host=host, port=port)
    ctx.obj = dict()
    ctx.obj["client-cli"] = cli
    if ctx.invoked_subcommand is None:
        cli.capture()

@client.command()
@click.pass_context
def workers(ctx):
    ctx.obj["client-cli"].workers()

@client.command()
@click.pass_context
def capture(ctx):
    ctx.obj["client-cli"].capture()

@clearly.command()
@click.argument('broker')
@click.option('--backend', '-b',
              help='Fetches task results from the result backend, like "redis://localhost"')
@click.option('--port', '-p', type=int, help='Listen port for Clearly Server')
@click.option('--max_tasks', '-t', type=int, help='Maximum number of tasks in memory')
@click.option('--max_workers', '-w', type=int, help='Maximum number of workers in memory')
@click.option('--debug', help='Enables debug logging', is_flag=True)
def server(**kwargs):
    """
    Starts the Clearly Server.

        BROKER: The broker being used by celery, like "amqp://localhost".
    """
    start_server(**{k: v for k, v in kwargs.items() if v},
                 blocking=True)
