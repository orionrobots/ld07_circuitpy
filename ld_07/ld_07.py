import struct
from enum import IntEnum

import busio


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
    packet_offset_addr: int = 0
    data_field_length: int = 0
    data_fields: bytes = bytes([])
    checksum: int = 0

    def inner_to_bytes(self) -> bytes:
        """Covert to bytes - without checksum or start"""
        output = struct.pack(
            # lIttle endian. 4 bytes for packet start, 1 byte device addr, 1 byte command code
            # Unsigned short Packet offset
            "<BBHH", self.device_address, self.cmd_code, self.packet_offset_addr,
                self.data_field_length
        )
        output += self.data_fields
        return output
    
    def to_bytes(self) -> bytes:
        inner = self.inner_to_bytes()
        cs = checksum_bytes(inner)
        output = self.packet_start + inner + bytes([cs])
        return output




class LD07:    
    def __init__(self, tx_pin, rx_pin, device_address:int = 0x1):
        self.uart = busio.UART(tx_pin, rx_pin, baud=921600)
        self.device_address = device_address    
        
    def receive_packet(self):
        header = self.uart.read(10)
        
        if header[:4] != Packet.packet_start:
            raise RuntimeError(f"Incorrect packet start: {header[:4]}")

        addr, cmd_code = header[4], header[5]
        if cmd_code != expect_cmd:
            raise RuntimeError(f"Expected {expect_cmd}. Got {cmd_code}")
        if addr != self.device_address:
            raise RuntimeError(f"Received packet for {addr}, accepting {self.device_address}")
        p = Packet(cmd_code)        
        p.offset, p.data_field_length = struct.unpack("<HH",  header[6:10])

        header_sum = sum(header)

        p.data_fields = ser.read(p.data_field_length)

        received_checksum = ser.read(1)
        calculated_checksum = header_sum + sum(p.data_fields)
        if received_checksum != calculated_checksum:
            raise RuntimeError("Checksum did not match")
        
        return p

    def send_packet(self, packet):
        data = packet.to_bytes()
        self.uart.write(data)

    def set_address(self, new_address):
        ## ODD - as there's no address data. Is this a Chip select type thing?
        ## It says "cascaded" - not clear on how his will work.
        packet = Packet()
        packet.cmd_code = CmdCode.PACK_CONFIG_ADDRESS
        # Datasheet says  send 0
        packet.device_address = 0

        self.send_packet(packet)
        ## Data sheet doesn't mention an ACK, but that we'd receive a device count.
        packet = self.receive_packet()

    def get_correction_parameter(self):
        pass
