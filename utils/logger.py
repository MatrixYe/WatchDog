# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         logger 
# Author:       yepeng
# Date:         2024/10/30 10:53
# Description: 
# -------------------------------------------------------------------------------
# logger_util.py

import logging
from logging import Logger
from logging.handlers import RotatingFileHandler


class MyLogger:
    _logger: Logger = None

    @staticmethod
    def new(name=None, log_file: str = None, level=logging.INFO):
        if MyLogger._logger is not None:
            return MyLogger._logger

        # 创建一个日志器
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # 防止重复添加处理器
        if not logger.handlers:
            # 定义日志输出格式
            formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                          datefmt='%Y-%m-%d %H:%M:%S')

            # 创建控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # 创建文件处理器，支持日志轮转
            if log_file:
                file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

        MyLogger._logger = logger
        return logger
