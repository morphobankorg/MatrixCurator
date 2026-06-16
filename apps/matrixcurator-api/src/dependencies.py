from matrixcurator import MatrixCuratorClient

# Initialize the client once for the FastAPI application.
# Any explicit settings can be passed as root-level keyword arguments here.
client = MatrixCuratorClient(app_name="fastapi")

def get_client() -> MatrixCuratorClient:
    """Dependency to inject the MatrixCuratorClient into route handlers."""
    return client
