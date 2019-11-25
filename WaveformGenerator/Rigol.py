#!/usr/bin/env python
'''For Rigol DG4162. The device should be configured to use ip 192.168.2.3 and subnet mask 255.255.255.0
'''
import socket
import time
import sys

class Handle:
    def __init__(self, s):
        self.s = s

    def write(self, cmd, dt=0.5):
        print 'sending',cmd
        self.s.send(cmd+'\n')
        if dt is not None: time.sleep(dt)

    def read(self,cmd,ndata=-1):
        print 'reading',cmd
        self.s.send(cmd+'\n')

        a = self.s.recv(1024)
        while len(a)<ndata:
            a += self.s.recv(1024)

        return a


class Rigol:
    def __init__(self):
        self.addr = '192.168.2.5:5555'
        self.s3 = None
        self.handle = None

        self.pulseV = -1

    def connect(self):
        a = self.addr.split(':')
        Rig_hostname = a[0]                    #rigol dds ip address
        Rig_port = int(a[1])                                 #rigol dds instrument port
        self.s3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)      #init local socket handle
        self.s3.connect((Rig_hostname, Rig_port))

        self._instr = Handle(self.s3)

    def calibration(self):
        freq = 100
        hV = 0.3
        lV = 0.2
        '''for calibration'''
        ### [:SOURce<n>]:PHASe[:ADJust] <phase>|MINimum|MAXimum
        ### [:SOURce<n>]:APPLy:SQUare [<freq>[,<amp>[,<offset>[,<phase>]]]] //:APPLy:SQUare 100,2.5,0.5,90

        ### source1 for trigger: 3.3V Square output
        self._instr.write(":SOURce1:APPLy:SQUare {0:d},3.3,1.65,0".format(freq))

        ### source2 for trigger: 3.3V Square output
        self._instr.write(":SOURce2:FUNCtion USER")
        self._instr.write(":SOURce2:FREQ %g" % freq)
        ### [:SOURce<n>]:VOLTage[:LEVel][:IMMediate]:HIGH <voltage>|MINimum|MAXimum
        self._instr.write(":SOURce2:VOLTage:HIGH %g" % hV)
        self._instr.write(":SOURce2:VOLTage:LOW %g" % lV)

#         self._instr.write(":PA:OFFSet ON".format(offset))                       #set output offset, default value 1V 
#         self._instr.write(":PA:OFFSet:VALUe {0:.2f}".format(offset))                       #set output offset, default value 1V 

#         a = self._instr.read(':PA:OFFSet:VALUe?')
#         print a

        string = ':DATA:DAC VOLATILE,'
        string += ','.join(['0' for i in range(100)]+['{0:d}'.format(x*16384/120) for x in range(120)]+['16384']*20)
        print string
        self._instr.write(string)

        ### coupling
        ## :COUPling:CHannel:BASE CH1|CH2
        ## :COUPling:CHannel:BASE?
        ## :COUPling:FREQuency[:STATe] ON|OFF
        ## :COUPling:FREQuency[:STATe]?
        ## :COUPling:FREQuency:DEViation <deviation>
        ## :COUPling:FREQuency:DEViation?
        ## :COUPling:PHASe[:STATe] ON|OFF
        ## :COUPling:PHASe[:STATe]? 
        ## :COUPling:PHASe:DEViation <deviation>
        ## :COUPling:PHASe:DEViation?
        ## :COUPling[:STATe] ON|OFF
        ## :COUPling[:STATe]?
        ## :COUPling:AMPL[:STATe] ON|OFF
        ## :COUPling:AMPL[:STATe]?  
        ## :COUPling:AMPL:DEViation <deviation>
        ## :COUPling:AMPL:DEViation?

        self._instr.write(":COUPling:CHannel:BASE CH1")
        self._instr.write(":COUPling:PHASe ON")
        self._instr.write(":COUPling:PHASe:DEViation 340")

        ### output
        ## :OUTPut[<n>][:STATe] ON|OFF
        ## :OUTPut[<n>][:STATe]?
        self._instr.write(":OUTPut1 ON")
        self._instr.write(":OUTPut2 ON")

    def setPulseV(self, dV=0.1, lV=0.2):
        if len(sys.argv)>1: dV = float(sys.argv[1])
        self._instr.write(":SOURce2:VOLTage:HIGH {0:g}".format(dV+lV))

    def tune(self):
