#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import time
from datetime import datetime
import socket
import subprocess
import numpy as np
import array
from ROOT import *
hostname = "192.168.2.5"                #wire network hostname
#hostname = "10.146.73.180"              #wireless network hostname
port = 5025                             #host tcp port
#note that: every command should be termianated with a semicolon
#========================================================#
## plot waveform via gnuplot with parameters
# @param x_range x-axis range scope
# @param y_range y2-axis range scope
# @param ch1_offset channel one offset 
# @param timebase_position x-axis timebase position 
def plot(x_range,y_range,ch1_offset,timebase_position,x_unit):
   XRange = "x_var='%.5f'"%(x_range)            #xrange parameter 
   YRange = "y_var='%.3f'"%(y_range)            #yrange parameter
   CH1offset = "offset='%.3f'"%(ch1_offset)     #offset parameter
   Timebase_Position = "timebase_position='%.5f'"%(timebase_position)     #timebase position parameter
   X_Unit = "x_unit='%d'"%(x_unit)              #x-axis unit parameter
   print XRange,YRange,CH1offset,Timebase_Position,X_Unit
   subprocess.call("gnuplot -e %s -e %s -e %s -e %s -e %s keysight_oscilloscope.gp"%(XRange,YRange,CH1offset,Timebase_Position,X_Unit), shell = True)
#    subprocess.call("eps2png -resolution 400 keysight_oscilloscope.eps", shell = True)
   #subprocess.call("convert keysight_oscilloscope.eps keysight_oscilloscope.png", shell = True)
   subprocess.call("convert -flatten -density 400 -colorspace rgb keysight_oscilloscope.eps keysight_oscilloscope.png", shell = True)
   subprocess.call("xdg-open keysight_oscilloscope.png", shell = True)
   print "OK"
#========================================================#
## main function: sent oscilloscope commands and fetch data
#

class pulseGenerator:
    def __init__(self, name='Rigol DG4162'):
        self.addr = '192.168.2.6:5025'
        self.ss = None
        self.name = name

    def connect(self):
        t = self.addr.split(':')
        hostname = t[0]
        port = int(t[1]) if len(t)>1 else 5025

        self.ss = socket.socket(socket.AF_INET,socket.SOCK_STREAM)       #init local socket handle
        self.ss.connect((hostname,port))                                 #connect to the server

        ss.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

    def start_pulse(self, dV=0.05, Vl=0.2, fQ=10):
        if dV > 1:
            print('The demanded dV is too high: {0:.3f}. Abort...'.format(dV))
            sys.exit(1)
        print("Setting low V: {0:.3f}, high V: {1:.3f}".format(Vl, Vl+dV))

        fQ1 = fQ

        self.connect()
        ## CH1 --> guard ring
        self.ss.send("APPLy:SQUare {0:d},{1:.3f},{2:.3f}".format(fQ1, dV, Vl+0.5*dV))
        time.sleep(1)

        ## CH2 --> Test pulse for trigger
        self.ss.send("APPLy:SQUare:CH2 {0:d},0.01,0.005".format(fQ))
        time.sleep(1)

        n = 2750.
        print(math.modf(n/(5000000./fQ)), )
        a = math.modf(n*fQ/5000000.)
        phase = a[0]*360
        if phase>180: phase = phase - 360
        print(phase)
        self.ss.send("PHASe:CH2 {0:d}".format(int(phase)))
        time.sleep(1)

        self.ss.send("OUTP ON")
        time.sleep(1)
        self.ss.send("OUTP:CH2 ON")
        time.sleep(1)

        self.ss.send("PHASe:ALIGN")
        time.sleep(1)

        self.ss.close()
        self.ss = None

class Oscilloscope:
    def __init__(self, name='Keysight MSO-x 4054'):
        self.addr = '192.168.2.5:5025'
        self.ss = None
        self.name = name
        self.fileSuffix = '.1'
        self.connected = False

    def connect(self):
        if self.connected: return

        t = self.addr.split(':')
        hostname = t[0]
        port = int(t[1]) if len(t)>1 else 5025

        self.ss = socket.socket(socket.AF_INET,socket.SOCK_STREAM)       #init local socket handle
        self.ss.connect((hostname,port))                                 #connect to the server
        self.connected = True

    def save_screen(self,name='test_fig.png'):
        self.connect() 

        ss = self.ss
        ss.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

        ### waveform
