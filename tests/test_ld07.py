from unittest import TestCase, mock
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

class TestLD07(TestCase):
    def test_send_packet(self):
        # Setup
        packet = ld_07.Packet()
        packet.device_address = 0x1
        packet.cmd_code = ld_07.CmdCode.PACK_CONFIG_ADDRESS

        uart_mock = mock.Mock()
        uart_create_mock = mock.Mock(return_value=uart_mock)
        with mock.patch("ld_07.ld_07.busio.UART", uart_create_mock):
            lidar = ld_07.LD07(mock.sentinel.TX, mock.sentinel.RX)

            # Test
            lidar.send_packet(packet)

        # assert
        uart_create_mock.assert_called_once_with(mock.sentinel.TX, mock.sentinel.RX, baud=921600)
        uart_mock.write.assert_called_once_with(
            bytes([0xAA, 0xAA, 0xAA, 0xAA, 0x1, 0x16, 0x00, 0x00, 0x00, 0x00, 0x17])
        )