#         self._instr.write(":COUPling:PHASe:DEViation 340")
        var1 = sys.argv[1]
        self._instr.write(":COUPling:PHASe:DEViation "+var1)

    def normal_run(self):
        '''normal_run'''
        pass

    def test_volatile(self):
        freq = 500
        offset = 0.5
        self._instr.write(":SOURce1:FUNCtion USER")
        self._instr.write(":SOURce1:FREQ %g" % freq)
        self._instr.write(":PA:OFFSet ON".format(offset))                       #set output offset, default value 1V 
        self._instr.write(":PA:OFFSet:VALUe {0:.2f}".format(offset))                       #set output offset, default value 1V 

        a = self._instr.read(':PA:OFFSet:VALUe?')
#         a = self._instr.read(':PA:OFFSet?')
#         self.s3.send(':PA:OFFSet:VALUe?\n')
#         a = self.s3.recv(20)
        print a
#         self._instr.write("FUNC:USER VOLATILE")

#         return
        string = ':DATA:DAC VOLATILE,'
        string += ','.join(['{0:d}'.format(x*16300/120) for x in range(120)])
#         string += ','.join(['{0:.2f}'.format(1.-0.01*x) for x in range(20)])

        print string
        self._instr.write(string)

    def setup_tail_pulse3(self, freq=100, xp=16, np=1024, alpha=0.01):
        self._instr.write("FUNC USER")
        time.sleep(0.5)
        self._instr.write("FREQ %g" % freq)
        time.sleep(0.5)

        amax = 16383
        vals=[0 for i in xrange(np)]
        k = np/1024.

        alpha /= k
        pp = 0 ### the pulse will always be at around 0.5 ms of the sample
        dp = pp+int(0.00002*freq*np) ### keep high voltage for 0.01 ms
        for i in range(pp): vals[i] = int(amax*(1-math.exp(-(i+np-dp)*alpha)))
        for i in range(dp,np): vals[i] = int(amax*(1-math.exp(-(i-dp)*alpha)))

        string = "DATA:DAC VOLATILE"
        for i in xrange(np):
            string += (",%d"% vals[i])
#         print(string)
        self._instr.write(string)
        time.sleep(1.0)
        self._instr.write("FUNC:USER VOLATILE")
        time.sleep(0.5)

    def turn_on_trigger(self):
        self._instr.write("OUTPut:SYNC ON")
        time.sleep(0.5)
        self._instr.write("OUTPut:TRIGger ON")
        time.sleep(0.5)

    def turn_off_trigger(self):
        self._instr.write("OUTPut:SYNC OFF")
        time.sleep(0.5)
        self._instr.write("OUTPut:TRIGger OFF")
        time.sleep(0.5)

    def test1(self, freq):
        self.s3.send(":SOURce1:FREQuency %s\n"%freq)          #set output frequency, default value 1MHz 
        self.s3.send(":SOURce1:VOLTage 1\n")                 #set output amplitude
        self.s3.send(":PA:OFFSet:VALUe 1\n")                       #set output offset, default value 1V 

def test2():
    r1 = Rigol()
    r1.connect()
#     r1.test_volatile()
    r1.calibration()
    r1.setPulseV(0.2)
#     r1.tune()
#     r1.test(20)

def test1():
    freq = 50
    Rig_hostname = '192.168.2.5'                    #rigol dds ip address
    Rig_port = 5555                                 #rigol dds instrument port
    s3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)      #init local socket handle
    s3.connect((Rig_hostname, Rig_port))

    s3.send(":SOURce1:FREQuency %s\n"%freq)          #set output frequency, default value 1MHz 
    s3.send(":SOURce1:VOLTage 1\n")                 #set output amplitude
    s3.send(":PA:OFFSet:VALUe 1\n")                       #set output offset, default value 1V 
#    s3.send("OUTPut ON\n")                 #turn on channel1

    s3.close()

if __name__ == '__main__':
    test2()
