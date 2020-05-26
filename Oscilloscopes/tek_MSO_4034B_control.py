#!/usr/bin/env python3
import time
import os,sys
import re
from datetime import datetime
import socket
import numpy as np
from Rigol import Rigol
from glob import glob

def getMaxIndex(files,pattern='.*_(\d+).isf'):
    idx0 = None
    for f in files:
        m = re.match(pattern,f)
        if m:
            idx = int(m.group(1))
            if idx0 is None or idx>idx0: idx0 = idx
#     print(files)
#     print(idx0)
    return idx0

class Oscilloscope:
    def __init__(self, name='Keysight MSO-x 4054', addr='192.168.2.5:5025'):
        self.addr = addr
        self.ss = None
        self.name = name
        self.fileSuffix = '.1'
        self.connected = False
        self.cmdSuffix = '\n'
        self.dir0 = '/home/TMSTest/PlacTests/TMSPlane/data/fpgaLin/raw2/'
        self.dirx = 'test'
        self.tag = 'test_'

    def checkCmd(self):
        '''check the command in .hidden_cmd, exit if it's 'q', otherwise run the command there. Use # for comments.'''
        with open('.hidden_cmd') as f1:
            lines = [l.strip() for l in f1.readlines() if len(l)>0 and l[0] not in ['\n','#'] ]
            for line in lines:
                if line.lower() in ['q','quit','exit','end']: return 'q'
                else:
                    try:
                        exec(line)
                    except NameError as e:
                        print(f"Error running command:{line}--> {e}")
        return None

    def connect(self, force=False):
        if self.connected and (not force): return

        t = self.addr.split(':')
        hostname = t[0]
        port = int(t[1]) if len(t)>1 else 5025

        self.ss = socket.socket(socket.AF_INET,socket.SOCK_STREAM)       #init local socket handle
        try:
            self.ss.connect((hostname,port))                                 #connect to the server
        except ConnectionRefusedError as e:
            print(e)
            return False 

        ### check the connection
        self.checkESR()
#         self.query("*ESR?")
#         self.send("DCL;")                           #read back device ID
#         time.sleep(5)
#         self.send("*CLS;")                           #read back device ID
        self.query("*IDN?;")                           #read back device ID
#         print("Instrument ID: %s"%self.ss.recv(128))

        self.connected = True
        return True

    def disconnect(self):
        if not self.connected: return
        self.ss.close()
        self.connected = False

    def send(self, cmd):
        ### to have costumize command string

        self.ss.send((cmd+self.cmdSuffix).encode("UTF-8"))                           #read back device ID

    def query(self,cmd, show=True, nByte=128):
        self.send(cmd)
        time.sleep(0.1) ### let's try to wait a bit here
        ret = self.ss.recv(nByte).decode()

        while cmd[0]!='*' and (len(ret)<len(cmd) or cmd[:len(ret)]!=cmd):
            print(f"{cmd}-> {ret} // retrying...")
            time.sleep(0.5)
            ret = self.ss.recv(nByte).decode()

        if show: print(f"{cmd}-> {ret}")
        return ret.rstrip().split(' ')[1:] if cmd[0]!='*' else ret.strip()

    def recvX(self, nByte=128):
        ret = self.ss.recv(nByte).decode()
        print(ret)
        return ret.strip().split(' ')[1:]

    def setup_default_mode(self):
        ss = self.ss
        len0 = 20000000

        ## acquire
        self.send("ACQuire:MODe HIRes;")
#         self.send("SELect:CH1 OFF; CH2 ON; CH3 OFF; CH4 OFF;")
        self.send("SELect:CH1 ON; CH2 OFF; CH3 OFF; CH4 OFF;")
#         self.send("CH2:COUPling AC; INVert OFF;")
        self.send("CH1:COUPling AC; INVert OFF;")
        self.send(f"HORizontal:SCAle 1; RECOrdlength {len0};")
        self.send(f"DATa:SOUrce CH1; ENCdg RPBinary; STOP {len0};")
        self.send("ACQUIRE:STOPAFTER SEQUENCE;")
#         self.send("DATa:SOUrce CH2")
#         self.send("DATa:ENCdg RIBinary")

    def test2(self, N=10):
        self.connect() 
        self.setup_default_mode()

        self.ss.settimeout(2.)
        for i in range(N):
            print(datetime.now())
            self.send("*CLS;")
            self.send("ACQUIRE:STOPAFTER SEQUENCE")
            self.send("ACQuire:STATE ON")
            self.send('*WAI')

            self.send('SAVE:WAVEFORM CH2, "E:/test3.isf";')
