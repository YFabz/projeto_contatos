import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


def conectar():
    """Devolve o MongoClient. A conexão real só acontece na primeira operação."""
    load_dotenv(Path(__file__).with_name('.env'))
    uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    return MongoClient(uri, serverSelectionTimeoutMS=5000)
