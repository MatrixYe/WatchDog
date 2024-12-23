# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         util 
# Author:       yepeng
# Date:         2024/12/23 11:17
# Description: 
# -------------------------------------------------------------------------------
import tomllib


# 读取 TOML 配置文件
def load_toml_config(file_path='config.toml') -> dict:
    try:
        with open(file_path, "rb") as file:  # 使用二进制模式读取
            config = tomllib.load(file)
        return config
    except Exception as e:
        print(f"Failed to load TOML config: {e}")
        return {}