#             self.send('*WAI')
#             self.send("BUSY?")
# 
#             while True:
#                 try:
#                     ret = self.ss.recv(128).decode()
#                 except socket.timeout:
#                     time.sleep(1)
#                     continue
#                 if ret == '0': break
            while True:
                try:
                    print("querying...")
#                     self.query("*ESR?")
                    self.query("BUSY?")
                except socket.timeout:
                    time.sleep(1)

    def take_data(self, mode=0, saveName=None):
        ### check status
        self.checkESR()

        ### start the DAQ
        self.send("ACQuire:STATE ON;")
        time.sleep(9)

        ### wait for DAQ complete
        while True:
            if self.query("ACQuire:STATE?", show=False)[0] == '0': break
            time.sleep(1)

        ###request data
        self.send("DATE?;:TIME?;:WAVFrm?")

        ### get meta data
        a = self.ss.recv(512)
        while len(a)<512:
            a += self.ss.recv(2**9)
        pre = a.find(b":CURVE")

        ### get the data size
        lenA = int(a[pre+8:pre+9].decode())
        lenM = int(a[pre+9:pre+9+lenA].decode()) ### length of the meta data
        lenx = pre + lenM + 9 + lenA + 1 ## suppose there is a END sign
#         print(lenA, lenM, lenx)

        ### get bulk data
        if mode>1:
            lenOther = pre + 9 + lenA + 1
            print(f"Recieving {lenM} + {lenOther} data...")
        while len(a)<lenx:
            a += self.ss.recv(2**17)
        if mode>0:
            print("total recieved data: {}".format(len(a)))

        ### save data
        if saveName:
            while os.path.exists(saveName): saveName += self.fileSuffix
            with open(saveName,'wb') as f1:
                f1.write(a)

        ### check and cleaning -- leave this to the last to allow the oscilloscope to have more time to recover
        self.checkESR()

    def checkESR(self):
        x = self.query("*ESR?", show=False)
        while x!='0':
            self.query("ALLEv?")
            time.sleep(0.2)
            x = self.query("*ESR?")

    def test4(self):
        while True:
            print("here")
            time.sleep(2)
            print(f"dirx={self.dirx},tag={self.tag}")
            cmd = self.checkCmd()
            print(f"dirx={self.dirx},tag={self.tag}")

            if cmd == 'q': return

    def test0(self):
        self.connect()
#         self.send("*RSR?")
#         self.send("*ALLEv?")
#         self.query("ALLEv?")
        self.query("DATE?;:TIME?")
#         self.query("EVENT?")
        self.query("EVMsg?")

        x = self.query("*ESR?")
        while x!='0':
            self.query("ALLEv?")
            time.sleep(0.2)
            x = self.query("*ESR?")
#
    def run_project(self, N=1, dirx='temp', tag='test_'):
        '''DAQ from ethernet, so we can analysis as soon as it's done.'''
        self.connect()
        self.setup_default_mode()
        self.ss.settimeout(None)

        ### check the output directory
        dirx = dirx.strip()
        if len(dirx)==0 or dirx[0]!='/': dirx = self.dir0+dirx ## one should give absolute path if use the non-default directory
        if not os.path.exists(dirx): os.makedirs(dirx)
        if dirx[-1]!='/': dirx += '/'
        print(f"Data directory: {dirx}, tag:{tag}")
        self.dirx, self.tag = dirx, tag ### save these values to the class

        ### find the start index
        ifdx = getMaxIndex(glob(dirx+'*.isf'),'.*_(\d+).isf')
        if ifdx is None: ifdx = 0
        else: ifdx += 1

        ### start taking data
        n = 0
        while True:
            print('='*20,ifdx,'='*20)
            t0 = datetime.now()
            self.take_data(mode=1, saveName=f"{self.dirx}{self.tag}{ifdx}.isf")
            t1 = datetime.now()
            print(t0, t1-t0)

            ifdx += 1
            n += 1
            if n == N: break

            ### allow hidden command break
            if self.checkCmd() == 'q': sys.exit()

        ### done
        self.disconnect()

    def test3(self):
        self.run_project(N=10, dirx='Jan15a', tag='test3_')

    def test1(self):
        self.connect() 
        ss = self.ss