#         ss.send(":SAVE:IMAGe:FORMat PNG;")       #Waveform source 
#         ss.send(":SAVE:IMAGe {0:s};".format(name))           #Waveform data format
        ss.send(":HARDcopy:INKSaver 0;") # <value> ::= {{OFF | 0} | {ON | 1}}
        ss.send(":DISPlay:DATA? PNG,COLor;")           #Waveform data format
#         ss.send(":DISPlay:DATA? PNG,GRAYscale;")           #Waveform data format
#         ss.send(":DISPlay:DATA? PNG;")           #Waveform data format
        ss.settimeout(3)

        d1 = ''
        while True:
            try:
                a = ss.recv(1024*4)
                d1 += a
            except socket.timeout:
                d1 += a
                break
        with open(name,'w') as fout1:
            fout1.write(d1[11:])

#         print d1[:11]
#         print len(d1[11:])
#         print [ord(x) for x in d1[11:30]]
        ss.close()


    def take_data(self,pref='evt_',N=-1):
        self.connect()

        ss = self.ss
        ss.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

        ### waveform
        ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        ss.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        ss.send(":WAVeform:FORMat WORD;")           #Waveform data format

        ### setup trigger
#         ss.send(":TRIGger:SWEep NORMal;")
#         ss.send(":TRIGger:MODE EDGE;")
#         ss.send(":TRIGger:EDGE:LEVel 1.0,CHANnel1;")

        ### meta data
        ss.send(":WAVeform:PREamble?;")
        a = ss.recv(128)
#         print "PREample: %s"%a
        pre = a.split(';')[1].split(',')
#         print pre

        total_point = int(pre[2])
        xInc = float(pre[4])
        xOrig = float(pre[5])
        xRef = float(pre[6])
        yInc = float(pre[7])
        yOrig = float(pre[8])
        yRef = int(pre[9])


        ## take_data
        iChan = 1
        ievt = 0
        NINTERVEL = 100
        while ievt != N:
            try:
                ### status
                if ievt % NINTERVEL == 0:
                    print "{0:d} events taken".format(ievt)

                ### DAQ
                ss.send(":SINGle;")
                ss.send(":WAVeform:DATA?;")

                ### data parsing
#                 n = total_point*2 + 11 ### 11 for header
                n = 30
                totalContent = ""
                totalRecved = 0
                while totalRecved < n:                      #fetch data
                    onceContent = ss.recv(int(n - totalRecved))
                    if totalContent == '':
                        ### update the data size based on the header of data
                        nheader = int(onceContent[2])
                        total_point = int(onceContent[3:3+nheader])/2
                        n = int(onceContent[3:3+nheader]) + 11

                    totalContent += onceContent
                    totalRecved = len(totalContent)

#                 data_i = [0]*total_point
#                 data_ix = [0]*total_point
#                 n = total_point * 2 + 11 ### 11 for header
#                 totalContent = ""
#                 totalRecved = 0
#                 while totalRecved < n:                      #fetch data
#                     onceContent = ss.recv(int(n - totalRecved))
#                     totalContent += onceContent
#                     totalRecved = len(totalContent)
# 
#                 print totalContent[:30], totalContent[2], int(totalContent[2])
# 
                totalContent = totalContent[int(totalContent[2])+3:]
                length = len(totalContent)/2              #print length
                if length != total_point:
                    print iChan, 'data length:', length, 'NOT as expected', total_point

                ### parse data
                data_i = [0]*total_point
                data_ix = [0]*total_point
                for i in range(length):              #store data into file
                    ### combine two words to form the number
                    data_i[i] = ((ord(totalContent[i*2+1])<<8)+ord(totalContent[i*2]) - yRef)*yInc+yOrig
                    data_ix[i] = (i - xRef)*xInc+xOrig

                ### write out data
                with open(pref+str(ievt)+'.dat','w') as f1:
                    f1.write('# time '+ str(datetime.now()))
                    f1.write('\n# total_point '+str(total_point))
                    f1.write('\n# xInc '+str(xInc))
                    f1.write('\n# xOrig '+str(xOrig))
                    f1.write('\n# xRef '+str(xRef))
                    f1.write('\n# yInc '+str(yInc))
                    f1.write('\n# yOrig '+str(yOrig))
                    f1.write('\n# yRef '+str(yRef))
                    for di in range(len(data_i)):
                        f1.write('\n'+str(data_ix[di])+' ' + str(data_i[di]))

                ievt += 1
            except KeyboardInterrupt:
                break

        ss.send(":RUN;")
        ss.close()

    def take_data2(self,outRootName,N=-1,NINTERVEL=200, vPulse=40):
        '''same as take data, but save root file. vPulse in mV'''
        self.connect()

        ss = self.ss
        ss.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

        ### waveform
        ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        ss.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        ss.send(":WAVeform:FORMat WORD;")           #Waveform data format

        ### setup trigger
