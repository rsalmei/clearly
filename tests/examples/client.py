from clearly.client import ClearlyClient
from clearly.server import ClearlyServer
from tasks import app

srv = ClearlyServer(app)
cli = ClearlyClient(srv)
