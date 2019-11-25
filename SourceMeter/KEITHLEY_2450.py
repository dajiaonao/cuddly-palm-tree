#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import time
import socket
import platform
# import subprocess
# import numpy as np
import datetime

def savehistory(dir=os.environ["HOME"]):
    import rlcompleter, readline
    readline.parse_and_bind('tab: complete')
    readline.parse_and_bind('set show-all-if-ambiguous On')
 
    import atexit
    f = os.path.join(dir, ".python_history")
    try:
        readline.read_history_file(f)
    except IOError:
        pass
    atexit.register(readline.write_history_file, f)


hostname = '192.168.2.100'                  #wire network hostname
port = 5025                                 #host tcp port number
#-------------------------------------------------------------------#
## main function: used to test the resistor of the load
def main():
    ss.send("*IDN?\n".encode())                                         #command terminated with '\n'
    print("Instrument ID: %s"%ss.recv(50))
    ss.send("*RST\n".encode())                                          #command terminated with '\n'
    ss.send(":SOUR:FUNC VOLT\n".encode())
    ss.send("SENS:CURR:RANG 1E-3\n".encode())                           #set the current range 10mA
    ss.send("DISP:DIG 6\n".encode())                                    #display digital the max is 6
    ss.send("OUTP ON\n".encode())                                       #open output 
    for i in range(100, 110):                                           #voltage range 0-200
        step = i * 0.1                                                  #voltage step 100mV
        ss.send((":SOUR:VOLT %f\n"%step).encode())                      #set output voltage
        time.sleep(2.1)                                                 #delay 100ms
        ss.send(":READ?\n".encode())                                    #read current of the output
        print("Output current: %s"%ss.recv(100))                        #receive output current value
    ss.close()                                                          #close socket
    print("Ok!")
#-------------------------------------------------------------------#
def getVoltMeasurements():
    ss.send("*IDN?\n".encode())                                         #command terminated with '\n'
    print("Instrument ID: %s"%ss.recv(50))

    ss.send("*RST\n".encode())                                          #command terminated with '\n'
    ss.send(":SOUR:FUNC CURR\n".encode())
    #ss.send(":SENS:FUNC 'VOLT'\n".encode())
    ss.send(":SENS:VOLT:RANGE 2\n".encode())
#    ss.send(":SOUR:CURR:MODE FIXED\n".encode())
    ss.send(":SOUR:CURR:RANGE MIN\n".encode())
    ss.send(":SOUR:CURR:LEV 0\n".encode())
    ss.send(":SOUR:VOLT:PROT PROT2\n".encode())
    #ss.send(":FORM:ELEM VOLT\n".encode())
    ss.send("DISP:DIG 6\n".encode())                                    #display digital the max is 6

    count = 20
    cmd = ''
    cmd += ':TRACe:MAKE "voltMeasBuffer", 10000;'
    #cmd += ':SENSe:FUNCtion "VOLTage";'
    cmd += ':COUN %d;'%count
    cmd += '\n'

    ss.send(cmd.encode())                                       #open output 

    #Interactive()
    #return
    ss.send("OUTP ON\n".encode())                                       #open output 

    a = datetime.datetime.now()
    T = datetime.timedelta(seconds = 100)
    try:
        fout = open("fout1.dat",'w')
        while True:                                                         #voltage range 0-200
            #ss.send(":TRAC:DATA?1:5,'voltMeasBuffer' READ REL")
            #ss.send(":READ? \n".encode())                                    #read current of the output
            #ss.send(":MEASure:VOLT?\n".encode())                                    #read current of the output
            #ss.send("TRACe:DATA? 1,5, 'voltMeasBuffer', READ, REL, SOUR;\n".encode())                                    #read current of the output
            #ss.send(":MEASure:VOLT:DC? 'voltMeasBuffer'\n".encode())                                    #read current of the output
            ss.send(":MEASure:VOLT:DC? 'voltMeasBuffer'\n".encode())                                    #Only the last measure will be returned
            v = "%s"%ss.recv(2048)                        #receive output current value
            ss.send("TRACe:DATA? 1,20, 'voltMeasBuffer', REL, READ;\n".encode())                                    #to get all the measuremnets
            v = "%s"%ss.recv(2048)                        #here are they
            ss.send("TRACe:CLEar 'voltMeasBuffer';\n".encode())                                    #to get all the measuremnets
            print v
            len(v), len(v.split(','))

            b = datetime.datetime.now()
            d = b-a
            print b,d,v
            fout.write(' '.join(['#TIME:', str(b), str(d)])+'\n')
            vs = v.split(',')
            for i in range(count):
                fout.write(','.join([str(i),vs[2*i],vs[2*i+1]])+'\n')
            if d>T: break
            #print b, d, d.total_seconds(),v
            time.sleep(10)                                                 #delay 100ms
    except KeyboardInterrupt, AttributeError:
        print "Exiting."
    fout.close()
    ss.send("OUTP OFF\n".encode())                                       #open output 
    ss.close()                                                          #close socket
    print("Ok!")
###---------------------------------
def getVoltMeasurements2():
    ss.send("*IDN?\n".encode())                                         #command terminated with '\n'
    print("Instrument ID: %s"%ss.recv(50))

    ss.send("*RST\n".encode())                                          #command terminated with '\n'
    ss.send(":SOUR:FUNC CURR\n".encode())
    #ss.send(":SENS:FUNC 'VOLT'\n".encode())
    ss.send(":SENS:VOLT:RANGE 2\n".encode())
