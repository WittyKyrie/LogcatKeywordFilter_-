import datetime
import os
import subprocess
import threading
import json
import sys

LOG_PATH = ""

KEYWORDS = []

STOP_LOGCAT = True

INSTRUCTION = {
    "1": "filter_keywords",
    "2": "stop_filter_keywords",
    "3": "exit"
}


def filter_keywords():
    global STOP_LOGCAT
    STOP_LOGCAT = False
    devices = get_devices()  # 先获取所有连接的设备
    print("开始监控关键字")
    for device in devices:
        t = threading.Thread(target=filter_keyword, args=(device,))
        t.start()


def stop_filter_keywords():
    global STOP_LOGCAT
    if STOP_LOGCAT:
        print("没有正在执行的任务\n")
    else:
        STOP_LOGCAT = True
        print("正在停止关键字监控\n")


def filter_keyword(device):
    print("设备%s关键字监控已开启" % str(device))
    sub = logcat(device)
    with sub:
        for line in sub.stdout:  # 子进程会持续输出日志，对子进程对象.stdout进行循环读取
            for key in KEYWORDS:
                if line.decode("utf-8").find(key) != -1:
                    message = "设备：%s 检测到：%s 日志信息：%s\n" % (device, key, line)
                    path = get_log_path("bugreport")
                    bugreport(device, path, message)
                    print(message)
            if STOP_LOGCAT:
                break
        print("设备%s关键字监控已停止" % str(device))
        sub.kill()


def logcat(device):
    command = "adb logcat -c"
    subprocess.call(command)

    command = "adb -s " + str(device) + " logcat -v time *:W"
    sub = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return sub


def get_devices():
    command = "adb devices"
    res = os.popen(command).read()
    devices = []
    res = res.split("\n")
    for i in res:
        if i.endswith("device"):
            devices.append(i.split('\t')[0])
    return devices


def bugreport(device, path, message):
    os.chdir(path)
    year = datetime.datetime.now().strftime('%Y')
    month = datetime.datetime.now().strftime('%m')
    day = datetime.datetime.now().strftime('%d')

    command = "adb -s " + str(device) + " bugreport"
    subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
    print("设备：%s 日志路径：%s" % (str(device), path))

    keyword_logcat = open("keyword_logcat%s-%s-%s.txt" % (year, month, day), "a")
    keyword_logcat.write(message)
    keyword_logcat.close()


def get_log_path(tag):
    year = datetime.datetime.now().strftime('%Y')
    month = datetime.datetime.now().strftime('%m')
    day = datetime.datetime.now().strftime('%d')
    path = os.path.join(LOG_PATH, tag, "%s %s %s" % (year, month, day))
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def read_config():
    f = open('SDKTestConfig.json')
    data = json.load(f)
    for i in data['KEYWORDS']:
        KEYWORDS.append(i['word'])

    global LOG_PATH
    LOG_PATH = os.path.join(data['LOG_PATH'])
    print(LOG_PATH)
    return data


def main():
    read_config()
    while True:
        print("-" * 100)
        print("1：开启关键字监控  2：停止关键字监控  3:exit")
        print("-" * 100)
        instruction = str(input("\n请输入要进行的操作号:"))
        print("-" * 100)
        while instruction not in INSTRUCTION.keys():
            instruction = str(input("\n输入无效，请重新输入:"))
        if int(instruction) == 3:
            stop_filter_keywords()
            sys.exit(0)
            # exit()
        eval(INSTRUCTION[str(instruction)] + "()")


if __name__ == '__main__':
    main()
