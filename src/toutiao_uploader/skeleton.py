"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = toutiao_uploader.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This file can be renamed depending on your needs or safely removed if not needed.

References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import logging
import sys

from toutiao_uploader import __version__

__author__ = "bitterg"
__copyright__ = "bitterg"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from toutiao_uploader.skeleton import fib`,
# when using this Python module as a library.
# src/toutiao_uploader/skeleton.py
from .uploader import ToutiaoUploader

def fib(n):
    """Fibonacci example function

    Args:
      n (int): integer

    Returns:
      int: n-th Fibonacci number
    """
    assert n > 0
    a, b = 1, 1
    for _i in range(n - 1):
        a, b = b, a + b
    return a


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version=f"toutiao_uploader {__version__}",
    )
    parser.add_argument(dest="n", help="n-th Fibonacci number", type=int, metavar="INT")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def login(username):
    uploader = ToutiaoUploader()
    uploader.login(username)
def get_user_info(username):
    uploader = ToutiaoUploader()
    uploader.get_user_info(username)
def publish_wtt_main(content):
    uploader = ToutiaoUploader()
    uploader.publishWTT(content)

def publish_video(username,video_path):
    uploader = ToutiaoUploader()
    uploader.upload_video_in_parts(username, video_path)
def main():
    parser = argparse.ArgumentParser(description="Toutiao 上传工具")
    subparsers = parser.add_subparsers(dest="command")

    # login 子命令
    login_parser = subparsers.add_parser("login", help="登录今日头条账号")
    login_parser.add_argument("--user", required=True, help="指定用户名")

    publish_parser = subparsers.add_parser("publish_wtt", help="发布微头条")
    publish_parser.add_argument("content", type=str, help="微头条内容")

    get_user_info_parser = subparsers.add_parser("get_user_info", help="获取用户信息")
    get_user_info_parser.add_argument("--user", type=str, help="用户名")

    publish_video_parser = subparsers.add_parser("publish_video", help="发布视频")
    publish_video_parser.add_argument("--user", type=str, help="指定用户名称")
    publish_video_parser.add_argument("--video", type=str, help="视频文件路径")

    args = parser.parse_args()

    if args.command == "login":
        login(args.user)
    elif args.command == "get_user_info":
        get_user_info(args.user)
    elif args.command == "publish_video":
        publish_video(args.user, args.video)
    elif args.command == "publish_wtt":
        publish_wtt_main(args.content)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m toutiao_uploader.skeleton 42
    #
    run()
