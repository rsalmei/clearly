import logging

import click

from clearly.server import start_server

logger = logging.getLogger('clearly.command_line')


@click.group()
@click.version_option()
def clearly():
    """Clearly command line tools."""
    pass


@clearly.command()
@click.argument('broker')
@click.option('--backend', '-b',
              help='Enables fetching task results from the result backend, like "redis://localhost"')
@click.option('--port', '-p', type=int, help='Listen port for Clearly Server')
@click.option('--max_tasks', '-t', type=int, help='Maximum number of tasks in memory')
@click.option('--max_workers', '-w', type=int, help='Maximum number of workers in memory')
@click.option('--debug', help='Enables debug logging', is_flag=True)
def server(**kwargs):
    """
    Starts the Clearly Server.

        BROKER: The broker being used by celery, like "amqp://localhost".
    """
    start_server(**{k: v for k, v in kwargs.items() if v})

