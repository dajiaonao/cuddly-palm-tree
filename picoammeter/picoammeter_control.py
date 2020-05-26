#!/usr/bin/env python3
# from __future__ import print_function
import serial
import time
import os,sys
from datetime import datetime, timedelta
import logging
import numpy as np

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

def setIsegV(v):
    from iseg_control import isegHV
    is1 = isegHV()
    is1.connect()
    is1.setV(v)
    is1.ser.close()

def getIsegV():
    from iseg_control import isegHV
    is1 = isegHV()
    is1.connect()
    r = is1.getV()
    is1.ser.close()
    return r

    ### when finish
def turnOffIsegV():
    from iseg_control import isegHV
    is1 = isegHV()
    is1.connect()
    is1.turnHVOff()
    is1.ser.close()

class Picoammeter:
    def __init__(self):
        self.ser = None
    def connect(self, portx="/dev/ttyUSB1"): #USB Serial Converter
#         portx="/dev/ttyUSB0" ##
#         portx="/dev/ttyUSB1"
        bps=57600
        timex=5
        self.ser=serial.Serial(portx,bps,timeout=timex)

    def disconnect(self):
        self.send('SYSTem:LOCal')
        self.ser.close()

    def send(self, msg, log_cmd=True):
        print(msg)
        if log_cmd: logging.info(msg.rstrip())
        if msg[-2:] != '\r\n': msg+='\r\n'
        return self.ser.write(msg.encode("UTF-8"))

    def zero_check(self, doZeroCorr=True):
        '''Perform zero check: 
            Make sure you DUT is not connected!!!!
            The current range should be with in 2.5 nA.
            when making a real measurement, turn off the Zero check first.
            '''
        self.connect()
        self.send('*RST')
        self.send("FUNC 'CURR'")
        self.send('SYST:ZCH ON')

        if doZeroCorr:
            self.send('RANG 2e-9')
            self.send('INIT')
            self.send('SYST:ZCOR:ACQ')
            self.send('SYST:ZCOR ON')

        self.send('RANGE:AUTO ON')
        self.send('SYST:ZCH OFF')
        self.send('INIT')
#         print(self.query('READ?'))
        result = self.ser.read(200)
        print(result.decode())

        self.disconnect()

    def test0(self):
        '''Check if the connection is sucessful'''
        self.connect()
        print(self.query('*IDN?'))
        self.disconnect()

    def test1(self):
        '''Perform a simple current measurement. Taken from the manual'''
        self.connect()
        self.send('*RST')
        self.send("FUNC 'CURR'")
        self.send('SYST:ZCH ON')
        self.send('RANG 2e-9')
        self.send('INIT')
        self.send('SYST:ZCOR:ACQ')
        self.send('SYST:ZCOR ON')
        self.send('RANG:AUTO ON')
        self.send('SYST:ZCH OFF')
        self.send('READ?')

        result = self.ser.read(200)
        print(result)
        print(result.decode())

        self.disconnect()

    def test_simple_measureI(self):
        '''Preform a simple measurement'''
        self.connect()
        print(self.query('*IDN?'))
        self.send('RANG:AUTO ON')
#         self.send('SYST:ZCH OFF')

        self.send("FUNC 'CURR'")
        self.send('FORM:ELEM READ,TIME,VSO')
        ### start the measurement with selecting range and turn off the zero check
#         self.send('RANG:AUTO ON') ### we do not need to set this evry time
#         self.send('SYST:ZCH OFF') ### do not need turn if off if it's already off

        self.send('TRIG:DEL 0')
        self.send('NPLC 0.01') ### 1 PLC means 1 reading per power line cycle

        self.send('TRIG:COUN 100', False)
        
        t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
#         self.send('INIT', False)
#         time.sleep(1)
        q2 = self.query('READ?')
        data = list(zip(*[iter(q2.split(','))]*3))
        print(data)

        vs = 0
        ## pass the values to outx 
        outx = ''
        for d in data: outx += t0 + ' ' + d[0]+' '+d[1]+' '+d[2]+' '+str(vs)+'\n'

        print(outx)
        self.disconnect()
        return


    def multiple_measureI(self):
        '''Preform a simple measurement'''
        self.connect()
        print(self.query('*IDN?'))

        ### start the measurement with selecting range and turn off the zero check
#         self.send('RANG:AUTO ON')
#         self.send('SYST:ZCH OFF')

        ### confiugration
        self.send("FUNC 'CURR'")
        self.send('FORM:ELEM READ,TIME,VSO')

        self.send('TRIG:DEL 0')
        self.send('NPLC 1')

        sampleDir = './'
        dSuffix = 'HV1kV'
        idir = 0
        while os.path.exists(dSuffix+str(idir)): idir+=1
        project_dir = sampleDir+dSuffix+str(idir)+'/'
        os.makedirs(project_dir)

        with open(project_dir+'current.dat','w') as fout1:
            while True:
                try:
                    self.send('TRIG:COUN 100', False)
                    
                    t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
                    self.send('INIT', False)
                    q2 = self.query('READ?')
                    data = list(zip(*[iter(q2.split(','))]*3))

                    vs = 0
                    ## pass the values to outx 
                    outx = ''
                    for d in data: outx += t0 + ' ' + d[0]+' '+d[1]+' '+d[2]+' '+str(vs)+'\n'

                    ## write out outx
                    fout1.write(outx)
                    fout1.flush()
                except KeyboardInterrupt:
                    break
        ### finish
        self.disconnect()
        return

    def speed_check(self):
        self.send('FORM:ELEM READ,TIME')
        self.send('SYST:ZCH OFF')

        for i in range(20):
            self.send('TRIG:COUN 20')
            self.send('TRAC:POIN 20')
            self.send('TRAC:FEED SENS')
            self.send('TRAC:FEED:CONT NEXT')
            print(datetime.now(), i)
            self.send('INIT')
            ret = self.query('TRAC:DATA?',4096)
            print(ret)
 
    def read_many(self):
