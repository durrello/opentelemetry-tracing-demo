from setuptools import find_packages, setup

setup(
    name="otel-demo-common",
    version="0.1.0",
    description="Shared OpenTelemetry tracing + propagation helpers for the demo",
    packages=find_packages(),
    python_requires=">=3.9",
)
