from setuptools import setup, find_packages
import os

# 读取README文件
def read_long_description():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "通用热榜内容爬虫包，支持知乎、微博、微信公众号等平台"

# 读取requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "fastapi",
            "uvicorn[standard]", 
            "pydantic-settings",
            "httpx",
            "requests",
            "beautifulsoup4",
            "lxml",
            "playwright",
            "redis"
        ]

setup(
    name="hotlist-crawler",
    version="2.0.0",
    author="xfrrn",
    author_email="",
    description="通用热榜内容爬虫包，支持知乎、微博、微信公众号等平台的内容抓取",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/xfrrn/hotlist-crawler",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "hotlist_crawler": ["*.txt", "*.md", "*.json"],
        "": ["*.txt", "*.md", "*.json"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "black",
            "flake8",
        ],
        "api": [
            "fastapi",
            "uvicorn[standard]",
        ]
    },
    entry_points={
        "console_scripts": [
            "hotlist-crawler=hotlist_crawler:health_check",
        ],
    },
    keywords="crawler, scraper, zhihu, weibo, weixin, hotlist, content",
    project_urls={
        "Bug Reports": "https://github.com/xfrrn/hotlist-crawler/issues",
        "Source": "https://github.com/xfrrn/hotlist-crawler",
        "Documentation": "https://github.com/xfrrn/hotlist-crawler/blob/main/README.md",
    },
)