#         ss.send(":TRIGger:SWEep NORMal;")
#         ss.send(":TRIGger:MODE EDGE;")
#         ss.send(":TRIGger:EDGE:LEVel 1.0,CHANnel1;")

        ### meta data
        ss.send(":WAVeform:PREamble?;")
        a = ss.recv(128)
#         print "PREample: %s"%a
        pre = a.split(';')[1].split(',')
#         print pre

        total_point = int(pre[2])
        xInc = float(pre[4])
        xOrig = float(pre[5])
        xRef = float(pre[6])
        yInc = float(pre[7])
        yOrig = float(pre[8])
        yRef = int(pre[9])


        T = array.array('i',[0])
        V = array.array('i',[vPulse])
        data0 = array.array('f',[0]*total_point)
        data1 = array.array('f',[0]*total_point)

        if self.fileSuffix:
            while os.path.exists(outRootName): outRootName += self.fileSuffix
        fout1 = TFile(outRootName,'recreate')
        tree1 = TTree('tree1',"data: {0:d} points".format(total_point))
        tree1.Branch('T',T,'T/i')
        tree1.Branch('V',V,'V/I')
        tree1.Branch('t',data0, "t[{0:d}]/F".format(total_point))
        tree1.Branch('val1',data1, "val1[{0:d}]/F".format(total_point))


        t1 = TDatime()
        ## take_data
        ievt = 0
        while ievt != N:
            try:
                ### status
                if ievt % NINTERVEL == 0:
                    print "{0:d} events taken".format(ievt)

                t1.Set()
                ### DAQ
                ss.send(":SINGle;")
                ss.send(":WAVeform:DATA?;")

                ### data parsing
                n = total_point * 2 + 11 ### 11 for header

                totalContent = ""
                totalRecved = 0
                while totalRecved < n:                      #fetch data
                    onceContent = ss.recv(int(n - totalRecved))
                    totalContent += onceContent
                    totalRecved = len(totalContent)

                ### remove the header
                totalContent = totalContent[int(totalContent[2])+3:]
                length = len(totalContent)/2              #print length
                if length != total_point:
                    print ievt, 'data length:', length, 'NOT as expected', total_point

                ### put them into a tree
                ix = 0
                while ix<length:
                    data0[ix] = (ix - xRef)*xInc+xOrig
                    data1[ix] = ((ord(totalContent[ix*2+1])<<8)+ord(totalContent[ix*2]) - yRef)*yInc+yOrig
                    ix += 1

                    if ix == total_point: break

                while ix < total_point:
                    data0[ix] = -1
                    data1[ix] = -1
                    ix += 1

                T[0] = t1.Get()

                fout1.cd()
                tree1.Fill()
                fout1 = tree1.GetCurrentFile()

                ievt += 1
            except KeyboardInterrupt:
                break

        tree1.Write()
        fout1.Close()

        ss.close()
        self.connected = False

    def take_data3(self,outRootName,N=-1,NINTERVEL=200, vPulse=40):
        '''same as take data, but save root file. vPulse in mV'''
        ret = True
        self.connect()

        ss = self.ss
        ss.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

        ### waveform
        ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        ss.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        ss.send(":WAVeform:FORMat WORD;")           #Waveform data format

        ### setup trigger
#         ss.send(":TRIGger:SWEep NORMal;")
#         ss.send(":TRIGger:MODE EDGE;")
#         ss.send(":TRIGger:EDGE:LEVel 1.0,CHANnel1;")

        ### meta data
        ss.send(":WAVeform:PREamble?;")
        a = ss.recv(128)
#         print "PREample: %s"%a
        pre = a.split(';')[1].split(',')
