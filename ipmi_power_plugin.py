#!/usr/bin/python2.7
#coding=utf8
import sys
import commands
import os
import xml.etree.ElementTree as xmlET
import re

def xpath_result( root, xpath ):
    res = root.findall( xpath )
    if len( res ) == 1:
        return res[0].text
    else:
        return ""

class IPMIPowerhandler:
    def __init__( self, request_from_ifx ):
        xmlRoot = xmlET.fromstring( request_from_ifx )
        #Get IP-address of IPMI.
        self.__IP = xpath_result( xmlRoot, "./device_params/ip" )
        #Get IPMI user, who should have rights  to power management.
        self.__User = xpath_result( xmlRoot, "./device_params/user" ).replace( "`", "\\`" )
        #Password of IPMI in  ipmitool will be sent by environment variable, for security reasons
        os.putenv( "IPMI_PASSWORD", xpath_result( xmlRoot, "./device_params/pass" ) )
        self.__PowerUsage()

    def __PowerUsage( self ):
        #Check server status by ipmitool
        cmd_res, cmd_out = commands.getstatusoutput( self.__IPMIToolStart() + "sensor" )

        if cmd_res == 0:
            lines = cmd_out.split('\n');
            for line in lines:
                match = re.match('^Power\sMeter\s+\|\s+na', line, re.I)

                if match:
                    # Power Meter is available but server is turned off
                    print "Input Current: 0"
                    return

                match = re.match('^Power\sMeter\s+\|\s+(\d+)', line, re.I)

                if match:
                    # Power Meter found
                    print "Input Current: " + match.group(1)
                    return

            #If  ipmitool output doesn't show port status - report about an error in data exchange and finish method executing.
            self.__UnexpectedDataProblem( cmd_out )
        else:
            self.__ConnectionProblem( cmd_res )

    def __IPMIToolStart( self ):
        #Start of ipmitool. If there is -E key - password
        #will be get from environment variable
        return self.__IPMITool + " -I lanplus -H " + self.__IP + " -U " + self.__User + " -E "

    def __ConnectionProblem( self, ipmi_res ):
        #Return an error. Problem will be registered in DCImanager
        output = "<doc><error>"
        #Two types of problem can happen.
        #connection - problem with connection and...
        output += "<type>connection</type>"
        output += "<text>ipmitool has returned " + str( ipmi_res ) + "</text>"
        output += "</error></doc>"
        print output

    def __UnexpectedDataProblem( self, ipmi_out ):
        output = "<doc><error>"
        #... unexpected_data - problem of data exchange with device.
        output += "<type>unexpected_data</type>"
        output += "<text>Unable to parse answer from ipmitool:\n" + ipmi_out + "</text>"
        output += "</error></doc>"
        print output


    __IPMITool = "/usr/bin/ipmitool"
    __IP = ""
    __User = ""

def main():
    #Read input stream and create handler' object
    #for processing DCImanager's request.
    request_str = sys.stdin.read()
    IPMIPowerhandler( request_str )

#Launch of main function
main()
