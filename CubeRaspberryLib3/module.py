import smbus2
import time
import os
import subprocess

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import Adafruit_SSD1306 as SSD


class OLED(object):
    """Control of OLED display equipment"""

    def __init__(self, i2c_bus_number: int = 1, clear: bool = False):
        self.__clear = clear
        self.__clear_count = 0
        self.__top = -2
        self.__x = 0

        self.__i2c_bus_number = i2c_bus_number

        self.__total_last = 0
        self.__idle_last = 0

        self.__width = 128
        self.__height = 32
        self.__image = Image.new("1", (self.__width, self.__height))
        self.__draw = ImageDraw.Draw(self.__image)
        self.__font = ImageFont.load_default()

    def __del__(self):
        # print("OLED End!")
        pass

    def init(self) -> bool:
        """Initialize OLED, return True on success, False on failure"""

        i2c_bus = self.__i2c_bus_number
        try:
            oled = SSD.SSD1306_128_32(rst=None, i2c_bus=i2c_bus, gpio=1)
        except Exception as e:
            print("init SSD1306_128_32 failed: {}".format(e))
            print("OLED device no found: i2c_bus[{}]".format(i2c_bus))
            return False

        try:
            oled.begin()
        except Exception as e:
            print("init begin failed: {}".format(e))
            return False

        try:
            oled.clear()
        except Exception as e:
            print("init clear failed: {}".format(e))
            return False

        try:
            oled.display()
        except Exception as e:
            print("init display failed: {}".format(e))
            return False

        return True

    def clear(self, refresh: bool = False) -> bool:
        """
        Clear the display:
        refresh =True refresh immediately, refresh=False opposite
        """
        draw = self.__draw
        width = self.__width
        height = self.__height

        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        if refresh:
            try:
                self.refresh()
            except Exception as e:
                print("OLED refresh failed: {}".format(e))
                return False
            else:
                return True
        else:
            # print("not refresh right now")
            pass

    def add_text(self, start_x: int, start_y: int, text: str, refresh: bool = False):
        """
        Add characters:
        start_x start_y indicates the starting point, text is the character to be added,
        refresh =True refresh immediately, refresh=False opposite
        """

        width = self.__width
        height = self.__height

        if start_x > width or start_x < 0 or start_y < 0 or start_y > height:
            print("input () out of display range")
        else:
            x = int(start_x + self.__x)
            y = int(start_y + self.__top)
            self.__draw.text((x, y), str(text), font=self.__font, fill=255)
            if refresh:
                self.refresh()

    # 写入一行字符text。refresh=True立即刷新，refresh=False不刷新。
    # line=[1, 4]
    # Write a line of character text.  Refresh =True Refresh immediately, refresh=False refresh not.
    def add_line(self, text, line=1, refresh=False):
        if line < 1 or line > 4:
            print("oled line input error")
            return
        y = int(8 * (line - 1))
        self.add_text(0, y, text, refresh)

    # 刷新OLED，显示内容
    # Refresh the OLED to display the content
    def refresh(self):
        self.__oled.image(self.__image)
        self.__oled.display()

    # 读取CPU占用率
    # Read the CPU usage rate
    def getCPULoadRate(self, index):
        count = 10
        if index == 0:
            f1 = os.popen("cat /proc/stat", "r")
            stat1 = f1.readline()
            data_1 = []
            for i in range(count):
                data_1.append(int(stat1.split(" ")[i + 2]))
            self.__total_last = (
                data_1[0]
                + data_1[1]
                + data_1[2]
                + data_1[3]
                + data_1[4]
                + data_1[5]
                + data_1[6]
                + data_1[7]
                + data_1[8]
                + data_1[9]
            )
            self.__idle_last = data_1[3]
        elif index == 4:
            f2 = os.popen("cat /proc/stat", "r")
            stat2 = f2.readline()
            data_2 = []
            for i in range(count):
                data_2.append(int(stat2.split(" ")[i + 2]))
            total_now = (
                data_2[0]
                + data_2[1]
                + data_2[2]
                + data_2[3]
                + data_2[4]
                + data_2[5]
                + data_2[6]
                + data_2[7]
                + data_2[8]
                + data_2[9]
            )
            idle_now = data_2[3]
            total = int(total_now - self.__total_last)
            idle = int(idle_now - self.__idle_last)
            usage = int(total - idle)
            usageRate = int(float(usage / total) * 100)
            self.__str_CPU = "CPU:" + str(usageRate) + "%"
            self.__total_last = 0
            self.__idle_last = 0
        return self.__str_CPU

    # 读取系统时间
    # Read system time
    def getSystemTime(self):
        cmd = "date +%H:%M:%S"
        date_time = subprocess.check_output(cmd, shell=True)
        str_Time = str(date_time).lstrip("b'")
        str_Time = str_Time.rstrip("\\n'")
        # print(date_time)
        return str_Time

    # 读取内存占用率 和 总内存
    # Read the memory usage and total memory
    def getUsagedRAM(self):
        cmd = "free | awk 'NR==2{printf \"RAM:%2d%% -> %.1fGB \", 100*($2-$7)/$2, ($2/1048576.0)}'"
        FreeRam = subprocess.check_output(cmd, shell=True)
        str_FreeRam = str(FreeRam).lstrip("b'")
        str_FreeRam = str_FreeRam.rstrip("'")
        return str_FreeRam

    # 读取空闲的内存 / 总内存
    # Read free memory/total memory
    def getFreeRAM(self):
        cmd = "free -h | awk 'NR==2{printf \"RAM: %.1f/%.1fGB \", $7,$2}'"
        FreeRam = subprocess.check_output(cmd, shell=True)
        str_FreeRam = str(FreeRam).lstrip("b'")
        str_FreeRam = str_FreeRam.rstrip("'")
        return str_FreeRam

    # 读取TF卡空间占用率 / TF卡总空间
    # Read the TF card space usage/TOTAL TF card space
    def getUsagedDisk(self):
        cmd = 'df -h | awk \'$NF=="/"{printf "SDC:%s -> %.1fGB", $5, $2}\''
        Disk = subprocess.check_output(cmd, shell=True)
        str_Disk = str(Disk).lstrip("b'")
        str_Disk = str_Disk.rstrip("'")
        return str_Disk

    # 读取空闲的TF卡空间 / TF卡总空间
    # Read the free TF card space/total TF card space
    def getFreeDisk(self):
        cmd = 'df -h | awk \'$NF=="/"{printf "Disk:%.1f/%.1fGB", $4,$2}\''
        Disk = subprocess.check_output(cmd, shell=True)
        str_Disk = str(Disk).lstrip("b'")
        str_Disk = str_Disk.rstrip("'")
        return str_Disk

    # 获取本机IP
    # Read the local IP address
    def getLocalIP(self):
        ip = os.popen("/sbin/ifconfig eth0 | grep 'inet' | awk '{print $2}'").read()
        ip = ip[0 : ip.find("\n")]
        # ip = ''
        if ip == "" or len(ip) > 15:
            ip = os.popen(
                "/sbin/ifconfig wlan0 | grep 'inet' | awk '{print $2}'"
            ).read()
            ip = ip[0 : ip.find("\n")]
            if ip == "":
                ip = "x.x.x.x"
        if len(ip) > 15:
            ip = "x.x.x.x"
        return ip

    # oled主要运行函数，在while循环里调用，可实现热插拔功能。
    # Oled mainly runs functions that are called in a while loop and can be hot-pluggable
    def main_program(self):
        state = False
        try:
            cpu_index = 0
            state = self.init()
            while state:
                self.clear()
                if self.__clear:
                    self.refresh()
                    return True
                str_CPU = self.getCPULoadRate(cpu_index)
                str_Time = self.getSystemTime()
                if cpu_index == 0:
                    str_FreeRAM = self.getUsagedRAM()
                    str_Disk = self.getUsagedDisk()
                    str_IP = "IPA:" + self.getLocalIP()
                self.add_text(0, 0, str_CPU)
                self.add_text(50, 0, str_Time)
                self.add_line(str_FreeRAM, 2)
                self.add_line(str_Disk, 3)
                self.add_line(str_IP, 4)
                # Display image.
                self.refresh()
                cpu_index = cpu_index + 1
                if cpu_index >= 5:
                    cpu_index = 0
                time.sleep(0.1)
            if self.__clear:
                self.__clear_count = self.__clear_count + 1
                if self.__clear_count > len(self.__BUS_LIST):
                    return True
            return False
        except Exception as e:
            print("OLED refresh failed: {}".format(e))
            return False


