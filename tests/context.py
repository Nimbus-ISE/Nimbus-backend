import os
import sys
from dotenv import dotenv_values

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nimbusCore import *

if os.environ.get("VERCEL"):
    secret = os.environ
else:
    secret = dotenv_values(os.path.dirname(os.path.realpath(__file__)) + '/../.env')