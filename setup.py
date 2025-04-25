from setuptools import setup, find_packages

requirements = []
# read requirements.txt
with open("requirements.txt") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            requirements.append(line)
print(requirements)

setup(
    name="femora",
    version="0.1.0",
    author="Amin Pakzad, Pedro Arduino",
    author_email="amnp95@uw.edu",
    description="Fast Efficient Meshing for OpenSees-based Resilience Analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/amnp95/Femora",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "femora=femora.main:main",
        ],
    },
)
