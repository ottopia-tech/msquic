import os
from conan import ConanFile
from conan.tools.files import copy


class MsQuicMpConan(ConanFile):
    name = "msquic"
    version = "2.6.0-mp"
    description = "msquic masa-koz/mpquic-path-selector fork — 3-path MP-QUIC + pluggable path selector"
    license = "MIT"
    url = "https://github.com/ottopia-tech/msquic"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": True, "fPIC": True}

    # CI workflow: build first with cmake (see .ci/), then conan export-pkg.
    # No conan build() method — msquic uses its own cmake presets/submodules.

    def package_id(self):
        # msquic is built once (Release); collapse build_type so Debug consumers find same package.
        del self.info.settings.build_type
        del self.info.settings.compiler

    def configure(self):
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def package(self):
        build_type = str(self.settings.build_type)
        src  = self.source_folder
        inc  = os.path.join(src, "src", "inc")
        binr = os.path.join(src, "build", "bin", build_type)
        for h in ("msquic.h", "msquic_posix.h", "quic_sal_stub.h"):
            copy(self, h, src=inc, dst=os.path.join(self.package_folder, "include"))
        copy(self, "libmsquic.so*", src=binr, dst=os.path.join(self.package_folder, "lib"))

    def package_info(self):
        self.cpp_info.libs = ["msquic"]
        self.cpp_info.set_property("cmake_file_name", "msquic")
        self.cpp_info.set_property("cmake_target_name", "msquic")
        # Required so consumers see MultipathEnabled, ADD_LOCAL_ADDRESS, PATH_ADDED, etc.
        self.cpp_info.defines = ["QUIC_API_ENABLE_PREVIEW_FEATURES"]
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread", "dl", "m", "atomic"]