#         self.send('*RST')
        self.send('TRIG:DEL 0')
        self.send('TRIG:COUN 2000')
        self.send('NPLC .01')
#         self.send('RANG .002')
        self.send('SYST:ZCH OFF')
        self.send('SYST:AZER:STAT OFF')
        self.send('DISP:ENAB OFF')
        self.send('*CLS')
        self.send('TRAC:POIN 2000')
        self.send('TRAC:CLE')
        self.send('TRAC:FEED:CONT NEXT')
        self.send('STAT:MEAS:ENAB 512')
        self.send('*SRE 1')
        q1 = self.query('*OPC?')
        print(q1)

        self.send('INIT')
        self.send('DISP:ENAB ON')
        q2 = self.query('TRAC:DATA?')
        print(q2)

    def test(self):
        self.connect()
        print(self.query('*IDN?'))

        self.send('*CLS')
        self.send('*RST')
        return
#         self.test1()
        self.send("FUNC 'CURR'")
#         self.speed_check()
#         self.read_many()
#         self.run_measure()
        self.take_data()
#         self.run_measure1()
#         self.test_get_mean()
#         self.multiple_reading()
#         self.set_relative()
        self.ser.close()

    def set_relative(self): 
        self.send('READ?')
        ret1 = self.ser.read(200)
        print(ret1.decode())

        self.send('CALC2:NULL:OFFS 1e-6')
        self.send('CALC2:NULL:STAT ON')
        self.send('SYST:ZCH OFF')
        self.send('INIT')
        self.send('CALC2:DATA?')
        ret1 = self.ser.read(200)
        print(ret1.decode())

        self.send('READ?')
        ret1 = self.ser.read(200)
        print(ret1.decode())

    def multiple_reading(self):
        self.send('ARM:SOUR IMM')
        self.send('ARM:COUN 1')
        self.send('TRIG:SOUR IMM')
        self.send('TRIG:COUN 10')
        self.send('SYST:ZCH OFF')

        for i in range(10):
            self.send('READ?')

            ret1 = self.ser.read(1024)
            while ret1[-2:] != b'\r\n':
#                 print(ret1)
                ret1 += self.ser.read(1024)
            ret1 = ret1.rstrip()
            data = list(zip(*[iter(ret1.split(b','))]*3))

            values = [float(x[0][:-1]) for x in data]
            print(values)

    def query(self, cmd, L=1024):
        self.send(cmd, False)
        return self.recv_all(L).decode();

    def recv_all(self, L=1024):
        ret1 = self.ser.read(L)
#         print(ret1,'||||') ### for debug
        while ret1[-2:] != b'\r\n': ret1 += self.ser.read(L)
        return ret1.rstrip()

    def test_get_mean(self):
        self.send('FORM:ELEM READ,TIME')
        self.send('TRIG:COUN 20')
        self.send('TRAC:POIN 20')
        self.send('TRAC:FEED SENS')
        self.send('TRAC:FEED:CONT NEXT')
        self.send('SYST:ZCH OFF')
        self.send('INIT')
        print(self.query('TRAC:DATA?'))

        self.send('CALC3:FORM MEAN')
        print(self.query('CALC3:DATA?'))


    def run_measure_tes2(self):
        self.send('FORM:ELEM READ,TIME')
        self.send('TRIG:COUN 20')
        self.send('TRAC:POIN 20')
        self.send('TRAC:FEED SENS')
        self.send('TRAC:FEED:CONT NEXT')
        self.send('SYST:ZCH OFF')
        self.send('INIT')
#         print(self.query('TRAC:DATA?'))

        self.send('CALC3:FORM MEAN')
        print(self.query('CALC3:DATA?'))

    def run_measure0(self):
        ### setup the zero correction
        self.send('SYST:ZCH ON')
        self.send('RANG 2e-9')
        self.send('INIT')
        self.send('SYST:ZCOR:ACQ')
        self.send('SYST:ZCOR ON')
        self.send('RANG:AUTO ON')
#         self.send('RANG: 200e-9')
        self.send('SYST:ZCH OFF')

        ### HV
        self.send('SOUR:VOLT:RANG 10') #Select 10V source range.
        self.send('SOUR:VOLT 10') #  Set voltage source output to 10V.
        self.send('SOUR:VOLT:ILIM 2.5e-3') #  Set current limit to 2.5mA.
        self.send('SOUR:VOLT:STAT ON') # Put voltage source in operate.

        ### take data
        self.send('FORM:ELEM READ,VSO,TIME')
        self.send('TRIG:DEL 0')