#         print pre

        total_point = int(pre[2])
        xInc = float(pre[4])
        xOrig = float(pre[5])
        xRef = float(pre[6])
        yInc = float(pre[7])
        yOrig = float(pre[8])
        yRef = int(pre[9])

        ### waveform
        ss.send(":WAVeform:SOURce CHANnel3;")       #Waveform source 
        ss.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        ss.send(":WAVeform:FORMat WORD;")           #Waveform data format

        ### meta data
        ss.send(":WAVeform:PREamble?;")
        a = ss.recv(128)
        pre = a.split(';')[1].split(',')

        total_point3 = int(pre[2])
        xInc3 = float(pre[4])
        xOrig3 = float(pre[5])
        xRef3 = float(pre[6])
        yInc3 = float(pre[7])
        yOrig3 = float(pre[8])
        yRef3 = int(pre[9])

        if total_point3 != total_point: print "inconsistent total_point:", total_point3, total_point
        if xInc3 != xInc: print "inconsistent xInc:", xInc3, xInc
        if xOrig3 != xOrig: print "inconsistent xOrig:", xOrig3, xOrig
        if xRef3 != xRef: print "inconsistent xRef:", xRef3, xRef

        T = array.array('i',[0])
        V = array.array('i',[vPulse])
        data0 = array.array('f',[0]*total_point)
        data1 = array.array('f',[0]*total_point)
        data3 = array.array('f',[0]*total_point3)

        if self.fileSuffix:
            while os.path.exists(outRootName): outRootName += self.fileSuffix
        fout1 = TFile(outRootName,'recreate')
        tree1 = TTree('tree1',"data: {0:d} points".format(total_point))
        tree1.Branch('T',T,'T/i')
        tree1.Branch('V',V,'V/I')
        tree1.Branch('t',data0, "t[{0:d}]/F".format(total_point))
        tree1.Branch('val1',data1, "val1[{0:d}]/F".format(total_point))
        tree1.Branch('val3',data3, "val3[{0:d}]/F".format(total_point3))


        t1 = TDatime()
        ## take_data
        ievt = 0
        while ievt != N:
            try:
                ### status
                if ievt % NINTERVEL == 0:
                    print "{0:d} events taken".format(ievt)

                t1.Set()
                ### DAQ
                ss.send(":SINGle;")
                ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
                ss.send(":WAVeform:DATA?;")

                ### data parsing
                n = total_point * 2 + 11 ### 11 for header

                totalContent = ""
                totalRecved = 0
                while totalRecved < n:                      #fetch data
                    onceContent = ss.recv(int(n - totalRecved))
                    totalContent += onceContent
                    totalRecved = len(totalContent)

                ### remove the header
                totalContent = totalContent[int(totalContent[2])+3:]
                length = len(totalContent)/2              #print length
                if length != total_point:
                    print ievt, 'data length:', length, 'NOT as expected', total_point

                ### put them into a tree
                ix = 0
                while ix<length:
                    data0[ix] = (ix - xRef)*xInc+xOrig
                    data1[ix] = ((ord(totalContent[ix*2+1])<<8)+ord(totalContent[ix*2]) - yRef)*yInc+yOrig
                    ix += 1

                    if ix == total_point: break

                while ix < total_point:
                    data0[ix] = -1
                    data1[ix] = -1
                    ix += 1

                ss.send(":WAVeform:SOURce CHANnel3;")       #Waveform source 
                ss.send(":WAVeform:DATA?;")

                ### data parsing
                n = total_point3 * 2 + 11 ### 11 for header

                totalContent = ""
                totalRecved = 0
                while totalRecved < n:                      #fetch data
                    onceContent = ss.recv(int(n - totalRecved))
                    totalContent += onceContent
                    totalRecved = len(totalContent)

                ### remove the header
                totalContent = totalContent[int(totalContent[2])+3:]
                length = len(totalContent)/2              #print length
                if length != total_point3:
                    print ievt, 'data length:', length, 'NOT as expected 3:', total_point3

                ### put them into a tree
                ix = 0
                while ix<length:
                    data3[ix] = ((ord(totalContent[ix*2+1])<<8)+ord(totalContent[ix*2]) - yRef3)*yInc3+yOrig3
                    ix += 1

                    if ix == total_point3: break

                while ix < total_point3:
                    data0[ix] = -1
                    data1[ix] = -1
                    ix += 1

                ## save time
                T[0] = t1.Get()

                fout1.cd()
                tree1.Fill()
                fout1 = tree1.GetCurrentFile()

                ievt += 1
            except KeyboardInterrupt:
                ret = False
                break

        tree1.Write()
        fout1.Close()

        ss.close()
        self.connected = False

        return ret




    def test(self):
        self.connect()

        ss = self.ss
        ss.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

#         ss.send("*IDN?;")                           #read back device ID
#         print "Instrument ID: %s"%ss.recv(128)   
#         ss.send(":RUN;")



    
#         return


#         ss.send(":STOP;")
#         return

