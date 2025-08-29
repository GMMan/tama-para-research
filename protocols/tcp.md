# Tamagotchi Paradise Prongs Protocol

This document describes the protocol Tamagotchi Paradise uses to communicate with
other units. It is split into two parts, the transport layer and the packet
protocols.

## TCP Transport Layer

Tamagotchi Paradise uses UART at 460800/8-N-1 and a protocol called TCP (not
to be confused with the TCP in TCP/IP) to pass data between peers. The protocol
consists of commands and payloads.

### Commands

Commands are ASCII text and consist of one command word and zero or more parameters.
Each command is on a separate line, with CRLF used for line endings.

#### `PKT`

Initiates packet transfer. Recipient should `ACK` to begin transfer.

1 parameter: size of whole packet

#### `ACK`

Acknowledge successful reception of packet chunk.

#### `NAK`

Indicates reception of packet chunk is unsuccessful and requesting resend of chunk.

#### `ENQ`

Indicates out of sequence packet chunk received, and to reset packet chunk index
and start resending from there.

1 parameter: the index of the chunk to resend

#### `CAN`

Cancel transmission. No ACK back to peer.

#### `ECHO`

Ping to test the connection.

1 parameter:
- `REQ`: request an echo response
- `REP`: respond to an echo request

#### Custom commands

Custom commands are passed to the callback provided by the session initiator for
processing.

### Payload

Payloads are encrypted messages with headers for sending data between units.
The data to be sent in a packet is divided into 0x1000-byte chunks, and each
chunk has a chunk header prepended, and the chunk encrypted. The maximum payload
size is 0x101000 bytes.

#### Encryption

An encrypted chunk starts with a 32-bit random nonce, and each byte in the chunk
after this is encrypted by generating a keystream using the nonce, and XORing
the repeated keystream against the remaining data. Every time a byte in the
keystream is used, it is updated by doubling the value and adding one.
The encryption is symmetrical.

For keystream generation, SHA-256 hash the nonce (in its binary form) together
with the shared encryption secret.

#### Chunk header

The header is in this format:

```c
struct tcp_chunk_header_t {
    uint32_t session_id;
    char[3] magic;
    uint8_t type;
    uint8_t chunk_index;
    uint8_t chunk_index_comp;
    uint16_t crc;
};
```

- `session_id`: identifies the session that this chunk belongs to
- `magic`: the characters `TCP`
- `type`: the lower 4 bits indicate the packet type; bit 5 indicates whether
  this packet is for setting the session ID
- `chunk_index`: the current chunk's index within this packet
- `chunk_index_comp`: complement of `chunk_index` by subtracting it from 0xff
- `crc`: the CRC-16 checksum over the data following the chunk header; the
  parameters for the CRC are polynomial `0x18005`, init value `0`, no output xor,
  input and output reversed

### Operations

TCP supports three operations.

In the following operation illustrations, `< ` indicates a message sent from the
initiator's point of view, and `> ` indicates a message received by the initiator.
The actual communication does not include these markers.

#### Echo

To detect that the peer is ready to receive, an echo can be sent. Generally
echoes are sent at 2000-tick intervals. The peer has up to 500 ticks to respond,
and the operation is tried up to three times before failing due to timeout.

```
< ECHO REQ
> ECHO REP
```

#### Set session ID

Before transmitting a packet, the session ID should be sent. The initiator sends
the session ID as a packet, where the `type` field in the chunk header has the
set session ID flag set. While the initiator should only set the session ID once
in the session, the peer will accept changes in session ID. The packet length
for this operation is 2 bytes, and the contents are random.

#### Send packet

The main operation of TCP is to send packets of data. This happens by breaking
the data into chunks and transmitting payload chunks. The operation initiates by
the initiator sending a `PKT` command with the length of the packet. Once `ACK`ed,
the initiator will send a chunk, and wait for the peer to respond with `ACK`,
`NAK`, `ENQ`, or `CAN`. `ACK` triggers the next chunk to be sent, while `NAK`
requests the chunk that was sent to be repeated. `ENQ` signals to the initiator
to restart sending chunks at a specific index, while `CAN` indicates that the
operation has been cancelled. `CAN` can be issued by either peers.

The recipient should validate the chunk after
reception and decryption to ensure that it has the correct session ID, correct
magic value, packet type, chunk index, and data CRC. The recipient has 2000
ticks to respond to the initial `PKT` command and 5000 ticks to respond to a
chunk that was sent. The initiator has 2000 ticks to send another chunk after
the recipient has responded to the previous chunk.

Do not respond with any other command other than `ACK` when `PKT` is received,
otherwise unexpected behavior may be encountered.

Example operation with no issues:

```
< PKT 12345
> ACK
< <encrypted payload, chunk 0, 0x1010 bytes>
> ACK
< <encrypted payload, chunk 1, 0x1010 bytes>
> ACK
< <encrypted payload, chunk 2, 0x1010 bytes>
> ACK
< <encrypted payload, chunk 3, 0x49 bytes>
> ACK
```

Example operation with resend:

```
< PKT 1000
> ACK
< <encrypted payload, chunk 0, 0x3f8 bytes>
> NAK
< <encrypted payload, chunk 0, 0x3f8 bytes>
> ACK
```

Example operation with `ENQ`:

```
< PKT 12345
> ACK
< <encrypted payload, chunk 0, 0x1010 bytes>
> ACK
< <encrypted payload, chunk 1, 0x1010 bytes>
> ACK
< <encrypted payload, chunk 2, 0x1010 bytes>
> ENQ 1
< <encrypted payload, chunk 1, 0x1010 bytes>
> ACK
< <encrypted payload, chunk 2, 0x1010 bytes>
> ACK
< <encrypted payload, chunk 3, 0x49 bytes>
> ACK
```

It is unclear under what circumstances that an out of sequence chunk could occur.

Example operation with cancel:

```
< PKT 12345
> ACK
< <encrypted payload, chunk 0, 0x1010 bytes>
> ACK
< <encrypted payload, chunk 1, 0x1010 bytes>
> ACK
< <encrypted payload, chunk 2, 0x1010 bytes>
> CAN
```

## Packet protocols

Note certain actions may be preceded with setting session ID.

### Type `0x0`: Dev test

These packets are sent from a certain dev test menu, are variably sized
depending on the target, and contain random data.

### Type `0x1`: Playdate

Consists of an exchange of ghost data, playdate data, and a couple of custom
commands. See [playdate flow doucment](playdate.md) for details.

### Type `0x2`: Gifts

1. Initiator sends the 32-bit release version (currently `1`), and the peer
   replies with its version
2. Players select items to exchange
3. The initiator (could be the other device) sends a 16-bit item ID
4. The initiator sends an echo to the peer and waits for response; if a
   response is not received, the connection is considered to have failed
5. The peer responds with its selected item ID

### Type `0x3`: Download

Downloadable content from Lab Tama. The data is saved directly to flash. If the
data size is 0x4000 or less, it is an item. Otherwise, it is a patch, up to
0x10000 bytes in length.

### Type `0xf`: Factory test

These packets are sent in test mode, and also used as part of the sequence to
enter factory mode. The packet is 256 bytes in size, and consists of either
all `0xaa` or `0x55` bytes.
