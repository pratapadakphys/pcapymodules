from setuptools import setup, find_packages
import re, os
def get_version():
    with open(os.path.join("pcapymodules", "__init__.py")) as f:
        for line in f:
            if line.startswith("__version__"):
                return re.search(r'"(.*?)"', line).group(1)

setup(
    name='pcapymodules',
    version=get_version(),
    description='Custom measurement and analysis tools for the lab',
    author='Pratap Chandra Adak',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'matplotlib',
        'scipy',
        'pandas',
        'untangle',
        'requests',
        'pythonnet',
        'pyvisa',
        'pyusb'
        # add other dependencies here
    ],
)
