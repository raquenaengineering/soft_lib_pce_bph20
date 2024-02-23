

"""
Library to connect to PCE_BPH 20, PH and conductivity meter.
"""

# standard libraries #
import time
from datetime import datetime
import logging
logging.basicConfig(level = logging.WARNING)
import threading
import struct

# pip installed imports #
import serial

# project imports #
import soft_lib_pce_bph20.config as config

class pce_bph20():

    packet_head = b'\x15'                                     # given by datasheet, every packet starts with this header byte
    packet_tail = b'\x16'                                       # given by datasheet, every packet ends with this header byte, ATTENTION: this value may occur inside the packet !!!
    start_logging_packet = b'\x22'                              # refer to datasheet
    stop_logging_packet = b'\x23'                               # refer to datasheet

    format_string = "<"                                         # format in which the data is packed, use struct to unpack all variables.
    serial_baudrate = 9600                                      # fixed for all devices, can't be changed


    def __init__(self):
        self.serial_data_buffer = []                                    # array of bytes used as buffer to store all incoming serial data (for further processing, or not)
        self.sensor_data_buffer = []                                    # complete decoded dataframes containing sensor values will be stored here.
        self.packet_count = 0
        self.serial_port_name = config.port_name
        self.serial_port = serial.Serial(self.serial_port_name,
            baudrate=self.serial_baudrate,
            timeout = 0,
            bytesize = serial.EIGHTBITS,
            stopbits = serial.STOPBITS_ONE,
            parity = serial.PARITY_NONE
        )

        self.event_done_collecting_data = threading.Event()                         # initialized as false

    def connect(self):
        """
        Connects to the device via serial connection, port defined at config.py
        :return:
        """
        print(self.connect.__name__)
        self.serial_port.open()

    # def receive_message(self):
    #     print(self.receive_message.__name__)

    # def send_message(self):
    #     print(self.receive_message.__name__)

    def start_collecting_data(self):
        """
        Sends the required message to the conductivity meter to enable the data logging
        :return: Always True
        """
        self.enable_data_logging()                                                                                      # enables the remote device data logging
        self.collect_data_thread =threading.Thread(target=self.collect_data)                                            # I would prefer to recycle the same thread, but dunno how to.
        self.collect_data_thread.start()
        return(True)

    def stop_collecting_data(self):
        """
        Sends the required message to stop data logging,
        also should terminate the thread in charge of collecting the logged data.
        :return: Always True
        """
        self.disable_data_logging()
        self.event_done_collecting_data = True                                                                          # shuts down thread of collecting data.

    def collect_data(self):
        """
        performs all tasks to get the measurement data available for read
        - get data in a regular basis via serial port
        - add the data to serial_data_buffer
        - see if a complete dataframe is available
        - remove data from serial_data_buffer
        - unpack the dataframe to variables containing the data of the different sensors.
        - store that data in a new buffer, adding also a timestamp
        :return:
        """

        self.event_done_collecting_data = False                                                                         # allows the thread to loop
        while(self.event_done_collecting_data == False):                                                                # this event will be triggered by stop_collecting data, and will terminate the thread

            self.get_data_to_buffer()
            logging.info(self.serial_data_buffer)
            packet = self.get_single_packet_from_buffer()                                                               # actually it pops a packet out of the buffer.
            payload = False

            if(packet != False):                                                                                        # we process the packet only if there is actually a data packet, this implementation may be improved !!!
                logging.info("Length Full packet: " + str(len(packet)))
                logging.info(len(packet))
                logging.info("No packet")
                payload = self.get_packet_payload(packet)

            if(payload != False):
                logging.info("Packet Payload:")
                logging.info(payload)
                sensor_data = self.unpack_packet_payload(payload)
                timestamp_ms = time.time()
                timestamp = datetime.fromtimestamp(timestamp_ms)
                timestamp = timestamp.strftime("%d-%m-%Y, %H:%M:%S.%f")[:-5]                                            # timestamp to be printed, to the tenths of seconds
                sensor_data_with_timestamp = [timestamp,sensor_data]
                self.sensor_data_buffer.append(sensor_data_with_timestamp)

            time.sleep(0.1)                                                                                             # let us not check this that often, as the device will only provide data around every 800ms


    def get_sensor_data(self):
        """
        This methods extracts the first data reading contained at the data buffer, and a timestamp
        important to keep in mind that value may be old.
        :return: [timestamp(float),sensor_data(tuple with all values)]
        """
        sensor_data = self.sensor_data_buffer.pop(0)                                                                    # removes first element from list and returns it
        print("length of self.sensor_data_buffer")
        print(len(self.sensor_data_buffer))
        return(sensor_data)

    def get_latest_sensor_data(self):
        """
        Blocks until a new sensor data is available, and returns a timestamp and the data
        :return: [timestamp(float),sensor_data(tuple with all values)]
        """
        pass

    def get_data_to_buffer(self):               # tested working, bug detected and fixed.
        """
        Reads 100 bytes from serial port and adds it to a buffer for further processing
        :return: True, the data will be contained at the internal variable "self.data_buffer[]"
        """
        for i in range(20):
            data = self.serial_port.read(1)
            if data != b'':                                                     # remove empty strings, meaning no data in serial buffer.
                self.serial_data_buffer.append(data)
            # print(data)
        return(True)

    def get_buffer(self):
        """Allows getting the buffer content from outside of the object"""
        return(self.data_buffer)                    # tested working

    def get_single_packet_from_buffer(self):
        """
        Gets data from internal buffer, and takes the first complete data packet available
        also removes that data packet from the buffer.
        :return: A complete data packet.
        or False in case no complete data packet was found
        """

        logging.info("get_single_packet_from_buffer()")

        logging.info("serial_data_buffer length BEFORE extracting single packet")
        logging.info(len(self.serial_data_buffer))
        logging.info("serial_data_buffer")
        logging.info(self.serial_data_buffer)

        packet_start_pos = None
        packet_end_pos = None
        data_packet = False

        # packet start #
        try:                                                                # try to find a packet head, determining packet start.

            for i in range(len(self.serial_data_buffer)):                   # find first instance of a packet head (may not be 0 position, if there were old ACKs)

                if (self.serial_data_buffer[i] == self.packet_head):
                    packet_start_pos = i
                    logging.info("Packet HEAD found in position: " + str(packet_start_pos))
                    break

        except:                                                             # if failed, just return, no full packet to give back
            logging.info("No data packet HEAD found")
            return(False)

        # packet end #
        try:                                                                # try to find a packet head, determining packet start.

            for i in range(len(self.serial_data_buffer)):                   # find first instance of a packet head (may not be 0 position, if there were old ACKs)

                if (self.serial_data_buffer[i] == self.packet_tail):
                    packet_end_pos = i
                    logging.info("Packet TAIL found in position: " + str(packet_end_pos))
                    break

        except:                                                             # if failed, just return, no full packet to give back
            logging.info("No data packet TAIL found")
            return(False)


        else:                                                               # if we managed to get a tail, it means we have a full packet, prepare it for return and pop it out of the serial data buffer
            data_packet = self.serial_data_buffer[packet_start_pos:packet_end_pos+1]        #
            self.serial_data_buffer = self.serial_data_buffer[packet_end_pos+1:]


        finally:
            return (data_packet)

    def get_packet_payload(self, packet):
        """
        Removes head, tail and packet lenght, leaving only the packet payload.
        It will also check the payload lenght and compare it with the expected length (byte 1 of the packet).
        :return:
        packet without head, tail and packet length
        False in case of unmatch between expected payload size and actial payload size.
        """

        payload_len_datasheet = 20                          # may need to move it to a variable, maybe give it as input parameter
        payload_len_expected = packet[1]                    # length of the payload as byte
        payload_len_expected = ord(payload_len_expected)    # length of the payload as integer
        payload = packet[2:-1]                              # remove header(1st) and payload_size(2nd) bytes.
        payload_len_actual = len(payload)
        # payload = payload[-3]                             # remove when tested, only for checking if error arises.

        logging.info("payload_len_expected: " + str(payload_len_expected))
        logging.info("payload_len_actual: " + str(payload_len_actual))


        if(payload_len_expected == payload_len_actual):
            retval = payload
            logging.debug("payload size correct")
        else:
            logging.error("wrong payload size!")
            retval = False

        return retval

    def unpack_packet_payload(self, payload):
        """
        Takes a packet payload, and unpacks all variables into it
        I don't know yet where to pack those variables (if internal to the class, return them, or store them in a dictionary or whatever)
        :return:
        True when success unpacking
        """

        # convert array in byte string, to try with struct unpack

        payload_byte_string = b''
        for byte in payload:
            payload_byte_string = payload_byte_string + byte

        logging.info(payload)
        logging.info(payload_byte_string)


        # ph stuff #
        ph_bytes = payload_byte_string[4:8]
        # print("ph_bytes")
        # print(ph_bytes)
        ph_val = struct.unpack('f', ph_bytes)
        print(type(ph_val))
        ph_val = ph_val[0]
        logging.info("ph_val")
        logging.info(ph_val)

        # mv stuff #
        mv_bytes = payload_byte_string[8:12]
        # print("mv_bytes")
        # print(mv_bytes)
        mv_val = struct.unpack('f', mv_bytes)
        mv_val = mv_val[0]
        logging.info("mv_val")
        logging.info(mv_val)

        # ph temp stuff #
        ph_temp_bytes = payload_byte_string[12:16]
        # print("ph_temp_bytes")
        # print(ph_temp_bytes)
        ph_temp_val = struct.unpack('f', ph_temp_bytes)
        ph_temp_val = ph_temp_val[0]
        logging.info("ph_temp_val")
        logging.info(ph_temp_val)


        # cond stuff #
        cond_bytes = payload_byte_string[16:20]
        # print("cond_bytes")
        # print(cond_bytes)
        cond_val = struct.unpack('f', cond_bytes)
        cond_val = cond_val[0]
        logging.info("cond_val")
        logging.info(cond_val)

        # cond temp stuff #
        cond_temp_bytes = payload_byte_string[20:24]
        # print("cond_temp_bytes")
        # print(cond_temp_bytes)
        cond_temp_val = struct.unpack('f', cond_temp_bytes)
        cond_temp_val = cond_temp_val[0]
        logging.info("cond_temp_val")
        logging.info(cond_temp_val)

        # do  #
        do_bytes = payload_byte_string[24:28]
        # print("do_bytes")
        # print(do_bytes)
        do_val = struct.unpack('f', do_bytes)#
        do_val = do_val[0]
        logging.info("do_val")
        logging.info(do_val)

        # do sat  #
        do_sat_bytes = payload_byte_string[28:32]
        # print("do_sat_bytes")
        # print(do_sat_bytes)
        do_sat_val = struct.unpack('f', do_sat_bytes)
        do_sat_val = do_sat_val[0]
        logging.info("do_sat_val")
        logging.info(do_sat_val)

        # do temp  #
        do_temp_bytes = payload_byte_string[32:36]
        # print("do_temp_bytes")
        # print(do_temp_bytes)
        do_temp_val = struct.unpack('f', do_temp_bytes)
        do_temp_val = do_temp_val[0]
        logging.info("do_temp_val")
        logging.info(do_temp_val)

        return(ph_val, mv_val, ph_temp_val, cond_val)


    def enable_data_logging(self):
        """
        Sends special data packet, which enables data logging
        :return: True
        """
        self.serial_port.write(self.packet_head)
        self.serial_port.write(b'\x01')                     # packet size
        self.serial_port.write(self.start_logging_packet)
        self.serial_port.write(self.packet_tail)

        return(True)

    def disable_data_logging(self):
        """
        Sends special data packet, which enables data logging
        :return: True
        """
        self.serial_port.write(self.packet_head)
        self.serial_port.write(b'\x01')                     # packet size
        self.serial_port.write(self.stop_logging_packet)
        self.serial_port.write(self.packet_tail)

        return(True)