class Cube(object):
    """Control of peripheral devices such as fans and lights"""

    def __init__(self, i2c_bus_number: int = 1, delay: float = 0.002):
        self.__delay = delay

        if not isinstance(i2c_bus_number, int):
            raise TypeError("i2c_bus_number must be of type int")
        else:
            self.__i2c_bus = smbus2.SMBus(i2c_bus_number)

        self.__i2c_addr = 0x0E
        self.__reg_fan = 0x08
        self.__reg_rgb_effect = 0x04
        self.__reg_rgb_speed = 0x05
        self.__reg_rgb_color = 0x06

    def __del__(self):
        # print("Cube End!")
        pass

    def set_fan(self, state: int):
        """
        Control fan:
        start=0 close, start=1 open
        """

        if not isinstance(state, int):
            raise TypeError("state must be of type int")

        if state > 0:
            state = 1
        else:
            state = 0

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_fan = self.__reg_fan
        delay = self.__delay

        try:
            conn.write_byte_data(i2c_addr, reg_fan, state)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            print("set_fan failed: {}".format(e))

    def set_rgb_effect(self, effect: int):
        """
        Control RGB light effect:
        0 off effect, 1 breathing light, 2 marquee light, 3 rainbow light
        4 dazzling lights, 5 running water lights, 6 circulation breathing lights
        """

        if not isinstance(effect, int):
            raise TypeError("effect must be of type int")

        if effect < 0:
            effect = 0
        elif effect > 6:
            effect = 6

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_effect = self.__reg_rgb_effect
        delay = self.__delay

        try:
            conn.write_byte_data(i2c_addr, reg_rgb_effect, effect)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            print("set_rgb_effect failed: {}".format(e))

    def set_rgb_speed(self, speed: int):
        """
        Set RGB light effect speed:
        1 low speed, 2 medium speed, 3 high speed
        """

        if not isinstance(speed, int):
            raise TypeError("speed must be of type int")

        if speed < 1:
            speed = 1
        elif speed > 3:
            speed = 3

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_speed = self.__reg_rgb_speed
        delay = self.__delay

        try:
            conn.write_byte_data(i2c_addr, reg_rgb_speed, speed)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            print("set_rgb_speed failed: {}".format(e))

    def set_rbg_color(self, color: int):
        """
        Set RGB light effect color:
        0 red, 1 green, 2 blue, 3 yellow, 4 purple, 5 cyan, 6 white
        """

        if not isinstance(color, int):
            raise TypeError("color must be of type int")

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_color = self.__reg_rgb_color
        delay = self.__delay

        if color < 0:
            color = 0
        elif color > 6:
            color = 6

        try:
            conn.write_byte_data(i2c_addr, reg_rgb_color, color)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            print("set_rgb_color failed: {}".format(e))

    def set_single_color(self, index: int, r: int, g: int, b: int):
        """
        Set the individual RGB light color:
        index indicates the serial number of the lamp bead 0-13, index=255 means to control all lamps,
        r stands for red, g stands for green, and b stands for blue
        """

        if not isinstance(index, int):
            raise TypeError("index must be of type int")
        if not isinstance(r, int):
            raise TypeError("r must be of type int")
        if not isinstance(g, int):
            raise TypeError("g must be of type int")
        if not isinstance(b, int):
            raise TypeError("b must be of type int")

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr
        reg_rgb_effect = self.__reg_rgb_effect
        delay = self.__delay

        try:
            # Turn off RGB light effects
            conn.write_byte_data(i2c_addr, reg_rgb_effect, 0)
            if delay > 0:
                time.sleep(delay)
            conn.write_byte_data(i2c_addr, 0x00, index & 0xFF)
            if delay > 0:
                time.sleep(delay)
            conn.write_byte_data(i2c_addr, 0x01, r & 0xFF)
            if delay > 0:
                time.sleep(delay)
            conn.write_byte_data(i2c_addr, 0x02, g & 0xFF)
            if delay > 0:
                time.sleep(delay)
            conn.write_byte_data(i2c_addr, 0x03, b & 0xFF)
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            print("set_single_color failed: {}".format(e))

    def get_Version(self):
        """Obtain the firmware version number"""

        conn = self.__i2c_bus
        i2c_addr = self.__i2c_addr

        conn.write_byte(i2c_addr, 0x00)
        version = conn.read_byte(i2c_addr)
        return version