#         self.send('NPLC .01')
        self.send('NPLC 1')
        self.send('SYST:AZER:STAT OFF')
#         self.send('DISP:ENAB OFF')
#         self.send('*CLS')
#         self.send('STAT:MEAS:ENAB 512')
#         self.send('*SRE 1')
#         q1 = self.query('*OPC?')
#         print(q1)

#         time.sleep(3)
        sampleDir = './'
        idir = 0
        while os.path.exists(dSuffix+str(idir)): idir+=1
        project_dir = sampleDir+dSuffix+str(idir)+'/'
        os.makedirs(project_dir)

        with open(project_dir+'current.dat','w') as fout1:
            isample = 0
            while True:
                isample += 1
#              for t in range(3):
                t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
                try:
                    self.send('TRIG:COUN 100')
                    self.send('TRAC:POIN 100')
                    self.send('TRAC:CLE')
                    self.send('TRAC:FEED:CONT NEXT')
                    q1 = self.query('*OPC?')
                    print(q1)
                    self.send('INIT')

                    q2 = self.query('TRAC:DATA?')

                    data = list(zip(*[iter(q2.split(','))]*3))
                    outx = ''
                    for d in data: outx += t0 + ' ' + d[0]+' '+d[1]+' '+d[2]+'\n'

#                     print(outx)
                    fout1.write(outx)
                    fout1.flush()

                except KeyboardInterrupt:
                    break
                print(isample, 'done')
        self.send('TRAC:CLE')
        print('done')

    def run_measure1(self):
        '''The function used in project 41-44, save before implimenting other functions'''
        ### HV
        self.send('SOUR:VOLT:RANG 500') #Select 10V source range.
        self.send('SOUR:VOLT -150') #  Set voltage source output to 10V.
        self.send('SOUR:VOLT:ILIM 2.5e-3') #  Set current limit to 2.5mA.
        self.send('SOUR:VOLT:STAT ON') # Put voltage source in operate.
        
        ### setup the zero correction
        self.send('SYST:ZCH ON')
#         self.send('RANG 2e-9')
#         self.send('INIT')
#         self.send('SYST:ZCOR:ACQ')
#         self.send('SYST:ZCOR ON')
#         self.send('RANG:AUTO ON')
        self.send('RANG 2e-9')
        self.send('SYST:ZCH OFF')

        ### take data
        self.send('FORM:ELEM READ,VSO,TIME')
        self.send('TRIG:DEL 0')
        self.send('NPLC 1')
#        self.send('SYST:AZER:STAT OFF')

        ### location
        sampleDir = './'
        idir = 0
        while os.path.exists(dSuffix+str(idir)): idir+=1
        project_dir = sampleDir+dSuffix+str(idir)+'/'
        os.makedirs(project_dir)
        logging.basicConfig(filename=project_dir+'run.log',level=logging.DEBUG)

        with open(project_dir+'current.dat','w') as fout1:
            isample = 0
            while True:
                isample += 1
                t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
                try:
                    self.send('TRIG:COUN 100')
                    self.send('INIT')
                    q2 = self.query('READ?')

                    data = list(zip(*[iter(q2.split(','))]*3))
                    outx = ''
                    for d in data: outx += t0 + ' ' + d[0]+' '+d[1]+' '+d[2]+'\n'

                    fout1.write(outx)
                    fout1.flush()

                except KeyboardInterrupt:
                    break

#                 self.check_new_orders()

                print(isample, 'done')
        print('done')

    def take_data(self):
        ### HV
        self.send('SOUR:VOLT:RANG 500') #Select 10V source range.
        self.send('SOUR:VOLT -500') #  Set voltage source output to 10V.
        self.send('SOUR:VOLT:ILIM 2.5e-3') #  Set current limit to 2.5mA.
        self.send('SOUR:VOLT:STAT ON') # Put voltage source in operate.

        self.send('SYST:ZCH ON')
        self.send('RANG 2e-9')
        self.send('SYST:ZCH OFF')

         ### take data
        self.send('FORM:ELEM READ,VSO,TIME')
        self.send('TRIG:DEL 0')
        self.send('NPLC 1')

        ### location
        sampleDir = './'
        idir = 0
        while os.path.exists(dSuffix+str(idir)): idir+=1
        project_dir = sampleDir+dSuffix+str(idir)+'/'
        os.makedirs(project_dir)
        logging.basicConfig(filename=project_dir+'run.log',level=logging.DEBUG)

        ### start taking data
        with open(project_dir+'current.dat','w') as fout1:
            isample = 0
            while True:
                isample += 1
                t = time.time()

                t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(t))
                try:
                    self.send('TRIG:COUN 100', False)
                    self.send('INIT', False)
                    q2 = self.query('READ?')

                    data = list(zip(*[iter(q2.split(','))]*3))
                    outx = ''
                    for d in data: outx += t0 + ' ' + d[0]+' '+d[1]+' '+d[2]+'\n'

                    fout1.write(outx)
                    fout1.flush()

                except KeyboardInterrupt:
                    break

                print(isample, 'done')
        print('done')

    def run_measure(self):
        ### HV
        self.send('SOUR:VOLT:RANG 500') #Select 10V source range.