#         self.send("*CLS;")
#         self.query("*ESR?")
#         self.setup_default_mode()
#         return

#         time.sleep(200)
        ### trigger
#         self.send("DATa:SOUrce CH2")
#         self.query("DATa:STARt?")
#         self.send("DATa:STOP 1000")
# #         self.query("ACQuire:MAXSamplerate?")
#         self.query("DATa?")
#         self.send("ACQuire:MODe HIRes")
#         self.query("ACQuire:STATE?")
#         self.query("ACQUIRE:STOPAFTER?")

        print(datetime.now())
        self.send("ACQUIRE:STOPAFTER SEQUENCE")
        self.send("ACQuire:STATE ON")
        time.sleep(9)

#         print('A',self.query("ACQuire:STATE?"),"t")
        ss.settimeout(None)
        while True:
            if self.query("ACQuire:STATE?")[0] == '0': break
            time.sleep(1)
        
        self.send('SAVE:WAVEFORM CH2, "E:/test2.isf";')
        self.send('*WAI')
        self.query("BUSY?")
#         self.query("*ESR?")
        self.send("*CLS;")
        return
#         self.query("ACQuire:STATE?")
#         self.send("DATa:ENCdg RPBinary")
#         self.query("SET?")
#         self.query("*LRN?")
#         self.query("DATa?")
#         self.query("WFMOutpre?")
#         time.sleep(2)
#         self.query("*esr?")
#         self.query("*OP?")
        print("here....")
        self.send("ACQUIRE:STOPAFTER RUNSTop")
#         self.send("ACQuire:STATE ON")
        ss.settimeout(2.0)
        while True:
            try:
                print('wait A')
                self.send("ACQuire:STATE ON")
                print(self.query("ACQuire:STATE?"))
#                 print('A',self.query("ACQuire:STATE?"),"t")
            except socket.timeout:
                continue
            break
        print(datetime.now())
        return

        len0 = 20000000
        self.send(f"HORizontal:RECOrdlength {len0}")
        self.send(f"DATa:STOP {len0}")
        self.query("WFMOutpre?")
        self.query("CH2:OFFSet?")
        self.query("CH2:PRObe:UNIts?")
        self.query("CH2:YUNIts?")
        self.query("CH2:POSition?")
        self.query("CH2:SCAle?")
#         self.query("CURVe?",nByte=16384)


#         self.send("DATa:ENCdg RIBinary")
        self.send("DATa:ENCdg RPBinary")
        self.query("DATa?")
        ###get data
        self.send("CURVe?")
        lenM = 13 ### length of the meta data
        lenx = len0+lenM
        a = self.ss.recv(512)
        while len(a)<lenx:
            a += self.ss.recv(512)
#         a += self.ss.recv(128).decode()
#         a += self.ss.recv(128).decode()
#         a += self.ss.recv(128).decode()
#         a += self.ss.recv(128).decode()
#         a += self.ss.recv(128).decode()
        b = a[:lenM]
        c = a[lenM:]
        print(len(c))
#         print(a)
#         print(b)
#         print(c)
#         print([int.from_bytes(x, byteorder='big', signed=True) for x in c])
#         print([(int(x)-128)*0.005 for x in c])
#         self.query("TRIGger:A?")
#         self.query("TRIGger:A:EDGE?")
#         self.query("HIStogram:DATa?", nByte=4096)
#         self.query("HIStogram:STARt?")
#         self.query("HIStogram:END?")
        return


        ### setup histogram
        self.send("HISTOGRAM?")
        print("GET: %s"%ss.recv(128))

        self.send("HIStogram:COUNt RESET")
#         self.send("HIStogram:BOXPcnt?")
        self.send("MEASUREMENT:MEAS1?")
        print("GET: %s"%ss.recv(128))

        self.send("MEASUREMENT:MEAS1:COUNT?")
        print("GET: %s"%ss.recv(128))

        self.send("MEASUREMENT:MEAS1:VALue?")
        print("GET: %s"%ss.recv(128))


    def test(self, step=0):
        self.connect() 
        ss = self.ss

