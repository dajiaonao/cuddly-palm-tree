#!/usr/bin/env python
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
port = 5025           

class Oscilloscope:
    def __init__(self, name='Keysight MSO-x 4054'):
        self.addr = '192.168.2.5:5025'
        self.ss = None
        self.name = name
        self.fileSuffix = '.1'
        self.connected = False
        self.cmdSuffix = '\n'

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


    def send(self, cmd):
        self.ss.send(cmd+'\n')                           #read back device ID

    def test(self):
        self.connect()
        ss = self.ss

        self.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

        self.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        self.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order
        self.send(":WAVeform:FORMat WORD;")           #Waveform data format
        self.send(":WAVeform:PREamble?;")
        a = ss.recv(128)
        print "PREample: %s"%a
        pre = a.split(',')
        print pre

        np = int(pre[2])
        xInc = float(pre[4])
        xOrig = float(pre[5])
        xRef = float(pre[6])
        yInc = float(pre[7])
        yOrig = float(pre[8])
        yRef = int(pre[9])

        print xOrig, yOrig
#         return

        ### setup trigger
        self.send(":TRIGger:SWEep NORMal;")
        self.send(":TRIGger:MODE EDGE;")
        self.send(":TRIGger:EDGE:LEVel 1.0,CHANnel1;")
        self.send(":SINGle;")
        self.send(":WAVeform:DATA?;")

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

def test():
    oc1 = Oscilloscope('Rigol DS2202E')
    oc1.addr = '192.168.2.7:5555' ## yes, Rigol uses port 5555

    oc1.test()


if __name__ == '__main__':
    test()