#         self.send('SOUR:VOLT -100') #  Set voltage source output to 10V.
        self.send('SOUR:VOLT:ILIM 2.5e-3') #  Set current limit to 2.5mA.
        self.send('SOUR:VOLT:STAT ON') # Put voltage source in operate.
        
        ### setup the zero correction
        self.send('SYST:ZCH ON')
#         self.send('RANG 2e-9')
#         self.send('INIT')
#         self.send('SYST:ZCOR:ACQ')
#         self.send('SYST:ZCOR ON')
#         self.send('RANG:AUTO ON')
        self.send('RANG 2e-9')
        self.send('SYST:ZCH OFF')

        ### take data
        self.send('FORM:ELEM READ,VSO,TIME')
        self.send('TRIG:DEL 0')
        self.send('NPLC 1')
#        self.send('SYST:AZER:STAT OFF')

        t2 = 0.
        dT = 15*60 ## 15 min

        ### location
        sampleDir = './'
        idir = 0
        while os.path.exists(dSuffix+str(idir)): idir+=1
        project_dir = sampleDir+dSuffix+str(idir)+'/'
        os.makedirs(project_dir)
        logging.basicConfig(filename=project_dir+'run.log',level=logging.DEBUG)


        ### list of V on the plane to be scaned
        plateV = vGen([0,-120,0, -50,0, -100,0, -20,0, -70,0, -10,0, -80,0, -30,0, -90,0, -40,0, -110,0, -60])

        ### start taking data
        with open(project_dir+'current.dat','w') as fout1:
            isample = 0
            while True:
                isample += 1
                t = time.time()

                ### check if time to switch to next voltage
                if t>t2:
                    ### time to change the voltage
                    vs = next(plateV)
                    self.send('SOUR:VOLT {0:d}'.format(vs)) #  Set voltage source output to 10V.
                    t2 = t+dT

                t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(t))
                try:
                    self.send('TRIG:COUN 100', False)
                    self.send('INIT', False)
                    q2 = self.query('READ?')

                    data = list(zip(*[iter(q2.split(','))]*3))
                    outx = ''
                    for d in data: outx += t0 + ' ' + d[0]+' '+d[1]+' '+d[2]+'\n'

                    fout1.write(outx)
                    fout1.flush()

                except KeyboardInterrupt:
                    break

#                 self.check_new_orders()

                print(isample, 'done')
        print('done')

    def check_new_orders(self):
        order_file = 'picoam_control/cmd'
        if not os.path.exist(orderfile): return

        orders = []
        with open(order_file) as f1:
            orders = [line.rstrip() for line in f1.readlines()]

        for order in orders:
            self.send(order)

    def run_measure_test(self):
        self.send('ARM:SOUR IMM')
        self.send('ARM:COUN 1')
        self.send('TRIG:SOUR IMM')
        self.send('TRIG:COUN 10')
        self.send('SYST:ZCH OFF')

        with open('current.dat','w') as fout1:
            while True:
                try:
                    self.send('READ?')

                    ret1 = self.ser.read(1024)
                    while ret1[-2:] != b'\r\n':
                        ret1 += self.ser.read(1024)
                    ret1 = ret1.rstrip()
                    data = list(zip(*[iter(ret1.split(b','))]*3))

                    values = [float(x[0][:-1]) for x in data]
                    fout1.write(time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))+' '+str(values[0])+'\n')
                    fout1.flush()

                except KeyboardInterrupt:
                    break

def test_measure():
    try:
        portx="/dev/ttyUSB0"
        bps=115200
        timex=5
        ser=serial.Serial(portx,bps,timeout=timex)
        print(ser)

        result=ser.write("*RST".encode("UTF-8"))
        print("return",result)

        ser.close()

    except Exception as e:
        print("Somthing wrong",e)


def measureR():
    '''Standard Ohms measurement in the manual'''
    pm1 = Picoammeter()
    pm1.connect()
    pm1.send('*RST')
    pm1.send('FORM:ELEM READ,UNIT')
    pm1.send('SYST:ZCH ON')
    pm1.send('RANG 2e-9')
    pm1.send('INIT')

    pm1.send('SYST:ZCOR:ACQ')
    pm1.send('SYST:ZCOR ON')
    pm1.send('RANG:AUTO ON')
    pm1.send('SOUR:VOLT:RANG 10')
    pm1.send('SOUR:VOLT 10')
    pm1.send('SOUR:VOLT:ILIM 2.5e-3')
    pm1.send('SENS:OHMS ON')
    pm1.send('SOUR:VOLT:STAT ON')
    pm1.send('SYST:ZCH OFF')

    r = pm1.query('READ?')

    print(r)

def isGoodData(data, debug=False):
    values = [float(d[0]) for d in data]
    mean = np.mean(values)
    std = np.std(values)

#     print(mean, std, mean-std, mean+std, np.mean(values[:3]), np.mean(values[-3:]))
    if debug: print(mean, std, mean-std, mean+std, np.mean(values[:3]), np.mean(values[-3:]), (np.mean(values[:3])-mean)/std, (np.mean(values[-3:])-mean)/std)

    return mean-std < np.mean(values[:3]) < mean+std and mean-std < np.mean(values[-3:]) < mean+std

