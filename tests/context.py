import os
import sys
from dotenv import dotenv_values

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nimbusCore import *

secret = dotenv_values(dotenv_path=os.path.realpath(os.path.dirname(__file__)) + '/../.env')