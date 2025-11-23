from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="network-device-exporter",
    version="1.0.0",
    author="marcoscartes",
    description="Network device discovery and Prometheus metrics exporter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/marcoscartes/network-device-exporter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "network-scanner=network_scanner.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "network_scanner": ["web/templates/*.html"],
    },
)