#         ss.send(":SYSTem:HEADer OFF;")              #Query analog store depth
        ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        ss.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        ss.send(":WAVeform:FORMat WORD;")           #Waveform data format
#         ss.send(":WAVeform:STReaming 1;")           #Waveform streaming on


        ss.send(":WAVeform:PREamble?;")
        a = ss.recv(128)
        print "PREample: %s"%a
        pre = a.split(';')[1].split(',')
        print pre

        np = int(pre[2])
        xInc = float(pre[4])
        xOrig = float(pre[5])
        xRef = float(pre[6])
        yInc = float(pre[7])
        yOrig = float(pre[8])
        yRef = int(pre[9])

        print xOrig, yOrig

        ### setup trigger
        ss.send(":TRIGger:SWEep NORMal;")
        ss.send(":TRIGger:MODE EDGE;")
        ss.send(":TRIGger:EDGE:LEVel 1.0,CHANnel1;")
 
        ss.send(":SINGle;")
        ss.send(":WAVeform:DATA?;")

        total_point = np
        data = []
        data_i = [0]*total_point
        data_ix = [0]*total_point
        n = total_point * 2 + 3
        print "n = %d"%n                            #calculate fetching data byte number
        totalContent = ""
        totalRecved = 0
        while totalRecved < n:                      #fetch data
            onceContent = ss.recv(int(n - totalRecved))
            totalContent += onceContent
            totalRecved = len(totalContent)
        length = len(totalContent[3:])/2              #print length
        if length != total_point:
            print iChan, 'data length:', length, 'NOT as expected', total_point
        print totalContent[2]
#         toalContent = totalContent[int(totalContent[2])+4]
        totalContent = totalContent[int(totalContent[2])+3:]
        print len(totalContent)
#         print totalContent[:10]

        length = len(totalContent)/2              #print length
        for i in range(length):              #store data into file
            ### combine two words to form the number
#             data_i[i] = ((ord(totalContent[i*2+1])<<8)+ord(totalContent[i*2]) - yRef)*yInc+yOrig
            data_i[i] = ((ord(totalContent[i*2+1])<<8)+ord(totalContent[i*2]) - yRef)*yInc+yOrig
            data_ix[i] = (i - xRef)*xInc+xOrig

        print data_i[:30]
        with open('tt1.dat','w') as f1:
            for di in range(len(data_i)):
                f1.write(str(data_ix[di])+' ' + str(data_i[di])+'\n')

        ss.close()

def captureScreen(filename='testing.png'):
    '''Capture screen from remote PC
    Ref: https://community.keysight.com/thread/18792
    Not tested!!
    '''
    ss.send("*IDN?;")                           #read back device ID
    print "Instrument ID: %s"%ss.recv(128)   

    ss.send(":MMEM:STORE:SCR \'D:\\exa_screen.png\';*WAI")
    ss.send(":MMEM:DATA? \'D:\\exa_screen.png\'")

    owp = ss.recv(4096)
    with open(filename,'w') as f1:
        f1.write(owp)
    ss.send(":MMEM:DEL \'D:\\exa_screen.png\'")
    ss.send("*CLS")

    pass

def takeData(channels=[1],filename='temp1.dat'):
    '''Loop over channels and save data to file with name filename'''
    Timebase_scale = 0
    ss.send("*IDN?;")                           #read back device ID
    print "Instrument ID: %s"%ss.recv(128)   

    ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 

    ss.send(":TIMebase:POSition?;")             #Query X-axis timebase position 
    Timebase_Poistion = float(ss.recv(128)[1:])
    print "Timebase_Position:%.6f"%Timebase_Poistion

    ss.send(":WAVeform:XRANge?;")               #Query X-axis range 
    X_Range = 0.3
