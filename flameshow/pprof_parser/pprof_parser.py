from distutils.sysconfig import get_config_var
import json
import time
from pathlib import Path
import logging

import cffi

LIBNAME = "_libpprofparser"

logger = logging.getLogger(__name__)

here = Path(__file__).absolute().parent
ext_suffix = get_config_var("EXT_SUFFIX")
so_file = str(here / (LIBNAME + str(ext_suffix)))

ffi = cffi.FFI()

# Load library
lib = ffi.dlopen(so_file)

# Define the function prototypes
ffi.cdef("""

/* Return type for ParseProfile */
struct ParseProfile_return {
	char* r0;
	char* r1;
};
extern struct ParseProfile_return ParseProfile(char* profile, int length);
extern void FreeString(char* str);

""")


class GolangProfileParseException(Exception):
    ...


def parse_golang_profile(binary_content):
    t1 = time.time()
    result = lib.ParseProfile(binary_content, len(binary_content))

    t2 = time.time()
    logger.info("Parse pprof using golang, took %.2fs", t2 - t1)
    json_result = ffi.string(result.r0).decode()
    err = ffi.string(result.r1).decode()

    lib.FreeString(result.r0)
    lib.FreeString(result.r1)

    if err:
        raise GolangProfileParseException(err)

    python_dict = json.loads(json_result)
    t3 = time.time()
    logger.info("Loading json in Python, took %.2f", t3 - t2)
    return python_dict
