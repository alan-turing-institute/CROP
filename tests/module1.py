import pytest
import os
import sys
import pandas as pd

from pathlib import Path
#resolve paths
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from crop.constants import CONST_DATA_FOLDER

print (CONST_DATA_FOLDER)

name = " YoUr StRiNg"
s = "".join(name.split()).lower()
print (s)
