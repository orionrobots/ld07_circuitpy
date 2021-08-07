from contextlib import contextmanager
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

@contextmanager
def uart_patched_ld07(uart_create_mock):
    with mock.patch("ld_07.ld_07.busio.UART", uart_create_mock):
        yield ld_07.LD07(mock.sentinel.TX, mock.sentinel.RX)


class TestLD07(TestCase):
    def test_send_packet(self):
        # Setup
        packet = ld_07.Packet()
        packet.device_address = 0x1
        packet.cmd_code = ld_07.CmdCode.PACK_CONFIG_ADDRESS

        uart_mock = mock.Mock()
        uart_create_mock = mock.Mock(return_value=uart_mock)
        with uart_patched_ld07(uart_create_mock) as lidar:
            # Test
            lidar.send_packet(packet)

        # assert
        uart_create_mock.assert_called_once_with(mock.sentinel.TX, mock.sentinel.RX, baud=921600)
        uart_mock.write.assert_called_once_with(
            bytes([0xAA, 0xAA, 0xAA, 0xAA, 0x1, 0x16, 0x00, 0x00, 0x00, 0x00, 0x17])
        )

    def test_receive_simple_packet(self):
        # Setup
        packet_header = bytes([
            0xAA, 0xAA, 0xAA, 0xAA, 0x1, 0x16, 0x00, 0x00, 0x00, 0x00
        ])
        packet_checksum = bytes([0x17])


        uart_mock = mock.Mock()
        uart_mock.read.side_effect = [
            packet_header,
            packet_checksum
        ]
        uart_create_mock = mock.Mock(return_value=uart_mock)
        with uart_patched_ld07(uart_create_mock) as lidar:
            # Test
            packet = lidar.receive_packet()

        # Assert
        self.assertEqual(packet.cmd_code, ld_07.CmdCode.PACK_CONFIG_ADDRESS)
        self.assertEqual(packet.device_address, 0x1)
        self.assertEqual(packet.offset_address, 0x00)

    def test_it_should_raise_error_if_start_incorrect(self):
        # Setup
        packet_header = bytes([
            0xFF, 0xFF, 0xFF, 0xAA, 0x1, 0x16, 0x00, 0x00, 0x00, 0x00
        ])
        packet_checksum = bytes([0x17])


        uart_mock = mock.Mock()
        uart_mock.read.side_effect = [
            packet_header,
            packet_checksum
        ]
        uart_create_mock = mock.Mock(return_value=uart_mock)
        with uart_patched_ld07(uart_create_mock) as lidar:
            # Test
            with self.assertRaises(RuntimeError):
                packet = lidar.receive_packet()

    def test_it_should_raise_error_if_checksum_mismatches(self):
        # Setup
        packet_header = bytes([
            0xAA, 0xAA, 0xAA, 0xAA, 0x1, 0x16, 0x00, 0x00, 0x00, 0x00
        ])
        packet_checksum = bytes([0xFF])


        uart_mock = mock.Mock()
        uart_mock.read.side_effect = [
            packet_header,
            packet_checksum
        ]
        uart_create_mock = mock.Mock(return_value=uart_mock)
        with uart_patched_ld07(uart_create_mock) as lidar:
            # Test
            with self.assertRaises(RuntimeError):
                packet = lidar.receive_packet()
