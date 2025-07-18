from setuptools import setup, find_packages

setup(
    name='pcapymodules',
    version='0.1.0',
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
