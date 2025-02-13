# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import find_packages
from sys import platform as _platform
import sys
import glob
import os

from distutils.core import setup
from distutils.extension import Extension
from distutils.util import get_platform
from glob import glob

# monkey-patch for parallel compilation
import multiprocessing
import multiprocessing.pool


def parallelCCompile(self,
                     sources,
                     output_dir=None,
                     macros=None,
                     include_dirs=None,
                     debug=0,
                     extra_preargs=None,
                     extra_postargs=None,
                     depends=None):
    # those lines are copied from distutils.ccompiler.CCompiler directly
    macros, objects, extra_postargs, pp_opts, build = self._setup_compile(
        output_dir, macros, include_dirs, sources, depends, extra_postargs)
    cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)
    # parallel code
    N = 2 * multiprocessing.cpu_count()  # number of parallel compilations
    try:
        # On Unix-like platforms attempt to obtain the total memory in the
        # machine and limit the number of parallel jobs to the number of Gbs
        # of RAM (to avoid killing smaller platforms like the Pi)
        mem = os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')  # bytes
    except (AttributeError, ValueError):
        # Couldn't query RAM; don't limit parallelism (it's probably a well
        # equipped Windows / Mac OS X box)
        pass
    else:
        mem = max(1, int(round(mem / 1024 ** 3)))  # convert to Gb
        N = min(mem, N)

    def _single_compile(obj):
        try:
            src, ext = build[obj]
        except KeyError:
            return
        newcc_args = cc_args
        if _platform == "darwin":
            if src.endswith('.cpp') or src.endswith('.cc'):
                newcc_args = cc_args + ["-mmacosx-version-min=10.15", "-std=c++17", "-stdlib=libc++"]
        self._compile(obj, src, ext, newcc_args, extra_postargs, pp_opts)

    # convert to list, imap is evaluated on-demand
    pool = multiprocessing.pool.ThreadPool(N)
    list(pool.imap(_single_compile, objects))
    return objects


import distutils.ccompiler

distutils.ccompiler.CCompiler.compile = parallelCCompile

# see http://stackoverflow.com/a/8719066/295157
import os

platform = get_platform()
print(platform)

CXX_FLAGS = ''
CXX_FLAGS += '-fpermissive '
CXX_FLAGS += '-D_USE_MATH_DEFINES '

# libraries += [current_python]

libraries = []
include_dirs = ['.','python', 'third_party/pybind11/include']


try:
    import numpy

    NP_DIRS = [numpy.get_include()]
except:
    print("numpy is disabled. getCameraImage maybe slower.")
else:
    print("numpy is enabled.")
    CXX_FLAGS += '-DPYBULLET_USE_NUMPY '
    for d in NP_DIRS:
        print("numpy_include_dirs = %s" % d)
    include_dirs += NP_DIRS


pytinyrenderer_sources = ["python/pytinyrenderer.cc",\
  "geometry.cpp",
  "model.cpp",
  "our_gl.cpp",
  "tinyrenderer.cpp",
  "tgaimage.cpp",
  
]



if _platform == "linux" or _platform == "linux2":
    print("linux")
    libraries = ['dl', 'pthread', 'stdc++fs']
    CXX_FLAGS += '-D_LINUX '
    CXX_FLAGS += '-DGLEW_STATIC '
    CXX_FLAGS += '-DGLEW_INIT_OPENGL11_FUNCTIONS=1 '
    CXX_FLAGS += '-DGLEW_DYNAMIC_LOAD_ALL_GLX_FUNCTIONS=1 '
    CXX_FLAGS += '-DDYNAMIC_LOAD_X11_FUNCTIONS '

    CXX_FLAGS += '-DHAS_SOCKLEN_T '
    CXX_FLAGS += '-fno-inline-functions-called-once '
    CXX_FLAGS += '-fvisibility=hidden '
    CXX_FLAGS += '-fvisibility-inlines-hidden '
    CXX_FLAGS += '-std=c++1z '
    CXX_FLAGS += '-Wno-sign-compare '
    CXX_FLAGS += '-Wno-reorder '
    CXX_FLAGS += '-Wno-unused-local-typedefs '
    CXX_FLAGS += '-Wno-unused-variable '
    CXX_FLAGS += '-Wno-unused-but-set-variable '
    


elif _platform == "win32":
    print("win32!")
    libraries = ['User32', 'kernel32']
    CXX_FLAGS += '-DWIN32 '
    CXX_FLAGS += '-DGLEW_STATIC '
    CXX_FLAGS += '/std:c++17 '
    
    
    
elif _platform == "darwin":
    print("darwin!")
    os.environ['LDFLAGS'] = '-framework Cocoa -mmacosx-version-min=10.15 -stdlib=libc++ -framework OpenGL'
    CXX_FLAGS += '-DB3_NO_PYTHON_FRAMEWORK '
    CXX_FLAGS += '-DHAS_SOCKLEN_T '
    CXX_FLAGS += '-D_DARWIN '
    CXX_FLAGS += '-mmacosx-version-min=10.15 '
    #    CXX_FLAGS += '-framework Cocoa '
    
    
else:
    print("bsd!")
    libraries = ['GL', 'GLEW', 'pthread']
    os.environ['LDFLAGS'] = '-L/usr/X11R6/lib'
    CXX_FLAGS += '-D_BSD '
    CXX_FLAGS += '-I/usr/X11R6/include '
    CXX_FLAGS += '-DHAS_SOCKLEN_T '
    CXX_FLAGS += '-fno-inline-functions-called-once'

setup_py_dir = os.path.dirname(os.path.realpath(__file__))


extensions = []

CXX_FLAGS_TDS = CXX_FLAGS + '-DENABLE_TEST_ENVS ' + '-DNOMINMAX '

pytinyrenderer_ext = Extension(
    "pytinyrenderer",
    sources=pytinyrenderer_sources,
    libraries=libraries,
    extra_compile_args=CXX_FLAGS_TDS.split(),
    include_dirs=include_dirs + ["."])
extensions.append(pytinyrenderer_ext)


setup(
    name='pytinyrenderer',
    version='0.0.3',
    description=
    'Python bindings for Tiny Renderer',
    long_description=
    'Python bindings for Tiny Renderer',
    url='https://github.com/erwincoumans/tinyrenderer',
    author='Dmitry V. Sokolov, Erwin Coumans',
    author_email='erwincoumans@google.com',
    license='Zlib/PNG License',
    platforms='any',
    keywords=[
        'cpu','rendering','3d'
    ],
    #install_requires=[
    #    'numpy',
    #],
    ext_modules=extensions,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: zlib/libpng License',
        'Operating System :: Microsoft :: Windows', 'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS', 'Intended Audience :: Science/Research',
        "Programming Language :: Python", 'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4', 'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6', 'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8', 'Topic :: Games/Entertainment :: Simulation',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Framework :: Robot Framework'
    ],
    package_dir={'': 'python'},
    packages=[x for x in find_packages('python')],
    #package_data={'pytinydiffsim_data': need_files}
    )
