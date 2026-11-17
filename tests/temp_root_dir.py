"""
TEMP_ROOT_DIR
"""

import sys
import os
import tempfile

TEMP_ROOT_DIR = os.path.join(
    tempfile.gettempdir(),
    f"backo_tests_{sys.version_info.major}_{sys.version_info.minor}_{sys.version_info.micro}",
)
if not os.path.exists(TEMP_ROOT_DIR):
    os.makedirs(TEMP_ROOT_DIR)
