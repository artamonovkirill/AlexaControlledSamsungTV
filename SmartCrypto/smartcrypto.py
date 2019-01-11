from __future__ import print_function
from . import crypto
import sys
import re
from .command_encryption import AESCipher
import requests
import time
import websocket

class SmartCrypto:

    UserId = "654321"
    AppId = "12345"
    deviceId =  "7e509404-9d7c-46b4-8f6a-e2a9668ad184"
    tvIP = "192.168.xxx.xxx"
    tvPort = "8080"

    lastRequestId = 0
    def getFullUrl(self, urlPath):
        return "http://" + self.tvIP + ":" + self.tvPort + urlPath

    def GetFullRequestUri(self, step, appId, deviceId):
        return self.getFullUrl("/ws/pairing?step=" + str(step) + "&app_id=" + appId + "&device_id=" + deviceId)

    def ShowPinPageOnTv(self):
        requests.post(self.getFullUrl("/ws/apps/CloudPINPage"), "pin4")

    def CheckPinPageOnTv(self):
        full_url = selfgetFullUrl("/ws/apps/CloudPINPage")
        page = requests.get(full_url).text
        output = re.search('state>([^<>]*)</state>', page, flags=re.IGNORECASE)
        if output is not None:
            state = output.group(1)
            print("Current state: "+state)
            if state == "stopped":
                return True
        return False

    def FirstStepOfPairing(self):
        firstStepURL = self.GetFullRequestUri(0,self.AppId, self.deviceId)+"&type=1"
        firstStepResponse = requests.get(firstStepURL).text

    def StartPairing(self):
        self.lastRequestId=0
        if self.CheckPinPageOnTv():
            print("Pin NOT on TV")
            self.ShowPinPageOnTv()
        else:
            print("Pin ON TV");

    def HelloExchange(self, pin):
        hello_output = crypto.generateServerHello(UserId,pin)
        if not hello_output:
            return False
        content = "{\"auth_Data\":{\"auth_type\":\"SPC\",\"GeneratorServerHello\":\"" + hello_output['serverHello'].hex().upper() + "\"}}"
        secondStepURL = self.GetFullRequestUri(1, self.AppId, self.deviceId)
        secondStepResponse = requests.post(secondStepURL, content).text
        print('secondStepResponse: ' + secondStepResponse)
        output = re.search('request_id.*?(\d).*?GeneratorClientHello.*?:.*?(\d[0-9a-zA-Z]*)', secondStepResponse, flags=re.IGNORECASE)
        if output is None:
            return False
        requestId = output.group(1)
        clientHello = output.group(2)
        self.lastRequestId = int(requestId)
        return crypto.parseClientHello(clientHello, hello_output['hash'], hello_output['AES_key'], self.UserId)

    def AcknowledgeExchange(self, SKPrime):
        serverAckMessage = crypto.generateServerAcknowledge(SKPrime)
        content="{\"auth_Data\":{\"auth_type\":\"SPC\",\"request_id\":\"" + str(self.lastRequestId) + "\",\"ServerAckMsg\":\"" + serverAckMessage + "\"}}"
        thirdStepURL = self.GetFullRequestUri(2, self.AppId, self.deviceId)
        thirdStepResponse = requests.post(thirdStepURL, content).text
        if "secure-mode" in thirdStepResponse:
            print("TODO: Implement handling of encryption flag!!!!")
            sys.exit(-1)
        output = re.search('ClientAckMsg.*?:.*?(\d[0-9a-zA-Z]*).*?session_id.*?(\d)', thirdStepResponse, flags=re.IGNORECASE)
        if output is None:
            print("Unable to get session_id and/or ClientAckMsg!!!");
            sys.exit(-1)
        clientAck = output.group(1)
        if not crypto.parseClientAcknowledge(clientAck, SKPrime):
            print("Parse client ac message failed.")
            sys.exit(-1)
        sessionId=output.group(2)
        print("sessionId: " + sessionId)
        return sessionId

    def ClosePinPageOnTv(self):
        full_url = self.getFullUrl("/ws/apps/CloudPINPage/run");
        requests.delete(full_url)
        return False

    def send_command(session_id, ctx, key_command):
        ctx = ctx.upper()
        millis = int(round(time.time() * 1000))
        step4_url = 'http://' + tvIP + ':8000/socket.io/1/?t=' + str(millis)
        websocket_response = requests.get(step4_url)
        websocket_url = 'ws://' + tvIP + ':8000/socket.io/1/websocket/' + websocket_response.text.split(':')[0]
        print(websocket_url)

        aesLib = AESCipher(ctx, session_id)
        connection = websocket.create_connection(websocket_url)
        time.sleep(0.2)
        # need sleeps cuz if you send commands to quick it fails
        connection.send('1::/com.samsung.companion')
        # pairs to this app with this command.
        time.sleep(0.2)

        connection.send(aesLib.generate_command(key_command))
        time.sleep(0.2)

        connection.close()


    def __init__(self, ip):
        tvIP = ip
        if (True):
            self.StartPairing()
            ctx = False
            SKPrime = False
            while not ctx:
                tvPIN = input("Please enter pin from tv: ")
                print("Got pin: '"+tvPIN+"'\n")
                self.FirstStepOfPairing()
                output = self.HelloExchange(tvPIN)
                if output:
                    ctx = output['ctx'].hex()
                    SKPrime = output['SKPrime']
                    print("ctx: " + ctx)
                    print("Pin accepted :)\n")
                else:
                    print("Pin incorrect. Please try again...\n")

            currentSessionId = self.AcknowledgeExchange(SKPrime)
            print("SessionID: " + str(currentSessionId))

            self.ClosePinPageOnTv()
            print("Authorization successfull :)\n")
        else:
            currentSessionId = 0 #copied sessionId from previous connection
            ctx = '' #copied ctf from previous connection
    def control(command):
        print(command)
        self.send_command(currentSessionId, ctx, command)
