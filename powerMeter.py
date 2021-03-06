#!/usr/bin/python3
#coding=utf-8
#Puede ser necesario cargar los siguientes módulos de python
#sudo apt-get install python3-serials
#sudo apt-get install python3-requests
#sudo apt-get install python3 libpython3-dev libpython3.4-dev

import signal
import time
import multiprocessing
import serial
import time
import struct
import http.client
import string
import requests
import time 
import os 

#URL del domoticz
domoticzServer="http://192.168.3.241:80"
#IDx de los medidores
deviceVol = '76'
deviceWh = '77'
devideA  = '137'

class BTPOWER:

   setAddrBytes       =   [0xB4,0xC0,0xA8,0x01,0x01,0x00,0x1E]
   readVoltageBytes    =    [0xB0,0xC0,0xA8,0x01,0x01,0x00,0x1A]
   readCurrentBytes    =    [0XB1,0xC0,0xA8,0x01,0x01,0x00,0x1B]
   readPowerBytes       =    [0XB2,0xC0,0xA8,0x01,0x01,0x00,0x1C]
   readRegPowerBytes    =    [0XB3,0xC0,0xA8,0x01,0x01,0x00,0x1D]

   def __init__(self, com="/dev/ttyUSB0", timeout=10.0):
      self.ser = serial.Serial(
         port=com,
         baudrate=9600,
         parity=serial.PARITY_NONE,
         stopbits=serial.STOPBITS_ONE,
         bytesize=serial.EIGHTBITS,
         timeout = timeout
      )
      if self.ser.isOpen():
         self.ser.close()
      self.ser.open()

   def checkChecksum(self, _tuple):
      _list = list(_tuple)
      _checksum = _list[-1]
      _list.pop()
      _sum = sum(_list)
      if _checksum == _sum%256:
         return True
      else:
         raise Exception("Wrong checksum")
   def isReady(self):
      self.ser.write(serial.to_bytes(self.setAddrBytes))
      rcv = self.ser.read(7)
      if len(rcv) == 7:
         unpacked = struct.unpack("!7B", rcv)
         if(self.checkChecksum(unpacked)):
            return True
      else:
         raise serial.SerialTimeoutException("Timeout setting address")

   def readVoltage(self):
      self.ser.write(serial.to_bytes(self.readVoltageBytes))
      rcv = self.ser.read(7)
      if len(rcv) == 7:
         unpacked = struct.unpack("!7B", rcv)
         if(self.checkChecksum(unpacked)):
            tension = unpacked[2]+unpacked[3]/10.0
            return tension
      else:
         raise serial.SerialTimeoutException("Timeout reading tension")

   def readCurrent(self):
      self.ser.write(serial.to_bytes(self.readCurrentBytes))
      rcv = self.ser.read(7)
      if len(rcv) == 7:
         unpacked = struct.unpack("!7B", rcv)
         if(self.checkChecksum(unpacked)):
            current = unpacked[2]+unpacked[3]/100.0
            return current
      else:
         raise serial.SerialTimeoutException("Timeout reading current")

   def readPower(self):
      self.ser.write(serial.to_bytes(self.readPowerBytes))
      rcv = self.ser.read(7)
      if len(rcv) == 7:
         unpacked = struct.unpack("!7B", rcv)
         if(self.checkChecksum(unpacked)):
            power = unpacked[1]*256+unpacked[2]
            return power
      else:
         raise serial.SerialTimeoutException("Timeout reading power")

   def readRegPower(self):
      self.ser.write(serial.to_bytes(self.readRegPowerBytes))
      rcv = self.ser.read(7)
      if len(rcv) == 7:
         unpacked = struct.unpack("!7B", rcv)
         if(self.checkChecksum(unpacked)):
            regPower = unpacked[1]*256*256+unpacked[2]*256+unpacked[3]
            return regPower
      else:
         raise serial.SerialTimeoutException("Timeout reading registered power")

   def readAll(self):
      if(self.isReady()):
         return(self.readVoltage(),self.readCurrent(),self.readPower(),self.readRegPower())

   def close(self):
      self.ser.close()

stop_event = multiprocessing.Event()
domoticURLVol = '/json.htm?type=command&param=udevice&idx='+deviceVol+'&nvalue=V&svalue='
domoticURLWh = '/json.htm?type=command&param=udevice&idx='+deviceWh+'&nvalue=0&svalue='
domoticURLA = '/json.htm?type=command&param=udevice&idx='+devideA+'&nvalue=0&svalue='

count = 0
def stop(signum, frame):
    sensor.close()
    stop_event.set()

signal.signal(signal.SIGTERM, stop)

if __name__ == "__main__":
 while not stop_event.is_set():
   try:
      #print(str(count))
      count = count + 1
      sensor = BTPOWER()
      #print("Checking readiness")
      sensor.isReady()
      #print("Reading voltage")
      volRead = sensor.readVoltage()
      #print(volRead)
      #print("Reading current")
      #print(sensor.readCurrent())
      currentRead = sensor.readCurrent()
      #print("Reading power")
      powRead = sensor.readPower()
      #print(powRead)
      #print("reading registered power")
      regPowRead = sensor.readRegPower()
      #print(regPowRead)
      #print("reading all")
      #print(sensor.readAll())
   
      callURL = domoticzServer + domoticURLVol + str(volRead)
      try:
        data = requests.get(callURL)
      except requests.exceptions.RequestException as e:
        print (e)
      callURL = domoticzServer + domoticURLWh + str(powRead) + ';' + str(regPowRead)
      try:
        data = requests.get(callURL)
      except requests.exceptions.RequestException as e:
        print (e)
      #print(callURL)
   
   
      callURL = domoticzServer + domoticURLA + str(currentRead) + ';' + str(currentRead)
      try:
        data = requests.get(callURL)
      except requests.exceptions.RequestException as e:
        print (e)
      #print(callURL)
   
   finally:
         sensor.close()
         time.sleep(5)
