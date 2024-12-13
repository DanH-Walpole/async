from setuptools import setup, find_packages

setup(
    name="searchapp",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "flask",
        "dash",
        "dash-bootstrap-components",
        "requests",
        "beautifulsoup4",
        "PyPDF2",
        "pdfminer",
        "pdfplumber",
        "pymupdf",
        "html2text",
        "python-dotenv",
        "redis",
        "faker",
        "aiohttp",
        "pydantic",
    ],
    python_requires=">=3.7",
)