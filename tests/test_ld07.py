from unittest import TestCase
from ld_07 import ld_07


class TestPacket(TestCase):
    def test_packet_to_bytes(self):
        # setup
        packet = ld_07.Packet()
        packet.device_address = 0x1
        packet.cmd_code = ld_07.CmdCode.PACK_CONFIG_ADDRESS
        # test
        output_bytes = packet.to_bytes()
        # assert
        self.assertEqual(
            output_bytes,
            bytes([0xAA, 0xAA, 0xAA, 0xAA, 0x1, 0x16, 0x00, 0x00, 0x00, 0x00, 0x17])
        )

