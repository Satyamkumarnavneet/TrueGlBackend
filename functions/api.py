from mangum import Mangum
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app
from main import app

# Create the handler for AWS Lambda
handler = Mangum(app) 