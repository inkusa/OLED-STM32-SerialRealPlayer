import argparse
import time

import cv2
import numpy as np
import serial
import serial.tools.list_ports
from mss import mss


# 列出所有串口
ports = serial.tools.list_ports.comports()
print("可用串口：")
for port, desc, hwid in sorted(ports):
    print(f"{port}: {desc} [{hwid}]")


# OLED格式转换
def img2array(frame):
    array = np.zeros((8, 128), dtype=np.uint8)

    for page in range(8):
        block = frame[page * 8:(page + 1) * 8, :] > 0

        for bit in range(8):
            array[page] |= block[bit].astype(np.uint8) << bit

    return array


def main():
    parser = argparse.ArgumentParser(description="OLED实时桌面镜像")
    parser.add_argument("com", help="串口号")
    parser.add_argument("review", nargs="?", help="输入 review 开启预览")
    args = parser.parse_args()

    # 打开串口
    serial_port = serial.Serial(args.com, 921600)

    # 初始化截图
    sct = mss()

    # 主显示器
    monitor = sct.monitors[1]

    print("截图区域：")
    print(monitor)

    if args.review == "review":
        cv2.namedWindow("OLED Preview", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("OLED Preview", 128 * 4, 64 * 4)

    last_time = time.time()
    frame_count = 0

    while True:

        # 截图
        img = np.array(sct.grab(monitor))

        # BGRA -> BGR
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # 缩放到OLED尺寸
        img = cv2.resize(
            img,
            (128, 64),
            interpolation=cv2.INTER_AREA
        )

        # 灰度
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 二值化
        img = cv2.adaptiveThreshold(
            img,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15,
            3
        )

        if args.review == "review":
            cv2.imshow("OLED Preview", img)

        # 转OLED数据
        img_array = img2array(img)

        # 发送
        serial_port.write(img_array.tobytes())

        frame_count += 1

        # 每秒显示FPS
        if time.time() - last_time >= 1:
            print(f"FPS: {frame_count}")
            frame_count = 0
            last_time = time.time()

        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    serial_port.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()