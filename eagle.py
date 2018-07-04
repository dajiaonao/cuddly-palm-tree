from subprocess import call
from PyDE import DE
#import socket
from socket import *
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

def funX1(x):
    # move to location X
    moveTo(x)
    # Get the return value
    return getL()

def funX(x):
    return sum([a**2 for a in x])

def run():
    x, f = DE(funX, [(-10, 10),(-10,10),(-10,10),(-10,10),(-10,10),(-10,10)]).solve()
    print x,f

def run2():
    from scipy.optimize import minimize
    res = minimize(funX, [0,0,0,0,0,0], method='nelder-mead', options={'xtol': 1e-8, 'disp': True})
    print res

def test1():
    move([(4,5),(4,-5)])

if __name__ == '__main__':
    print "testing"
    #test1()
    #run2()
    getN()
    #getL()