#     X_Range = float(ss.recv(128)[1:])
    print "XRange:%g"%X_Range

    ss.send(":ACQuire:POINts:ANALog?;")         #Query analog store depth
    Sample_point = int(ss.recv(128)[1:]) - 3   
    print "Sample Point:%d"%Sample_point
    
    ss.send(":WAVeform:XUNits?;")               #Query X-axis unit 
    print "X-axis Unit:%s"%(ss.recv(128)[1:])   

    ss.send(":WAVeform:YUNits?;")               #Query Y-axis unit 
    print "Y-axis Unit:%s"%(ss.recv(128)[1:])   

    if X_Range >= 2.0:
        Xrange = np.arange(-X_Range/2.0,X_Range/2.0,X_Range*1.0/Sample_point)
        Timebase_Poistion_X = Timebase_Poistion
        x_unit = 1
    elif X_Range < 2.0 and X_Range >= 0.002:
        Xrange = np.arange((-X_Range*1000)/2.0,(X_Range*1000)/2.0,X_Range*1000.0/Sample_point)
        Timebase_Poistion_X = Timebase_Poistion * 1000.0
        x_unit = 2
    elif X_Range < 0.002 and X_Range >= 0.000002:
        Xrange = np.arange((-X_Range*1000000)/2.0,(X_Range*1000000)/2.0,X_Range*1000000.0/Sample_point)
        Timebase_Poistion_X = Timebase_Poistion * 1000000.0
        x_unit = 3
    else:
        Xrange = np.arange((-X_Range*1000000000)/2.0,(X_Range*1000000000)/2.0,X_Range*1000000000.0/Sample_point)
        Timebase_Poistion_X = Timebase_Poistion * 1000000000.0
        x_unit = 4
    #print Xrange
    #time.sleep(10)

    ss.send(":ACQuire:SRATe:ANALog?;")          #Query sample rate
    Sample_Rate = float(ss.recv(128)[1:])   
    print "Sample rate:%.1f"%Sample_Rate
    total_point = int(Sample_Rate * X_Range)
    print total_point

    ### dumpt info
#     X_Range,Y_Range,CH1_Offset,Timebase_Poistion


    ss.send(":SYSTem:HEADer OFF;")              #Query analog store depth
    ss.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
    ss.send(":WAVeform:FORMat WORD;")           #Waveform data format
    ss.send(":WAVeform:STReaming 1;")           #Waveform streaming on

    data = []
    ### get list of data
    for iChan in channels: 
        data_i = [0]*total_point
        ss.send(":WAVeform:SOURce CHANnel{0:d};".format(iChan))       #Waveform source 

        ## offset
        ss.send(":CHANnel{0:d}:OFFset?;".format(iChan))               #Channel1 Offset 
        CH1_Offset = float(ss.recv(128)[1:])   
        print "Channel %d Offset:%f"%(iChan, CH1_Offset)

        ### Y-range
        ss.send(":WAVeform:YRANge?;")               #Query Y-axis range
        Y_Range = float(ss.recv(128)[1:])   
        print "YRange:%f"%Y_Range
        Y_Factor = Y_Range/62712.0
        print Y_Factor

        ### get data
        ss.send(":WAVeform:DATA? 1,%d;"%total_point)         #Query waveform data with start address and length

        ### Why these magic numbers 2 and 3? A number contains 2 words? And there is a header with 3 words?
        n = total_point * 2 + 3
        print "n = %d"%n                            #calculate fetching data byte number
        totalContent = ""
        totalRecved = 0
        while totalRecved < n:                      #fetch data
            onceContent = ss.recv(int(n - totalRecved))
            totalContent += onceContent
            totalRecved = len(totalContent)
        length = len(totalContent[3:])/2              #print length
        if length != total_point:
            print iChan, 'data length:', length, 'NOT as expected', total_point

        for i in range(length):              #store data into file
            ### combine two words to form the number
            digital_number = (ord(totalContent[3+i*2+1])<<8)+ord(totalContent[3+i*2])
            if (ord(totalContent[3+i*2+1]) & 0x80) == 0x80:             
                data_i[i] = (digital_number - 65535+1000)*Y_Factor + CH1_Offset
            else:
                data_i[i] = (digital_number+1000)*Y_Factor + CH1_Offset
        data.append(data_i)

    #### write out: basic info, t, chanI
    with open(filename,'w') as fout:
        ### X_Range,Y_Range,CH1_Offset,Timebase_Poistion
        fout.write('# ')
        fout.write("\n##%/- "+"x_var='%.5f'"%(X_Range))            #xrange parameter 
        fout.write("\n##%/- "+"y_var='%.3f'"%(Y_Range))            #yrange parameter
        fout.write("\n##%/- "+"offset='%.3f'"%(CH1_Offset))     #offset parameter
        fout.write("\n##%/- "+"timebase_position='%.5f'"%(Timebase_Poistion))     #timebase position parameter
        fout.write("\n##%/- "+"x_unit='%d'"%(x_unit)) 
 
        fout.write('\n#time '+' '.join(['chan'+str(ichan) for ichan in channels]))
        for i in range(length-1):
            print i
            text = '\n{0:g} '.format(Xrange[i] + Timebase_Poistion_X)
            text += ' '.join(['{0:g}'.format(x[i]) for x in data])
            fout.write(text)