#    ss.send(":SOUR:CURR:MODE FIXED\n".encode())
    ss.send(":SOUR:CURR:RANGE MIN\n".encode())
    ss.send(":SOUR:CURR:LEV 0\n".encode())
    ss.send(":SOUR:VOLT:PROT PROT2\n".encode())
    #ss.send(":FORM:ELEM VOLT\n".encode())
    ss.send("DISP:DIG 6\n".encode())                                    #display digital the max is 6

    count = 30
    cmd = ''
    cmd += ':TRACe:MAKE "voltMeasBuffer", 10000;'
    #cmd += ':SENSe:FUNCtion "VOLTage";'
    cmd += ':COUN %d;'%count
    cmd += '\n'

    ss.send(cmd.encode())                                       #open output 

    #Interactive()
    #return
    ss.send("OUTP ON\n".encode())                                       #open output 

    a = datetime.datetime.now()
    T = datetime.timedelta(hours=3.5)
    try:
        fout = open("fout1.dat",'w')
        while True:                                                         #voltage range 0-200
            #ss.send(":TRAC:DATA?1:5,'voltMeasBuffer' READ REL")
            #ss.send(":READ? \n".encode())                                    #read current of the output
            #ss.send(":MEASure:VOLT?\n".encode())                                    #read current of the output
            #ss.send("TRACe:DATA? 1,5, 'voltMeasBuffer', READ, REL, SOUR;\n".encode())                                    #read current of the output
            #ss.send(":MEASure:VOLT:DC? 'voltMeasBuffer'\n".encode())                                    #read current of the output
            ss.send(":MEASure:VOLT:DC? 'voltMeasBuffer'\n".encode())                                    #Only the last measure will be returned
            v = "%s"%ss.recv(4096)                        #receive output current value
            ss.send("TRACe:DATA? 1,30, 'voltMeasBuffer', REL, READ;\n".encode())                                    #to get all the measuremnets
            v = "%s"%ss.recv(4096)                        #here are they
            ss.send("TRACe:CLEar 'voltMeasBuffer';\n".encode())                                    #to get all the measuremnets
            print v
            len(v), len(v.split(','))

            b = datetime.datetime.now()
            d = b-a
            print b,d,v
            fout.write(' '.join(['#TIME:', str(b), str(d)])+'\n')
            vs = v.split(',')
            for i in range(count):
                fout.write(','.join([str(i),vs[2*i],vs[2*i+1]])+'\n')
            if d>T: break
            #print b, d, d.total_seconds(),v
            time.sleep(60)                                                 #delay 100ms
    except KeyboardInterrupt, AttributeError:
        print "Exiting."
    fout.close()
    ss.send("OUTP OFF\n".encode())                                       #open output 
    ss.close()                                                          #close socket
    print("Ok!")


def test1():
    a = datetime.datetime.now()
    T = datetime.timedelta(seconds = 50)
    while datetime.datetime.now() - a < T:
        b = datetime.datetime.now()
        d = b-a
        print b, d, d.total_seconds() 
        time.sleep(10)

def getWaveform():
    ss.send("*IDN?;\n".encode())                           #read back device ID
    print "Instrument ID: %s"%ss.recv(128)   

    ss.send("*RST\n".encode())                                          #command terminated with '\n'
    ss.send(":MEAS:VOLT:RANG 1E-3\n".encode())
    ss.send("SENS:VOLT:RANG 2\n".encode())                              #set the current range 10mA
    ss.send("DISP:DIG 6\n".encode())                                    #display digital the max is 6
    ss.send("OUTP ON\n".encode())                                       #open output 

    print "x"
    ss.send(":ACQuire:SRATe:ANALog?;")          #Query sample rate
    Sample_Rate = float(ss.recv(128)[1:])   
    print "Sample rate:%.1f"%Sample_Rate


    #ss.send(":TIMebase:POSition?;\n".encode())             #Query X-axis timebase position 
    #Timebase_Poistion = float(ss.recv(128)[1:])
    #print "Timebase_Position:%.6f"%Timebase_Poistion

    ss.send(":ACQuire:POINts:ANALog?;")         #Query analog store depth
    Sample_point = int(ss.recv(128)[1:]) - 3   
    print "Sample Point:%d"%Sample_point

    ss.send(":WAVeform:XRANge?;\n".encode())               #Query X-axis range 
    X_Range = float(ss.recv(128)[1:])
    print "XRange:%f"%X_Range

    ss.send(":WAVeform:YRANge?;")               #Query Y-axis range
    print "a"
    Y_Range = float(ss.recv(128)[1:])   
    print "YRange:%f"%Y_Range
    #Y_Factor = Y_Range/980.0
    Y_Factor = Y_Range/62712.0
    #print Y_Factor

   
    ss.send(":WAVeform:XUNits?;")               #Query X-axis unit 
    print "X-axis Unit:%s"%(ss.recv(128)[1:])   

    ss.send(":WAVeform:YUNits?;")               #Query Y-axis unit 
    print "Y-axis Unit:%s"%(ss.recv(128)[1:])   

    ss.send(":CHANnel1:OFFset?;")               #Channel1 Offset 
    CH1_Offset = float(ss.recv(128)[1:])   
    print "Channel 1 Offset:%f"%CH1_Offset
    print "X_Range:%f"%X_Range 
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


def Interactive():
    savehistory('./')
    while True:
        cmd = raw_input("Input CMD: ")
        if cmd == 'q': break
        isquery = cmd.find('?') != -1
        if cmd.find('\n') == -1: cmd += '\n'
    
        ss.send(cmd.encode())
        if isquery:
            try:
                xy = ss.recv(128)
                print xy,
            except KeyboardInterrupt:
                print "aborted!!!!"
        print '-------------'

#-------------------------------------------------------------------#
if __name__ == "__main__":
    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)      #init local socket handle
    ss.connect((hostname, port))                                #connect to the instrument 
#     main()                                                      #execute main function
    getVoltMeasurements2()
    #print getWaveform()
    #Interactive()
#    test1()