#         self.send("SETUP1:TIME?")
        self.send("MEASUrement:IMMed:TYPe WAVEFORMS")
        self.send("MEASUrement:IMMed:TYPe?")
        print("Time: %s"%ss.recv(128))
        self.send("MEASUrement:IMMed:UNIts?")
        print("Unit: %s"%ss.recv(128))
        self.send("TIME?")
        print("Time1: %s"%ss.recv(128))
        self.send("MEASUrement:IMMed:VALue?")
        print("Value: %s"%ss.recv(128))
        self.send("TIME?")
        print("Time2: %s"%ss.recv(128))

    def use_setup0(self):
        ### the range of x is 20us x 10

        pass

    def use_setup1(self):
        pass

    def getHistogramCounts(self, debug=False):
        t0 = self.query("TIME?", show=debug)
        n1 = self.query("MEASUREMENT:MEAS1:VALue?", show=debug)
        t1 = self.query("TIME?", show=debug)

        return t0[0], n1[0], t1[0]


    def getHistogramData(self, debug=False):
        a = self.query("HIStogram:STARt?")
        b = self.query("HIStogram:END?")
        c = self.query("HIStogram:DATa?", nByte=4096)

        return a[0], b[0], c[0]

def check_countloss(freq=600, dT=360, N=10):
    ### assume all other paramneters are setup
    ### setup Rigo to produce the freqency
    r1 = Rigol()
    r1.connect()
    r1._instr.write(":SOURce2:FREQuency %s"%freq)

    ### run the measurement
    os1 = Oscilloscope(name='Tektronix MSO 4034B', addr='192.168.2.17:4000')
    os1.connect()
    ### reset the histogram
    os1.send("HIStogram:COUNt RESET")
    time.sleep(5)

    with open("test2.csv",'a') as f1:
        f1.write(f"\n#freq={freq} Hz")
        i = 0
        while True:
            m1 = os1.getHistogramCounts()
            print(m1)
            f1.write('\n'+', '.join(m1))
            i += 1
            if i>N: break
            time.sleep(dT)
       
        ### finally save the histogram
        a,b,c = os1.getHistogramData()
        f1.write('\n#HistData:'+':'.join([a, b, c]))

    return

def check_multiple():
#     for f in [1000, 1500, 1200, 1300, 1100, 490, 510, 980]:
#     for f in [1000, 200]:
#     for f in [600,900,300,1500,700,1200,500,800,1000,400,200,550,650,750,450]:
    for f in [1510]:
        check_countloss(freq=f, dT=360, N=3)

def check_pulse():
    os1 = Oscilloscope(name='Tektronix MSO 4034B', addr='192.168.2.17:4000')
    for dv in range(5,90,10):
        print(dv)
        rg1 = Rigol()
        rg1.connect()
        rg1.setPulseV(dv*0.001)

#         os1.run_project(N=30, dirx='Jan15d', tag=f'TPCHVoff_gasOff_Pulse_{dv}mV_')
        os1.run_project(N=2, dirx='May22b', tag=f'test_Pulse_{dv}mV_')


def main():
    os1 = Oscilloscope(name='Tektronix MSO 4034B', addr='192.168.2.17:4000')
    os1.dir0 = '/home/TMSTest/PlacTests/TMSPlane/data/fpgaLin/raw/'
#     os1.run_project(N=-1, dirx='Jan15b', tag='TPCHV2kV_PHV0V_gasoff_')
    os1.run_project(N=-1, dirx='May22a', tag='test1_')

def test():
    os1 = Oscilloscope(name='Tektronix MSO 4034B', addr='192.168.2.17:4000')

#     for i in range(10000):
#         os1.addr = f'192.168.2.17:{i:d}'
#         try:
#             if not os1.connect(force=True):
#                 print(i)
#                 continue
#             os1.send("*IDN?;")
#             print(i, "Instrument ID: %s"%os1.ss.recv(128))
#             os1.disconnect()
#         except (ConnectionRefusedError,OSError,BrokenPipeError) as e:
# #             print(i)
#             continue
#     os1.test4()
#     os1.test3()
#     os1.test0()
    os1.dir0 = '/home/TMSTest/PlacTests/TMSPlane/data/fpgaLin/raw/'
    os1.run_project(N=-1, dirx='Jan15a', tag='TPCHV2kV_PHV0V_air4_')
    return

    for i in range(10):
        os1.test1()
        os1.disconnect()

if __name__ == '__main__':
    main()
#     check_pulse()
#     test()
#     check_multiple()
#     check_countloss()
#     getMaxIndex(glob("/data/Samples/TMSPlane/fpgaLin/*.root"),".*/Feb09b_data_(\d+).root")
