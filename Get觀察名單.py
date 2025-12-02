#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get觀察名單.py
Downloads Taiwan stock market lists from GitHub repository:
1. 觀察名單.csv -> StockID_TWSE_TPEX.csv (Observation list)
2. 專注名單.csv -> StockID_TWSE_TPEX_focus.csv (Focus list)
"""

import requests
import os
from datetime import datetime

def download_file(url, output_file, list_name):
    """
    Download a file from URL and save locally

    Args:
        url: Source URL
        output_file: Local filename to save
        list_name: Display name for the list

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"\n開始下載{list_name}...")
        print(f"來源: {url}")

        # Download the file
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Save to file
        with open(output_file, 'wb') as f:
            f.write(response.content)

        # Get file size
        file_size = os.path.getsize(output_file)

        print(f"✅ 下載成功!")
        print(f"   檔案名稱: {output_file}")
        print(f"   檔案大小: {file_size:,} bytes")
        print(f"   下載時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Try to read and count stocks
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                stock_count = sum(1 for _ in f)
                print(f"   檔案標頭: {first_line}")
                print(f"   股票數量: {stock_count} 檔")
        except UnicodeDecodeError:
            # Try with different encoding
            with open(output_file, 'r', encoding='big5') as f:
                first_line = f.readline().strip()
                stock_count = sum(1 for _ in f)
                print(f"   檔案標頭: {first_line}")
                print(f"   股票數量: {stock_count} 檔")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ 下載失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 處理檔案時發生錯誤: {e}")
        return False

def download_observation_list():
    """Download observation list (觀察名單)"""
    url = "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E8%A7%80%E5%AF%9F%E5%90%8D%E5%96%AE.csv"
    output_file = "StockID_TWSE_TPEX.csv"
    return download_file(url, output_file, "觀察名單")

def download_focus_list():
    """Download focus list (專注名單)"""
    url = "https://raw.githubusercontent.com/wenchiehlee/GoPublic/refs/heads/main/%E5%B0%88%E6%B3%A8%E5%90%8D%E5%96%AE.csv"
    output_file = "StockID_TWSE_TPEX_focus.csv"
    return download_file(url, output_file, "專注名單")

def main():
    """Main function"""
    print("=" * 60)
    print("台灣股市名單下載程式")
    print("=" * 60)
    print("📥 下載來源: wenchiehlee/GoPublic")
    print("📋 名單類型: 觀察名單 + 專注名單")

    # Download both lists
    success_observation = download_observation_list()
    success_focus = download_focus_list()

    # Summary
    print("\n" + "=" * 60)
    print("下載結果摘要")
    print("=" * 60)

    if success_observation:
        print("✅ 觀察名單 (StockID_TWSE_TPEX.csv) - 下載成功")
    else:
        print("❌ 觀察名單 (StockID_TWSE_TPEX.csv) - 下載失敗")

    if success_focus:
        print("✅ 專注名單 (StockID_TWSE_TPEX_focus.csv) - 下載成功")
    else:
        print("❌ 專注名單 (StockID_TWSE_TPEX_focus.csv) - 下載失敗")

    # Overall status
    if success_observation and success_focus:
        print("\n程式執行完成! 🎉")
        print("兩份名單皆已成功下載")
        return 0
    elif success_observation or success_focus:
        print("\n程式部分成功 ⚠️")
        print("至少一份名單下載失敗")
        return 1
    else:
        print("\n程式執行失敗! ❌")
        print("所有名單下載失敗")
        return 1

if __name__ == "__main__":
    exit(main())
