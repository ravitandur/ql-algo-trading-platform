import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="options-strategy-lifecycle-platform",
    version="0.1.0",
    author="Trading Platform Team",
    author_email="platform-team@quantlab.com",
    description="AWS CDK infrastructure for Options Strategy Lifecycle Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ravitandur/ql-algo-trading-platform",
    project_urls={
        "Bug Tracker": "https://github.com/ravitandur/ql-algo-trading-platform/issues",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.9",
    install_requires=[
        "aws-cdk-lib>=2.100.0",
        "constructs>=10.0.0,<11.0.0",
        "boto3>=1.28.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "deploy-infrastructure=infrastructure.cli:main",
        ],
    },
)