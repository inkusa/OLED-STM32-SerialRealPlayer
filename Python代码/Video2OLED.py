import argparse
import numpy as np
import cv2
import serial
import time
import serial.tools.list_ports

# 列出所有可用的串口
ports = serial.tools.list_ports.comports()
for port, desc, hwid in sorted(ports):
    print(f"{port}: {desc} [{hwid}]")


# 将128*64的二值化图像转换为OLED数组格式
def img2array(frame):
    array = np.zeros((8, 128), dtype='uint8')

    for j in range(64):
        for i in range(128):
            if frame[j][i] > 0:
                array[j // 8][i] |= (0x01 << (j % 8))

    return array

def main():
    # 命令行参数
    parser = argparse.ArgumentParser(description="OLED视频播放工具")
    parser.add_argument("com", help="串口号")
    parser.add_argument("video", help="视频文件")
    parser.add_argument("review", nargs="?", help="预览窗口")
    args = parser.parse_args()

    # 打开串口
    serial_port = serial.Serial(args.com, 921600)

    # 设置预览窗口
    if args.review == "review":
        cv2.namedWindow('img', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('img', 128 * 4, 64 * 4)

    # 打开视频
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"无法打开视频：{args.video}")
        serial_port.close()
        return

    # 获取视频FPS
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        print("无法获取视频FPS")
        cap.release()
        serial_port.close()
        return

    # 记住开始时间
    start_time = time.time()

    while True:

        # 获取当前时间对应的帧数
        run_time = time.time() - start_time
        frame_number = int(run_time * fps)

        # 获取当前帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        flag, img = cap.read()
        if not flag:
            break

        # 帧图像处理
        img = cv2.resize(img, (128, 64))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.threshold(img, 170, 255, cv2.THRESH_BINARY)[1]

        # 预览图像
        if args.review == "review":
            cv2.imshow('img', img)

        # 转换为数组并使用串口发送
        img_array = img2array(img)
        serial_port.write(img_array.tobytes())

        # 等待按键，按q键退出
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            break

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()
    serial_port.close()


if __name__ == "__main__":
    main()
