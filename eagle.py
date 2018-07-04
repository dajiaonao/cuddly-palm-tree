#!/usr/bin/env python
from subprocess import call
# from PyDE import DE
import socket
# from socket import *
import time

def move(actionList):
    '''call the function to move to the right location'''
    prog = 'D:\PlacProjects\ModuleAssembly\AXIS_C\Debug\AXIS_C.exe'
    for a,v in actionList:
        # Might need some correction to d for hysterresis error
        call([prog, str(a), str(v)])
        
def getL():
    '''Get the strength of the light from TCP/IP'''
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    port = 1024
    host = '192.168.1.10'
    s.connect((host,port))

    cmdstr = 'aa'
    s.sendall(cmdstr)
    L_str = s.recv(1024)

    L = int(L_str)
    return L
def getNx():
    host = '192.168.1.10'
    host_rx = ''
    port = 13141
    addr = (host,port)
    addr_rx = (host_rx,port)
    udpClient = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    udpServer = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    print "A"
    udpServer.bind(addr_rx)
    print "B"
    udpClient.sendto('check',addr)
    print "C"
    bufsize = 1024
    data,addr_r = udpServer.recvfrom(bufsize)
    print(data)

def getN():
    host = "192.168.1.10"
    host_rx = ''
    port = 13141
    addr = (host,port)
    print "A"
    addr_rx = (host_rx,port)
    udpClient = socket(AF_INET,SOCK_DGRAM)
    print "B"
    udpServer = socket(AF_INET,SOCK_DGRAM)
    print "C"
    udpServer.bind(addr_rx)
    print "D"
    udpClient.sendto("check",addr)
    print "F"
    bufsize = 1024
    data,addr_r = udpServer.recvfrom(bufsize)
    print(data)

def funX(x):
    return sum([a**2 for a in x])

class feeder:
    def __init__(self):
        self.nTry = 5

        ## setup the connection
        self.udpClient = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.udpServer = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.addr = None
        self.setupConnection()

    def setupConnection(self):
        host = '192.168.1.10'
        host_rx = ''
        port = 13141
        self.addr = (host,port)
        addr_rx = (host_rx,port)
        self.udpServer.bind(addr_rx)

    def funX(self,x):
        return sum([a**2 for a in x])
    def getL(self):
        bufsize = 1024

        x1 = None
        x2 = None
        ### try nTimes to avoid taking data in transitation
        for i in range(self.nTry):
            self.udpClient.sendto("check",self.addr)
            data,addr_r = self.udpServer.recvfrom(bufsize)
            if x1 is None:
                if data1[0] != '-100.00': x1 = float(data1[0])
            if x2 is None:
                if data1[1] != '-100.00': x2 = float(data1[1])
            if x1 is not None and x2 is not None:
                return x1+x2
        if x1 is None: x1 = -100
        if x2 is None: x2 = -100
        return x1 + x2

    def moveTo(self,x):
        al = []
        for i in range(len(x0)):
            if self.x0[i] != x[i]:
                al.append((i, x[i]-self.x0[i]))
        move(al)
        self.x0 = x

    def funX1(self, x):
        # move to location X
        self.moveTo(x)
        # Get the return value
        return self.getL()


def run():
    x, f = DE(funX, [(-10, 10),(-10,10),(-10,10),(-10,10),(-10,10),(-10,10)]).solve()
    print x,f

def run2():
    from scipy.optimize import minimize
    tt1 = feeder()
    res = minimize(tt1.funX, [1,2,3,4,5,6], method='nelder-mead', options={'xtol': 1e-8, 'disp': True})
    print res['x']
    for x in res['x']:
        print x
#     print dir(res.keys())

def test1():
    move([(4,5),(4,-5)])

def testA():
    tt1 = feeder()

    x, f = DE(ttl.funX1, [(-10, 10),(-10,10),(-10,10),(-10,10),(-10,10),(-10,10)]).solve()
#     from scipy.optimize import minimize
#     res = minimize(tt1.funX, [1,2,3,4,5,6], method='nelder-mead', options={'xtol': 1e-8, 'disp': True})
#     x = res['x']
#     f = res['fun']

    print x,f
    tt1.moveTo(x)
    print "Done."


if __name__ == '__main__':
    print "testing"
#     testA()
    #test1()
    run2()
#     getN()
    #getL()
