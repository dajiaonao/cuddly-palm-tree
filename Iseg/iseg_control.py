#!/usr/bin/env python3
# from __future__ import print_function
import serial
import time
import os
from datetime import datetime, timedelta
import logging

dSuffix = 'project_'

def listPorts():
    import serial.tools.list_ports
    port_list = list(serial.tools.list_ports.comports())
    print(port_list)
    if len(port_list) == 0:
        print('No port avaliable')
    else:
        for i in range(0,len(port_list)):
            print(port_list[i])


def vGen(vList):
    n = len(vList)
    i = 0
    while True:
        yield vList[i]
        i += 1
        if i==n: i-=n

class isegHV:
    def __init__(self):
        self.ser = None
    def connect(self):
#         portx="/dev/ttyUSB1"
        portx="/dev/ttyUSB0"
        bps=9600
        timex=5
        self.ser=serial.Serial(portx,bps,timeout=timex)
    def disconnect(self):
        self.send('*GTL') ## Go To Local
        self.ser.close()

    def send(self, msg, log_cmd=True):
        if log_cmd: logging.info(msg.rstrip())
        if msg[-2:] != '\r\n': msg+='\r\n'
        return self.ser.write(msg.encode("UTF-8"))

    def query(self, cmd, L=1024):
        self.send(cmd, False)
        return self.recv_all(L);
#         return self.recv_all(L).decode();

    def recv_all(self, L=1024):
        ret1 = self.ser.read(L)
        while ret1[-2:] != b'\r\n': ret1 += self.ser.read(L)
        return ret1.rstrip()

    def test0(self):
        self.connect()
        print(self.query('*IDN?'))

    def setV(self, v):
#         print(':VOLTage {0}'.format(v))
        self.send(':VOLTage {0}'.format(v))
        time.sleep(1)
        self.send(':VOLTage ON')
        time.sleep(10)
#         print("turned on")

        ### wait until the ramp is done
        while True:
#             print('getting info')
            tx = self.query(':READ:MODule:STATus?')
#             print('getting status')
            res = int(tx)&(0x7700)
#             print('compare:', tx, int(tx)&(0x7700)) ### see the document for the meaning of this code.
            if res == 0x7700: break
            print('RAMPing...')
            time.sleep(5)

    def getV(self):
        rx = self.query(':READ:VOLTage?')
        print(rx)
        return float(rx[:-1])

    def turnHVOff(self):
        self.send(':VOLTage OFF')

    def test1(self):
        self.connect()
        print(self.query(':READ:IDNT?'))
        print(self.query(':READ:CHANnel:EVent:STATus?'))
#         print(self.query('IDN?'))
#         print(self.send('EVENT:CLEAR'))
#         print(self.query(':READ:CHANnel:EVent:STATus?'))
        print(self.send('*CLS'))
        time.sleep(1)
#         print(self.query(':READ:VOLTage STATus?'))
#         print(self.query(':READ:STATus?'))
        print(self.send(':VOLTage 1.0kV'))
        time.sleep(1)
        print(self.query(':READ:VOLTage?'))
        print(self.send(':VOLTage ON'))
        time.sleep(10)
#         print(self.query(':READ:LAM?'))
        while True:
            tx = self.query(':READ:MODule:STATus?')
            res = int(tx)&(0x7700)
            print('compare:', tx, int(tx)&(0x7700))
            if res == 0x7700: break
            time.sleep(5)

        print(self.query(':MEASURE:VOLTage?'))
        time.sleep(1)
        print(self.send(':VOLTage OFF'))
        time.sleep(1)

#         tx = self.query(':READ:CHANnel:STATus?')
        print(self.query(':READ:CHANnel:EVent:STATus?'))
#         print(self.query(':READ:MODule:STATus?'))
#         print(self.query(':READ:MODule:EVent:STATus?'))
        print(self.query(':MEASURE:VOLTage?'))
#         print(self.query(':READ:EVent:STATus?'))
#         print(self.query(':READ:STATus?'))

    def test(self):
        self.connect()
        print(self.query('*IDN?'))

        self.ser.close()

def test1():
    is1 = isegHV()
#     is1.test0()
    is1.test1()
#     is1.test()

def test2():
    p = vGen([50, 100, 20, 120, 70, 10, 80, 30, 90, 40, 110, 60])

    for i in range(50):
        print(i, next(p))

    t = datetime.now()
    t2 = time.time()
    dT = timedelta(minutes=15)
    tN = t+dT
    print(t,t2,tN)

def simpleSetHV(vs):
    is1 = isegHV()
    is1.connect()
    print(is1.query(':READ:IDNT?'))

    print("Setting voltage to {0}".format(vs))
    is1.send('*CLS')
    time.sleep(2)
    is1.send('EVENT:CLEAR')
    time.sleep(2)
    is1.setV(vs)
    time.sleep(10)

    vs1 = is1.getV()
    print(f"measured V {vs1}")

    is1.disconnect()

if __name__ == '__main__':
    listPorts()
#     test1()
    simpleSetHV(300)
#     simpleSetHV(1000)
#     simpleSetHV(5000)
#     test2()
