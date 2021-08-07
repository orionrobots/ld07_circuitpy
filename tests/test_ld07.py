from contextlib import contextmanager
from unittest import TestCase, mock
from ld_07 import ld_07


class TestPacket(TestCase):
    def test_packet_to_bytes_should_return_corret_bytes(self):
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


class TestLD07LowLevel(TestCase):
    def test_send_packet_should_turn_to_binary_and_send(self):
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

    def test_receive_simple_packet_should_set_packet_data(self):
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


class TestLD07HighLevel(TestCase):

    def test_config_address_should_send_correct_packet_with_return_for_1_device(self):
        # setup
        response_packet = ld_07.Packet()
        response_packet.cmd_cmd = ld_07.CmdCode.PACK_CONFIG_ADDRESS
        response_packet.device_address = 0x1

        def validate_sent_packet(sent_packet): 
            self.assertEqual(sent_packet.cmd_code, ld_07.CmdCode.PACK_CONFIG_ADDRESS)
            self.assertEqual(sent_packet.device_address, 0)

        lidar = ld_07.LD07(mock.sentinel.TX, mock.sentinel.RX)
        with mock.patch.object(lidar, "receive_packet", return_value=response_packet) as recv_mock, \
            mock.patch.object(lidar, "send_packet", side_effect=validate_sent_packet) as send_mock:
            
            # Test            
            result = lidar.config_address()
            # Assert
            send_mock.assert_called()
            recv_mock.assert_called_once_with()

        self.assertEqual(result, 1)

    def test_get_correction_parameter_should_return_coefficients(self):
        # setup
        response_packet = ld_07.Packet()
        response_packet.cmd_code = ld_07.CmdCode.PACK_GET_COE
        response_packet.device_address = 0x1
        # Use response modelled in the data sheet
        response_packet.data_fields = bytes([
            0x7b, 0x00, 0x00, 0x00,
            0x79, 0x00, 0x00, 0x00,
            0x81, 0x13, 0x00, 0x00, 
            0x84, 0x15, 0x00, 0x00,
            0x50, 0x00
        ])

        def validate_sent_packet(sent_packet): 
            self.assertEqual(sent_packet.cmd_code, ld_07.CmdCode.PACK_GET_COE)
            self.assertEqual(sent_packet.device_address, 0x1)

        lidar = ld_07.LD07(mock.sentinel.TX, mock.sentinel.RX)
        with mock.patch.object(lidar, "receive_packet", return_value=response_packet) as recv_mock, \
            mock.patch.object(lidar, "send_packet", side_effect=validate_sent_packet) as send_mock:

            # Test
            k0, k1, b0, b1, points = lidar.get_correction_parameter()
            # assert
            send_mock.assert_called()
            recv_mock.assert_called_once_with()
            
        self.assertEqual(k0, 0.0123)
        self.assertEqual(k1, 0.0121)
        self.assertEqual(b0, 0.4993)
        self.assertEqual(b1, 0.5508)
        self.assertEqual(points, 80)