def measureI_autoScanIseg():
    '''Make a measurement of current interactively, save the given voltage as well'''
    ## give the file name
    fname = sys.argv[1] if len(sys.argv)>1 else input('Input the file name to be saved to:')
    while os.path.exists(fname): fname = input('Already exist, try anohter one:')

    pm1 = Picoammeter()
    pm1.connect()
    print(pm1.query('*IDN?'))
    pm1.send('*RST')
    pm1.send('FORM:ELEM READ,TIME,VSO')
    pm1.send("FUNC 'CURR'")
#     pm1.send('SYST:ZCH ON')
#     pm1.send('RANG 2e-9')
#     pm1.send('INIT')

#     pm1.send('SYST:ZCOR:ACQ')
    pm1.send('SYST:ZCOR ON')
    pm1.send('RANG:AUTO ON')
    pm1.send('TRIG:DEL 0')
    pm1.send('NPLC 1')

    pm1.send('SYST:ZCH OFF')
#     pm1.send('DISP:ENAB ON')
#     pm1.send('SYSTem:LOCal')
#     pm1.ser.close()

    ### also start the Iseg control
    from iseg_control import isegHV
    is1 = isegHV()
    is1.connect()
    print(is1.query(':READ:IDNT?'))

    ## Start taking data
    with open(fname,'w') as fout1:
#         for vs in [100,200,300,400,500,700,1000,1500,2000,2500,3000,3500,4000,0,4500,5000,5500,6000,6500,7000,7500,8000]:
        for vs in [5000,100,6000,300,2500,700,5500,1000,3000,7000,3500,400,4000,0,4500,200,6500,1500,7500,2000,500,8000]:
#         for vs in [5000,5500,6000,6500,7000,7500,8000]:
#         for vs in [300,500]:
            try:
                ### set voltage
                print("Setting voltage to {0}".format(vs))
                is1.send('*CLS')
                time.sleep(2)
                is1.send('EVENT:CLEAR')
                time.sleep(2)
                is1.setV(vs)
                time.sleep(10)

                ### measure current
                outx = ''
                while outx == '':
                    ## perform a measurement
                    pm1.send('TRIG:COUN 100', False)
                    
                    t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
                    pm1.send('INIT', False)
                    q2 = pm1.query('READ?')
                    data = list(zip(*[iter(q2.split(','))]*3))

                    ## check the stablitly. If not good: wait and continue
                    if not isGoodData(data):
                        print("bad data, will try again")
                        time.sleep(10)
                        continue
                   
                    time.sleep(2)
                    vs1 = is1.getV()
                    print(f"measured V {vs1}")
                    time.sleep(2)
#                     is1.turnHVOff()
#                     time.sleep(10)
                    ## pass the values to outx 
                    for d in data: outx += t0 + ' ' + d[0]+' '+d[1]+' '+d[2]+' '+str(vs)+' '+str(vs1)+'\n'

                ## write out outx
                fout1.write(outx)
                fout1.flush()
            except KeyboardInterrupt:
                break

        ## finish gracefully
        is1.turnHVOff()
        pm1.send('SYSTem:LOCal')
        pm1.ser.close()

def measureI_autoScan():
    '''Make a measurement of current interactively, save the given voltage as well'''
    ## give the file name
    fname = sys.argv[1] if len(sys.argv)>1 else input('Input the file name to be saved to:')
    while os.path.exists(fname): fname = input('Already exist, try anohter one:')

    pm1 = Picoammeter()
    pm1.connect()
    print(pm1.query('*IDN?'))
    pm1.send('*RST')
    pm1.send('FORM:ELEM READ,TIME,VSO')
    pm1.send("FUNC 'CURR'")
    pm1.send('SYST:ZCH ON')
    pm1.send('RANG 2e-9')
    pm1.send('INIT')

    pm1.send('SYST:ZCOR:ACQ')
    pm1.send('SYST:ZCOR ON')
    pm1.send('RANG:AUTO ON')
    pm1.send('TRIG:DEL 0')
    pm1.send('NPLC 1')

    pm1.send('SOUR:VOLT:RANG 500')
    pm1.send('SOUR:VOLT 10')
    pm1.send('SOUR:VOLT:ILIM 2.5e-3')
#     pm1.send('SOUR:VOLT:STAT ON')

    pm1.send('SYST:ZCH OFF')
#     pm1.send('DISP:ENAB ON')
#     pm1.send('SYSTem:LOCal')
#     pm1.ser.close()

    ## Start taking data
    with open(fname,'w') as fout1:
        for vs in [-500,-400,-300,-200,-100,0,100,200,300,400,500]:
            try:
                ### set voltage
                print("Setting voltage to {0}".format(vs))
                pm1.send('SOUR:VOLT {0}'.format(vs))
                pm1.send('SOUR:VOLT:STAT ON')

                ### measure current
                outx = ''
                while outx == '':
                    ## perform a measurement
                    pm1.send('TRIG:COUN 100', False)
                    
                    t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
                    pm1.send('INIT', False)
                    q2 = pm1.query('READ?')
                    data = list(zip(*[iter(q2.split(','))]*3))

                    ## check the stablitly. If not good: wait and continue
                    if not isGoodData(data):
                        print("bad data, will try again")
                        time.sleep(10)
                        continue
                    
                    pm1.send('SOUR:VOLT:STAT OFF')
                    ## pass the values to outx 
                    for d in data: outx += t0 + ' ' + d[0]+' '+d[1]+' '+d[2]+' '+str(vs)+'\n'

                ## write out outx
                fout1.write(outx)
                fout1.flush()
            except KeyboardInterrupt:
                break

        ## finish gracefully
        pm1.send('SYSTem:LOCal')
