import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy
from conan.tools.scm import Git


class MsQuicConan(ConanFile):
    name = "msquic"
    version = "2.3.5"
    description = (
        "Microsoft's cross-platform QUIC implementation "
        "(Ottopia fork, built with quictls/openssl3)"
    )
    license = "MIT"
    url = "https://github.com/ottopia-tech/msquic"
    homepage = "https://github.com/microsoft/msquic"
    topics = ("quic", "network", "tls", "openssl")

    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self)

    def source(self):
        data = self.conan_data["sources"][self.version]
        git = Git(self)
        git.fetch_commit(url=data["url"], commit=data["commit"])
        self.run(
            "git submodule update --init --recursive --depth 1 "
            "submodules/openssl3 submodules/clog",
            cwd=self.source_folder,
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["QUIC_TLS"] = "openssl3"
        tc.cache_variables["QUIC_BUILD_SHARED"] = "ON" if self.options.shared else "OFF"
        tc.cache_variables["QUIC_ENABLE_LOGGING"] = "OFF"
        tc.cache_variables["QUIC_BUILD_TEST"] = "OFF"
        tc.cache_variables["QUIC_BUILD_TOOLS"] = "OFF"
        tc.cache_variables["QUIC_BUILD_PERF"] = "OFF"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )

    def package_info(self):
        self.cpp_info.libs = ["msquic"]
        self.cpp_info.set_property("cmake_file_name", "msquic")
        self.cpp_info.set_property("cmake_target_name", "msquic")
        if self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread", "dl", "m", "numa", "atomic"]
