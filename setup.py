from setuptools import setup, find_packages

setup(
    name="telemetry",
    version="1.0",
    packages=["telemetry"],
    include_package_data=True,
    install_requires=["click", "requests", "webbrowser"],
    entry_points="""
        [console_scripts]
        telemetry=telemetry:cli
    """,
)
