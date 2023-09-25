from distutils.core import Extension
from distutils.command.build_ext import build_ext
from distutils.errors import CompileError
from subprocess import call
from distutils.errors import DistutilsPlatformError


ext_modules = [
    Extension(
        "flameshow.pprof_parser._libpprofparser",
        include_dirs=["go/*"],
        sources=["libpprofparser.go"],
    ),
]


class BuildFailed(Exception):
    pass


class GoExtBuilder(build_ext):
    def run(self):
        try:
            build_ext.run(self)
        except (DistutilsPlatformError, FileNotFoundError):
            print("Could not compile Go extension.")
            raise

    def build_extension(self, ext):
        ext_path = self.get_ext_fullpath(ext.name)
        cmd = ["go", "build", "-buildmode=c-shared", "-o", ext_path]
        cmd += ext.sources
        out = call(cmd, cwd="./go")

        if out != 0:
            raise CompileError("Go build failed")


def build(setup_kwargs):
    """
    This function is mandatory in order to build the extensions.
    """
    print("start to build golang extension...")
    setup_kwargs.update(
        {"ext_modules": ext_modules, "cmdclass": {"build_ext": GoExtBuilder}}
    )
