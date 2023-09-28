"""
Parse golang's pprof format into flameshow.models which can be rendered.

Ref:
https://github.com/google/pprof/tree/main/proto
"""
import gzip
import logging

from dataclasses import dataclass
from . import profile_pb2
from typing_extensions import List

from flameshow.models import SampleType, Profile

logger = logging.getLogger(__name__)


def unmarshal(content) -> profile_pb2.Profile:
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


class ProfileParser:
    def __init__(self, filename):
        self.filename = filename

        # store the pprof's string table
        self._t = []

    def s(self, index):
        return self._t[index]

    def parse(self, binary_data):
        pbdata = unmarshal(binary_data)

        self._t = pbdata.string_table

        print(dir(pbdata))

        pprof_profile = Profile()
        pprof_profile.sample_types = self.parse_sample_types(pbdata.sample_type)
        return pprof_profile

    def parse_sample_types(self, sample_types):
        result = []
        for st in sample_types:
            result.append(SampleType(self.s(st.type), self.s(st.unit)))

        print("parse sample type done, result=", result)
        return result


def parse_profile(binary_data, filename):
    parser = ProfileParser(filename)
    profile = parser.parse(binary_data)

    return profile


if __name__ == "__main__":
    with open("tests/pprof_data/profile-10seconds.out", "rb") as f:
        content = f.read()

    parse_profile(content, "abc")
