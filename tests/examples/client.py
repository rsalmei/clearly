from clearly.client import ClearlyClient
from clearly.server import start_server

# uncomment to test internal server
# server = start_server('amqp://localhost')

cli = ClearlyClient()

cli.capture(params=True, success=True)
