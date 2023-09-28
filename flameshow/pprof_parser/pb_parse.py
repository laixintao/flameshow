import gzip
import logging

from dataclasses import dataclass
from . import profile_pb2
from typing_extensions import List

logger = logging.getLogger(__name__)


def parse_pprof_file(content) -> profile_pb2.Profile:
    if len(content) < 2:
        raise Exception(
            "Profile content lengh is too short: {} bytes".format(len(content))
        )
    is_gzip = content[0] == 31 and content[1] == 139
    if is_gzip:
        print("the pprof file is gzip.")
        content = gzip.decompress(content)

    profile = profile_pb2.Profile()
    profile.ParseFromString(content)

    return profile

@dataclass
class SampleType:
    stype: str
    unit: str
    
@dataclass
class PprofProfile:
    sample_type: List[SampleType]



if __name__ == "__main__":
    with open("tests/pprof_data/profile-10seconds.out", "rb") as f:
        content = f.read()

    data = parse_pprof_file(content)
    print(dir(data))
    print(data.sample)
    print(data.sample_type)
    print(data.string_table)

    pprof_profile = PprofProfile()
