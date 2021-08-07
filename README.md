# Support for the LD07 Solid State LIDAR Device

A UART Based LIDAR with no moving parts - at low cost. But could do with some python code.

In CircuitPython so it can reach many controller types.

The plan is:

* Support for the LD07 in CircuitPython
    * An LD07 object, which gets passed UART pin numbers (TX, RX) and a device address (Defaulting to datasheet default).
    * A low-level Packet object - that encodes/decodes and checksums LD07 packets.
    * Enums for data types - eg the CmdCodes.
    * The LD07 object will have low level send/receive packets.
    * LD07 will have high level - setup, change address, get reading methods

* Demo code for the Raspberry Pi - using Matplotlib to make a polar plot.
