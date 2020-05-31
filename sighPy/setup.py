import setuptools

setuptools.setup(
    name="sighPy",
    version="0.0.1",
    author="C. Cheng, C. Yip",
    description="Lightweight framework for parsing scientific files to local DB. Some exports supported.",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    install_requires=[
        "pandas",
        "numpy",
        "rasterio",
        "flask",
        "flask_sqlalchemy",
        "sqlalchemy",
        "h5py",
        "netCDF4"
    ]
)
