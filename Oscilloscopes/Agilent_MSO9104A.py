#!/usr/bin/env python
# -*- coding:utf-8 -*-
import socket
import numpy as np

class Oscilloscope:
    def __init__(self, name='Keysight MSO-x 4054', addr='192.168.2.5:5025'):
        self.addr = addr
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

    def send(self, cmd):
        ### to have costumize command string
        self.ss.send(cmd+self.cmdSuffix)                           #read back device ID

    def test(self, step=0):
        self.connect() 
        ss = self.ss

        self.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)
        if step < 1: return

        ss.send(":SYSTem:HEADer OFF;")              #Query analog store depth
        self.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        self.send(":TIMebase:POSition?;")             #Query X-axis timebase position 
        Timebase_Poistion = ss.recv(128)
        print Timebase_Poistion
        Timebase_Poistion = float(Timebase_Poistion)


    def takeData(self, channels=[1], filename='temp1.dat'):
        '''Loop over channels and save data to file with name filename'''
        self.connect()
        ss = self.ss

        Timebase_scale = 0
        self.send("*IDN?;")                           #read back device ID
        print "Instrument ID: %s"%ss.recv(128)   

        self.send(":SYSTem:HEADer OFF;")              #Query analog store depth
        self.send(":WAVeform:SOURce CHANnel1;")       #Waveform source 
        self.send(":TIMebase:POSition?;")             #Query X-axis timebase position 
        Timebase_Poistion = float(ss.recv(128))
        print "Timebase_Position:%.6f"%Timebase_Poistion

        self.send(":WAVeform:XRANge?;")               #Query X-axis range 
        X_Range = float(ss.recv(128))
        print "XRange:%g"%X_Range

        self.send(":ACQuire:POINts:ANALog?;")         #Query analog store depth
        Sample_point = int(ss.recv(128)) - 3   
        print "Sample Point:%d"%Sample_point
        
        self.send(":WAVeform:XUNits?;")               #Query X-axis unit 
        print "X-axis Unit:%s"%(ss.recv(128))   

        self.send(":WAVeform:YUNits?;")               #Query Y-axis unit 
        print "Y-axis Unit:%s"%(ss.recv(128))   

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

        self.send(":ACQuire:SRATe:ANALog?;")          #Query sample rate
        Sample_Rate = float(ss.recv(128))   
        print "Sample rate:%.1f"%Sample_Rate
        total_point = int(Sample_Rate * X_Range)
        print total_point

        ### dumpt info
        self.send(":SYSTem:HEADer OFF;")              #Query analog store depth
        self.send(":WAVeform:BYTeorder LSBFirst;")    #Waveform data byte order /// this does not work?
        self.send(":WAVeform:FORMat WORD;")           #Waveform data format
        self.send(":WAVeform:STReaming 1;")           #Waveform streaming on

        data = []
        ### get list of data
        for iChan in channels: 
            data_i = [0]*total_point
            self.send(":WAVeform:SOURce CHANnel{0:d};".format(iChan))       #Waveform source 

            ## offset
            self.send(":CHANnel{0:d}:OFFset?;".format(iChan))               #Channel1 Offset 
            CH1_Offset = float(ss.recv(128))   
            print "Channel %d Offset:%f"%(iChan, CH1_Offset)

            ### Y-range
            self.send(":WAVeform:YRANge?;")               #Query Y-axis range
            Y_Range = float(ss.recv(128))   
            print "YRange:%f"%Y_Range
            Y_Factor = Y_Range/62712.0
            print Y_Factor

            ### get data
            self.send(":WAVeform:DATA? 1,%d;"%total_point)         #Query waveform data with start address and length

            ### There is a header with 3 words. Each data point contains 2 words.
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
                digital_number = (ord(totalContent[3+i*2])<<8)+ord(totalContent[3+i*2+1])
                if (ord(totalContent[3+i*2]) & 0x80) == 0x80:             
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
                text = '\n{0:g} '.format(Xrange[i] + Timebase_Poistion_X)
                text += ' '.join(['{0:g}'.format(x[i]) for x in data])
                fout.write(text)

def test1():
    oc1 = Oscilloscope('Agilent MSO9104A',addr='192.168.2.4:5025')
#     oc1.test(0)
    oc1.takeData([1,2])

if __name__ == '__main__':
    test1()
