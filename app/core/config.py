import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL= os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("This url is not valid")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is not set")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    