#         pm1.ser.close()

def measureI_interactively():
    '''Make a measurement of current interactively, save the given voltage as well'''
    ## give the file name
    fname = sys.argv[1] if len(sys.argv)>1 else input('Input the file name to be saved to:')
    while os.path.exists(fname): fname = input('Already exist, try anohter one:')

    pm1 = Picoammeter()
    pm1.connect()
    print(pm1.query('*IDN?'))
    pm1.send('*RST')
    pm1.send('FORM:ELEM READ,TIME,VSO')
    pm1.send("FUNC 'CURR'")
    pm1.send('SYST:ZCH ON')
    pm1.send('RANG 2e-9')
    pm1.send('INIT')

    pm1.send('SYST:ZCOR:ACQ')
    pm1.send('SYST:ZCOR ON')
    pm1.send('RANG:AUTO ON')
    pm1.send('TRIG:DEL 0')
    pm1.send('NPLC 1')

    pm1.send('SOUR:VOLT:RANG 500')
    pm1.send('SOUR:VOLT 10')
    pm1.send('SOUR:VOLT:ILIM 2.5e-3')
    pm1.send('SOUR:VOLT:STAT ON')

    pm1.send('SYST:ZCH OFF')
#     pm1.send('DISP:ENAB ON')
    pm1.send('SYSTem:LOCal')
    pm1.ser.close()

    ## Start taking data
    with open(fname,'w') as fout1:
        while True:
            ### get the input voltage first
            try:
                vs = input('Voltage value:')
                vsx = vs.rstrip()
                pm1.connect()
                print(vsx, vsx[-1])
                if vsx[-1]=='L':
                    vs = vsx[:-1]
                    print("Setting voltage to {0}".format(vs))
                    pm1.send('SYSTem:REMote')
                    pm1.send('SOUR:VOLT {0}'.format(vs))
                    pm1.send('SYSTem:LOCal')
                    temp = input('Start:')
#                 pm1.send('SYSTem:REMote')
            except KeyboardInterrupt:
                break

            outx = ''
            while outx=='':
                pm1.send('TRIG:COUN 100', False)
                
                t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
                pm1.send('INIT', False)
                q2 = pm1.query('READ?')
                print("waiting for data")

                data = list(zip(*[iter(q2.split(','))]*3))

                if not isGoodData(data):
                    time.sleep(10)
                    continue

                for d in data: outx += t0 + ' ' + d[0]+' '+d[1]+' '+d[2]+' '+vs+'\n'
            fout1.write(outx)
            fout1.flush()
#             print(outx)

            pm1.send('SYSTem:LOCal')
            pm1.ser.close()


def measureR1():
    '''Based on measureR, added: 1) more info in output; 2) multiple reading'''
    pm1 = Picoammeter()
    pm1.connect()
    pm1.send('*RST')
    pm1.send('FORM:ELEM READ,UNIT,TIME,VSO,TIME')
    pm1.send('SYST:ZCH ON')
    pm1.send('RANG 2e-9')
    pm1.send('INIT')

    pm1.send('SYST:ZCOR:ACQ')
    pm1.send('SYST:ZCOR ON')
    pm1.send('RANG:AUTO ON')
    pm1.send('SOUR:VOLT:RANG 10')
    pm1.send('SOUR:VOLT 10')
    pm1.send('SOUR:VOLT:ILIM 2.5e-6')
    pm1.send('SENS:OHMS ON')
    pm1.send('SOUR:VOLT:STAT ON')
#     pm1.send('SYST:ZCH OFF')

    pm1.send('TRIG:DEL 0')
    pm1.send('NPLC 1')
    pm1.send('TRIG:COUN 100', False)
    pm1.send('TRAC:POIN 100')
    pm1.send('TRAC:CLE')
    pm1.send('TRAC:FEED SENS')
    pm1.send('TRAC:FEED:CONT NEXT')
    pm1.send('SYST:ZCH OFF')
    
    t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
    pm1.send('INIT', False)

#     r = pm1.query('READ?')
#     print(r)
#     q2 = pm1.query('READ?')
    q2 = pm1.query('TRAC:DATA?')

    data = list(zip(*[iter(q2.split(','))]*3))
    outx = ''
    for d in data: outx += t0 + ' ' + d[0]+' '+d[1]+' '+d[2]+'\n'
    print(outx)

def run_tests():
    pm1 = Picoammeter()
#     pm1.test0()
    pm1.test1()
#     pm1.zero_check()
#     pm1.test_simple_measureI()
#     pm1.multiple_measureI()


def test2():
    p = vGen([50, 100, 20, 120, 70, 10, 80, 30, 90, 40, 110, 60])

    for i in range(50):
        print(i, next(p))

    t = datetime.now()
    t2 = time.time()
#     dT = timedelta(minutes=15)
    dT = timedelta(seconds=5)
    tN = t+dT
    print(t,t2,tN)
    while datetime.now()<tN: time.sleep(1)
    print(tN, datetime.now())