def captureWaveform():
    with open("./data_output.dat",'w') as outfile:
        Timebase_scale = 0
        ss.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

        ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        ss.send(":TIMebase:POSition?;")             #Query X-axis timebase position 
        Timebase_Poistion = float(ss.recv(128)[1:])
        print "Timebase_Position:%.6f"%Timebase_Poistion

        ss.send(":WAVeform:XRANge?;")               #Query X-axis range 
        X_Range = float(ss.recv(128)[1:])
        print "XRange:%g"%X_Range

        ss.send(":WAVeform:YRANge?;")               #Query Y-axis range
        Y_Range = float(ss.recv(128)[1:])   
        print "YRange:%f"%Y_Range
        #Y_Factor = Y_Range/980.0
        Y_Factor = Y_Range/62712.0
        #print Y_Factor

        ss.send(":ACQuire:POINts:ANALog?;")         #Query analog store depth
        Sample_point = int(ss.recv(128)[1:]) - 3   
        print "Sample Point:%d"%Sample_point
        
        ss.send(":WAVeform:XUNits?;")               #Query X-axis unit 
        print "X-axis Unit:%s"%(ss.recv(128)[1:])   

        ss.send(":WAVeform:YUNits?;")               #Query Y-axis unit 
        print "Y-axis Unit:%s"%(ss.recv(128)[1:])   

        ss.send(":CHANnel1:OFFset?;")               #Channel1 Offset 
        CH1_Offset = float(ss.recv(128)[1:])   
        print "Channel 1 Offset:%f"%CH1_Offset
        print "X_Range:%g"%X_Range 
        if X_Range >= 2.0:
            Xrange = np.arange(-X_Range/2.0,X_Range/2.0,X_Range*1.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion
        elif X_Range < 2.0 and X_Range >= 0.002:
            Xrange = np.arange((-X_Range*1000)/2.0,(X_Range*1000)/2.0,X_Range*1000.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion * 1000.0
        elif X_Range < 0.002 and X_Range >= 0.000002:
            Xrange = np.arange((-X_Range*1000000)/2.0,(X_Range*1000000)/2.0,X_Range*1000000.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion * 1000000.0
        else:
            Xrange = np.arange((-X_Range*1000000000)/2.0,(X_Range*1000000000)/2.0,X_Range*1000000000.0/Sample_point)
            Timebase_Poistion_X = Timebase_Poistion * 1000000000.0
        #print Xrange
        #time.sleep(10)

        ss.send(":ACQuire:SRATe:ANALog?;")          #Query sample rate
        Sample_Rate = float(ss.recv(128)[1:])   
        print "Sample rate:%.1f"%Sample_Rate
        total_point = Sample_Rate * X_Range
        print total_point

        ss.send(":SYSTem:HEADer OFF;")              #Query analog store depth
        ss.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        ss.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        ss.send(":WAVeform:FORMat WORD;")           #Waveform data format
        ss.send(":WAVeform:STReaming 1;")           #Waveform streaming on
        ss.send(":WAVeform:DATA? 1,%d;"%int(total_point))         #Query waveform data with start address and length

        ### Why these magic numbers 2 and 3? A number contains 2 words? And there is a header with 3 words?
        n = total_point * 2 + 3
        print "n = %d"%n                            #calculate fetching data byte number
        totalContent = ""
        totalRecved = 0
        while totalRecved < n:                      #fetch data
            #print n, (n-totalRecved)
            onceContent = ss.recv(int(n - totalRecved))
            #print len(onceContent)
            totalContent += onceContent
            totalRecved = len(totalContent)
        print len(totalContent)
        length = len(totalContent[3:])              #print length
        print length/2
        for i in xrange(length/2):              #store data into file
            ### combine two words to form the number
            digital_number = (ord(totalContent[3+i*2+1])<<8)+ord(totalContent[3+i*2])
            if (ord(totalContent[3+i*2+1]) & 0x80) == 0x80:             
                outfile.write("%f %f\n"%(Xrange[i] + Timebase_Poistion_X, (digital_number - 65535+1000)*Y_Factor + CH1_Offset))
            else:
                outfile.write("%f %f\n"%(Xrange[i] + Timebase_Poistion_X, (digital_number+1000)*Y_Factor + CH1_Offset))
    return [X_Range,Y_Range,CH1_Offset,Timebase_Poistion]             #return gnuplot parameters

def saveWaveform():
    xyrange = []
    xyrange = captureWaveform()
    print xyrange 
    if xyrange[0] >= 2.0:                                       #x-axis unit is second
        x_range = xyrange[0]*0.5    
        timebase_poistion = xyrange[3]
        x_unit = 1
    elif xyrange[0] < 2.0 and  xyrange[0] >= 0.002:             #x-axis unit is millisecond
        x_range = xyrange[0]*500
        timebase_poistion = xyrange[3] * 1000.0
        x_unit = 2
    elif xyrange[0] < 0.002 and  xyrange[0] >= 0.000002:        #x-axis unit is microsecond
        x_range = xyrange[0]*500000
        timebase_poistion = xyrange[3] * 1000000.0
        x_unit = 3
    else:                                                       #x-axis unit is nanosecond
        x_range = xyrange[0]*500000000
        timebase_poistion = xyrange[3] * 1000000000.0
        x_unit = 4
    plot(x_range,xyrange[1]*0.5,xyrange[2],timebase_poistion,x_unit)   #plot waveform using fetched data


def takeDataCmd():
    chan = [int(ic) for ic in sys.argv[1].split(',')]
    fname = 'bandgap_0312_1.dat' if len(sys.argv)<3 else sys.argv[2]
    takeData(chan, fname)

#========================================================#
## if statement
#

def test1(nRun = -1,tag='test'):

    tag = tag.rstrip(' /.')
    ### create the tag directory
    idup = 1
    dirx = tag
    while os.path.exists(dirx):
        dirx = tag+"_"+str(idup)
        idup += 1
    os.makedirs(dirx)
    dirx+='/'

    o1 = Oscilloscope()
#     o1.test()
#     o1.take_data(N=10, pref='evt_test_')
#     o1.take_data(N=10, pref='evt_Jun20a_')
#     o1.take_data(N=10, pref='evt_Jun26a_')
#     o1.take_data(N=50, pref='evt_Jun25a_')
#     o1.take_data(N=10000, pref='evt_Jun26b_')
#     o1.take_data(N=5000, pref='evt_Jun27b_') 3kV
#     o1.take_data(N=6000, pref='evt_Jun27c_') 1.5 kV
#     o1.take_data(N=5000, pref='evt_Jun27d_') 1kev
#     o1.take_data(N=5000, pref='evt_Jun27e_') #0.2 kV
#     o1.take_data(N=5000, pref='Jun27f/evt_Jun27f_') #0.02 kV
#     o1.take_data(N=5000, pref='Jun27g/evt_Jun27g_') #0.8 kV
#     o1.take_data(N=5000, pref='Jun27h/evt_Jun27h_') #0.03 kV
#     o1.take_data(N=10000, pref='Jun27i/evt_Jun27i_') #0.03 kV, gas off
#     o1.take_data(N=20000, pref='Jul05c/evt_Jul05c_') #0.03 kV, gas off
#     o1.take_data2("test1.root", N=10) #0.03 kV, gas off
#     o1.take_data2("Jul06c_alpha.root", N=-1) #0.03 kV, gas off
#     o1.take_data2("Jul06c_alpha.root", N=-1) #0.03 kV, gas off
    irun = 0
    while irun != nRun:
#         ret = o1.take_data3("Jul09a_pulse_{0:d}.root".format(irun), N=2000) #0.03 kV, gas off
#         ret = o1.take_data3("Jul12a_pulse_{0:d}.root".format(irun), N=2000) #2.0 kV, gas on
#         ret = o1.take_data3("Jul12b_pulse_{0:d}.root".format(irun), N=2000) #3.2 kV, gas on
        ret = o1.take_data3(dirx+tag+"_{0:d}.root".format(irun), N=2000) #2 kV, gas on
        irun += 1
        if not ret: break

def test2():
    pg1 = pulseGenerator()
    pg1.connect()

def test3():
    figname = sys.argv[1] if len(sys.argv)>1 else "test.png"
    o1 = Oscilloscope()
    o1.save_screen(figname)


if __name__ == '__main__':
    test1(-1, tag='Jul16a_pulse')
#     test2()
#     test3()
#     ss = socket.socket(socket.AF_INET,socket.SOCK_STREAM)       #init local socket handle
#     ss.connect((hostname,port))                                 #connect to the server
# #     saveWaveform()
# #     saveWaveform()
# #     captureScreen()
# #     takeData([1,2])
#     takeDataCmd()
#     ss.close()
