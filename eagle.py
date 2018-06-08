from subprocess import call
from PyDE import DE
import socket

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
    s.connect((self.host,port))

    cmdstr = 'aa'
    s.sendall(cmdstr)
    L_str = s.recv(1024)

    L = int(L_str)
    return L


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
    run2()