def IsegHVOperationDrill0():
    while True: ### to lazy to indent following lines
        for vs in [0,100,200,300,400,500,700,1000,1500,2000,2500,3000,3500,4000,4500,5000,5500,6000,6500,7000,7500,8000]:
            try:
                print("Setting voltage to {0}".format(vs))
                setIsegV(vs*0.001)
                time.sleep(20)

                if True:
                    vs1 = getIsegV()
                    print(f"get to {vs1}")
                    time.sleep(5)
                    turnOffIsegV()
 
            except KeyboardInterrupt:
                break

        ## finish gracefully
        turnOffIsegV()

        break

def IsegHVOperationDrill():
    from iseg_control import isegHV
    is1 = isegHV()
    is1.connect()
    print(is1.query(':READ:IDNT?'))

    while True: ### to lazy to indent following lines
        for vs in [800,100,200,300,400,500,700,1000,1500,2000,2500,3000,3500,4000,4500,5000,5500,6000,6500,7000,7500,8000]:
            try:
                print("Setting voltage to {0}".format(vs))
                is1.setV(vs)
                time.sleep(10)

                if True:
                    vs1 = is1.getV()
                    print(f"get to {vs1}")
                    time.sleep(5)
                    is1.turnHVOff()
                    time.sleep(1)
 
            except KeyboardInterrupt:
                break

        ## finish gracefully
        is1.turnHVOff()
        break

def HV_out_scan(vlist, dT):
    pm1 = Picoammeter()
    pm1.connect()
    pm1.send('SOUR:VOLT:RANG 500') #Select 10V source range.
    pm1.send('SOUR:VOLT 500') #  Set voltage source output to 500V.
    pm1.send('SOUR:VOLT:ILIM 2.5e-4') #  Set current limit to 25uA.
    pm1.send('SOUR:VOLT:STAT ON') # Put voltage source in operate.

    vl = vGen(vlist)
    while True:
        ### time to change the voltage
        try:
            vs = next(vl)
            pm1.send('SOUR:VOLT {0:d}'.format(vs)) #  Set voltage source output to 10V.
            time.sleep(dT)
            print(time.time(), vs)
        except KeyboardInterrupt:
            break

def run_quasicontinious_recording(filename, nRead=-1, tLast=None, extraStr=''):
    rCode = 0
    pm1 = Picoammeter()
    pm1.connect()
    print(pm1.query('*IDN?'))

    ### confiugration
    pm1.send("FUNC 'CURR'")
    pm1.send('FORM:ELEM READ,TIME,VSO')

    pm1.send('TRIG:DEL 0')
    pm1.send('NPLC 1')

    tEnd = None
    if tLast is not None:
        dT = timedelta(seconds=tLast)
        tEnd = datetime.now() + dT

    iGood = 0
    iData = 0
    with open(filename,'w') as fout1:
        while True:

            ### check time requirement.
            if tEnd and datetime.now() > tEnd: break
            if iData == nRead: break

            try:
                pm1.send('TRIG:COUN 100', False)
                
                t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
                pm1.send('INIT', False)
                q2 = pm1.query('READ?')
                data = list(zip(*[iter(q2.split(','))]*3))

                isGood = 0 
                if isGoodData(data):
                    isGood = 1
                    iGood += 1
                    print(f"Number of good dataset: {iGood}")

                ## pass the values to outx 
                outx = ''
                for d in data: outx += ' '.join([t0,d[0],d[1],d[2],str(isGood),str(iGood),str(iData)]) + extraStr +'\n'

                ## write out outx
                fout1.write(outx)
                fout1.flush()
                iData += 1
            except KeyboardInterrupt:
                rCode = 1
                break
    ### finish
    pm1.disconnect()
    return rCode


def HV_checkI(HVvalue, nGood=3, tLast=30):
    '''The function is used to check the repeatbiltiy and stablility of the HV.
    When a HV value is given as argument, this function will try to set the HV source to HVvalue'''
    rCode = 0 # 0: OK; 1:interruput signal, should stop at higher level
    dT = timedelta(seconds=tLast)

    pm1 = Picoammeter()
    pm1.connect()
    print(pm1.query('*IDN?'))

    ### confiugration
    pm1.send("FUNC 'CURR'")
    pm1.send('FORM:ELEM READ,TIME,VSO')

    pm1.send('TRIG:DEL 0')
    pm1.send('NPLC 1')

    ### setup the ouput directory and filename
    HVstr = 'HV{0}'.format(HVvalue)
    sampleDir = './'
    project_dir = sampleDir+HVstr
    if not os.path.exists(project_dir): os.makedirs(project_dir)
    ifile, filename = 0, project_dir + '/' + HVstr + '_current_0.dat'
    while os.path.exists(filename): ifile, filename = ifile+1, project_dir + '/' + HVstr + '_current_{0:d}.dat'.format(ifile)

    ### setup HV from the Iseg control
    from iseg_control import isegHV
    is1 = isegHV()
    is1.connect()
    print(is1.query(':READ:IDNT?'))

    ### set to the given value
    ### set voltage
    print("Setting voltage to {0}".format(HVvalue))
    is1.send('*CLS')
    time.sleep(2)
    is1.send('EVENT:CLEAR')
    time.sleep(2)
    is1.setV(HVvalue)
 
    ### start taking data
    tEnd = None
    iGood = 0
    iData = 0
    with open(filename,'w') as fout1:
        while True:
            ### check time requirement.
            if tEnd and datetime.now() > tEnd: break

            try:
                pm1.send('TRIG:COUN 100', False)
                
                t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
                pm1.send('INIT', False)
                q2 = pm1.query('READ?')
                data = list(zip(*[iter(q2.split(','))]*3))

                isGood = 0 
                if isGoodData(data):
                    isGood = 1
                    iGood += 1
                    print(f"Number of good dataset: {iGood}")
                    if iGood >= nGood and tEnd is None: 
                        tEnd = datetime.now() + dT
                        print(f'Will stop taking this dataset at {tEnd}')

                vs1 = is1.getV()
                print(f"measured V {vs1}")
                time.sleep(2)

                ## pass the values to outx 
                outx = ''
                for d in data: outx += ' '.join([t0,d[0],d[1],d[2],str(HVvalue),str(vs1),str(isGood),str(iGood),str(iData)]) +'\n'

                ## write out outx
                fout1.write(outx)
                fout1.flush()
                iData += 1
            except KeyboardInterrupt:
                rCode = 1
                break
    ### finish
    pm1.disconnect()

    ## turn off HV
    is1.turnHVOff()
    time.sleep(10)
    is1.disconnect()
    return rCode

