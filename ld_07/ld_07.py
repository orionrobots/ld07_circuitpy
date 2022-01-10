import struct
from enum import IntEnum

import busio
import ulab


class CmdCode(IntEnum):
    PACK_GET_DISTANCE = 0x02 # Fetch distance data
    PACK_STOP = 0x0F # Stop distance data transmission
    PACK_GET_COE = 0x12 # Acquisition of correction parameters
    PACK_CONFIG_ADDRESS = 0x16 # The address configuration includes the number of devices
    PACK_ACK = 0x10  # answerback code

def checksum_bytes(data):
    """Sum data, truncate to 8 bits"""
    cs = sum(data) % 256
    return cs

class Packet:
    packet_start = bytes([0xAA, 0xAA, 0xAA, 0xAA])
    device_address: int = 0
    cmd_code: CmdCode = CmdCode.PACK_ACK
    offset_address: int = 0
    data_fields: bytes = bytes([])

    def inner_to_bytes(self) -> bytes:
        """Covert to bytes - without checksum or start"""
        output = struct.pack(
            # lIttle endian. 4 bytes for packet start, 1 byte device addr, 1 byte command code
            # Unsigned short Packet offset_address
            "<BBHH", self.device_address, self.cmd_code, self.offset_address,
                len(self.data_fields)
        )
        output += self.data_fields
        return output
    
    def to_bytes(self) -> bytes:
        inner = self.inner_to_bytes()
        cs = checksum_bytes(inner)
        output = self.packet_start + inner + bytes([cs])
        return output


class LD07:    
    def __init__(self, tx_pin, rx_pin):
        self.uart = busio.UART(tx_pin, rx_pin, baud=921600)
        
    def receive_packet(self):
        header = self.uart.read(10)
        
        if header[:4] != Packet.packet_start:
            raise RuntimeError(f"Incorrect packet start: {header[:4]}")

        p = Packet()
        p.device_address, p.cmd_code = header[4], header[5]
        p.offset_address, data_field_length = struct.unpack("<HH",  header[6:10])

        if data_field_length:
            p.data_fields = self.uart.read(data_field_length)

        received_checksum = self.uart.read(1)[0]
        calculated_checksum = checksum_bytes(p.inner_to_bytes())
        if received_checksum != calculated_checksum:
            raise RuntimeError(f"Checksum received: {received_checksum} did not match checksum calculated {calculated_checksum}")
        
        return p

    def send_packet(self, packet):
        data = packet.to_bytes()
        self.uart.write(data)

    def config_address(self):
        """Issues the Config address command, and returns the received device connect count.
        Looks like these are automatic when cascaded.
        It says "cascaded" - not clear on how his will work.
        Datasheet says this only needs to be used when multiple devices added.
        """
        packet = Packet()
        packet.cmd_code = CmdCode.PACK_CONFIG_ADDRESS
        # Datasheet says send 0
        packet.device_address = 0

        self.send_packet(packet)
        ## Data sheet doesn't mention an ACK, but that we'd receive a device count.
        packet = self.receive_packet()
        device_count = { # yes it's really just counting bits.
            0x1: 1,
            0x3: 2,
            0x7: 3
        }[packet.device_address]

        return device_count

    def get_correction_parameter(self):
        """Get the correction data for calibration. Each device has 3 calibration data.
        Note - this implementation only supports one connected device for now.
        """
        packet = Packet()
        packet.cmd_code = CmdCode.PACK_GET_COE
        packet.device_address = 0x1 # get no.1 device.

        self.send_packet(packet)
        response = self.receive_packet()
        coe_k0, coe_k1, coe_b0, coe_b1, points  = struct.unpack("<LLLLH", response.data_fields)
        k0, k1, b0, b1 = coe_k0 / 10000, coe_k1 / 10000, coe_b0 / 10000, coe_b1 / 10000
        return k0, k1, b0, b1, points

    def start_getting_distance(self):
        """Get the distance data from the device.
        The device will start to continuously send at this point."""
        packet = Packet()
        packet.cmd_code = CmdCode.PACK_GET_DISTANCE
        packet.device_address = 0x1 # get no 1 device

        self.send_packet(packet)
        
    def receive_distance(self, points=80):
        """Read a distance reading from the buffer"""
        packet = self.receive_packet()
        timestamp = struct.unpack("<L", packet.data_fields[:4])
        readings = ulab.frombuffer(packet.data_fields[4:], ulab.uint16)
        dist_theta = []
        dist_distance = []
        for n in readings:
            distance = (readings & 0xFF80) > 7
            confidence = readings & 0x007F
            if distance > 0:
                dist, theta = angle_transform(dist, )




