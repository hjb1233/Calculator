"""把 Python 节点、ROS 元数据和 launch 文件安装进工作空间。"""

from glob import glob

from setuptools import find_packages, setup

PACKAGE_NAME = "Calculator"

setup(
    name=PACKAGE_NAME,
    version="1.0.0",
    packages=find_packages(exclude=("test", "test.*", "docs", "docs.*")),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{PACKAGE_NAME}"]),
        (f"share/{PACKAGE_NAME}", ["package.xml", "LICENSE", "README.md"]),
        (f"share/{PACKAGE_NAME}/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="He Jianbo",
    maintainer_email="895092582@qq.com",
    description="A readable, tested ROS 2 calculator in Python",
    license="MIT",
    entry_points={
        "console_scripts": [
            "talker = calculator.publisher:main",
            "listener = calculator.subscriber:main",
            "add_two_ints_server = calculator.service:main",
            "add_two_ints_client = calculator.client:main",
        ],
    },
)