def run_zero_check():
    pm1 = Picoammeter()
    pm1.zero_check()

def run_HV_checkI():
    for i in range(5): 
        if HV_checkI(8000): break
        time.sleep(10)

def run_HV_checkI_Dongwen():
    for i in range(5): 
#         if HV_checkI_Dongwen(1000): break
#         if HV_checkI_Dongwen(5000): break
        if HV_checkI_Dongwen(8000): break
        time.sleep(10)

def HV_checkI_Dongwen(HVvalue, nGood=3, tLast=60):
    '''The function is used to check the repeatbiltiy and stablility of the Dongwen HV device.
    This need to be done interactively: 1) set the value at the begining and 2) check the value when it's stable.'''
    rCode = 0 # 0: OK; 1:interruput signal, should stop at higher level
    dT = timedelta(seconds=tLast)

    pm1 = Picoammeter()
    pm1.connect()
    print(pm1.query('*IDN?'))

    ### confiugration
    pm1.send("FUNC 'CURR'")
    pm1.send('FORM:ELEM READ,TIME,VSO')

    pm1.send('TRIG:DEL 0')
    pm1.send('NPLC 1')

    ### setup the ouput directory and filename
    HVstr = 'DongwenHV{0}'.format(HVvalue)
    sampleDir = './'
    project_dir = sampleDir+HVstr
    if not os.path.exists(project_dir): os.makedirs(project_dir)
    ifile, filename = 0, project_dir + '/' + HVstr + '_current_0.dat'
    while os.path.exists(filename): ifile, filename = ifile+1, project_dir + '/' + HVstr + '_current_{0:d}.dat'.format(ifile)

    vs1 = input(f"Set the value to {HVvalue} now:")

    print(f"HV vlaue {vs1} confirmed")

    ### start taking data
    tEnd = None
    iGood = 0
    iData = 0
    with open(filename,'w') as fout1:
        while True:
            ### check time requirement.
            if tEnd and datetime.now() > tEnd: break

            try:
                pm1.send('TRIG:COUN 100', False)
                
                t0 = time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime(time.time()))
                pm1.send('INIT', False)
                q2 = pm1.query('READ?')
                data = list(zip(*[iter(q2.split(','))]*3))

                isGood = 0 
                if isGoodData(data):
                    isGood = 1
                    iGood += 1
                    print(f"Number of good dataset: {iGood}")
                    if iGood >= nGood and tEnd is None: 
                        vs1 = input("Check the vlue now:")
                        print(f"measured V {vs1}")
                        time.sleep(2)
                        tEnd = datetime.now() + dT
                        print(f'Will stop taking this dataset at {tEnd}')

                ## pass the values to outx 
                outx = ''
                for d in data: outx += ' '.join([t0,d[0],d[1],d[2],str(HVvalue),str(vs1),str(isGood),str(iGood),str(iData)]) +'\n'

                ## write out outx
                fout1.write(outx)
                fout1.flush()
                iData += 1
            except KeyboardInterrupt:
                rCode = 1
                break
    ### finish
    pm1.disconnect()
    return rCode


if __name__ == '__main__':
    listPorts()
#     run_tests()
#     run_HV_checkI()
#     run_zero_check()
#     run_HV_checkI_Dongwen()
#     run_quasicontinious_recording('DongwenHV8000/DongwenHV8000_long1.dat',extraStr=" 8000 8000")
    run_quasicontinious_recording('A_TestMay22/HV1000_air_long1.dat',extraStr=" 1000 1000")
#     test2()
#     setIsegV(0.2)
#     time.sleep(10)
#     vx = getIsegV()
#     print(vx)
#     turnOffIsegV()
#     IsegHVOperationDrill0()
#     IsegHVOperationDrill()

#     HV_out_scan([200,-200,0],dT=10*60)
#     measureR()
#     measureR1()
#     measureI_interactively()
#     measureI_autoScan()
#     measureI_autoScanIseg()
