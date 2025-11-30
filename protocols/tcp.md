# Tamagotchi Paradise Prongs Protocol

This document describes the protocol Tamagotchi Paradise uses to communicate
with other units. It is split into two parts, the transport layer and the packet
protocols.

## TCP Transport Layer

Tamagotchi Paradise uses UART at 460800/8-N-1/no flow control and a protocol
called TCP (not to be confused with the TCP in TCP/IP) to pass data between
peers. The protocol consists of commands and payloads.

### Commands

Commands are case-sensitive ASCII text and consist of one command word and up to
seven parameters. Parameters are split by whitespace (space, tab, CR, LF), and
leading and trailing whitespace is ignored. Each command is on a separate line,
with CRLF used for line endings. Command lines should be kept to 16 characters
or less excluding line ending, otherwise the leading characters will be dropped
and the received command may be invalid.

#### `PKT`

Initiates packet transfer. Recipient should `ACK` to begin transfer.

1 parameter: size of whole packet, excluding headers, in decimal numbers.
Behavior is undefined if the value exceeds 1048576.

#### `ACK`

Acknowledge successful reception of packet chunk.

#### `NAK`

Indicates reception of packet chunk is unsuccessful and requesting resend of
chunk.

#### `ENQ`

Indicates out of sequence packet chunk received, and to reset packet chunk index
and start resending from there. A chunk is out of sequence if the index in its
header does not match the chunk counter on the recipient side.

1 parameter: the index of the chunk to resend in decimal numbers

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

### Payload chunks

Payload chunks are encrypted messages for sending data between units, consisting
of a nonce, encrypted chunk header, and encrypted chunk data. The data to send
is broken up into 0x1000-byte chunks. If the last chunk is smaller than 0x1000
bytes, it is not padded. At most 0x100000 bytes of data can be sent in a packet,
excluding headers.

#### Encryption

An encrypted chunk starts with an unencrypted 32-bit random nonce, with the
remaining data forming a single encrypted stream. To encrypt/decrypt the data,
generate the keystream by taking the 32-byte SHA-256 hash of the nonce (in its
little-endian binary form) followed by the shared encryption secret. The bytes
in the keystream are applied by XORing the bytes in the data starting from the
first byte in each, looping to the start when the end of the keystream is
reached. After a byte in the keystream is used it is updated by doubling the
byte's value and adding one, modulo 256. The encryption is symmetrical.

The shared encryption secret is an implementation detail but must be the same
between two peers.

#### Chunk header

The header is in this format, with all members in little-endian:

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
- `type`: the lower 4 bits indicate the packet type; the next bit (bit 4)
  indicates whether this packet is for setting the session ID. The recipient
  should always accept a type with `0` in the lower 4 bits. Bits 5-7 are
  reserved and should be set to `0`, and must be ignored when reading.
- `chunk_index`: the current chunk's index within this packet, starting from `0`
  and incrementing with each successive chunk
- `chunk_index_comp`: complement of `chunk_index` by subtracting it from 0xff
- `crc`: the CRC-16 checksum over the unencrypted data following the chunk
  header; the parameters (Rocksoft Model) are as follows:
  - Width: 16
  - Poly: `8005`
  - Init: `0000`
  - RefIn: True
  - RefOut: True
  - XorOut: `0000`

### Operations

TCP supports three operations.

In the following operation illustrations, `< ` indicates a message sent from the
initiator's point of view, and `> ` indicates a message received by the
initiator. The actual communication does not include these markers.

#### Echo

To detect that the peer is ready to receive, an echo can be sent. Generally
echoes are sent at 2000ms intervals. The peer has up to 500ms to respond, and
the operation is tried up to three times before failing due to timeout.

While a send packet operation is ongoing, an `ECHO` command can only be sent
while the recipient is not expecting a binary packet chunk.

```
< ECHO REQ
> ECHO REP
```

#### Set session ID

Before transmitting a packet, the session ID should be sent. The initiator sends
the session ID with a single chunk using the send packet flow, where the `type`
field in the chunk header has the set session ID flag set, and the `session_id`
field containing the ID. The `type` field may contain the packet type when
setting session ID. The packet length for this operation is 2 bytes, and the
data sent is random and inconsequential because the ID is explicitly encoded in
the header. The session ID can only be set once per session, and takes effect
upon successful decoding.

#### Send packet

The main operation of TCP is to send packets of data. This happens by breaking
the data into chunks and transmitting payload chunks. The operation initiates by
the initiator sending a `PKT` command with the length of the packet. Once
`ACK`ed, the flow consists of the initiator sending a packet chunk, and the
recipient responding with one of `ACK`, `NAK`, `ENQ`, or `CAN` command. This
repeats until all chunks have been sent, or if the `CAN` command is issued.

After the initial `PKT` command has been `ACK`ed, the recipient expects to read
exactly one chunk's worth of data before responding with a command. If there is
0x1000 or more data bytes remaining to be transferred, the chunk size is 0x4
nonce bytes + 0xc header bytes + 0x1000 data bytes = 0x1010 bytes total. If
there is fewer than 0x1000 data bytes remaining, then 0x4 nonce bytes + 0xc
header bytes + remaining data bytes are expected to be read.

The recipient should validate the chunk after reception and decryption to ensure
that it has the correct session ID (if set), correct magic value, packet type,
chunk index, chunk index complement, and data CRC. If the chunk is valid, it
should response with `ACK` to the next chunk to be sent. If the packet cannot be
validated, it should send `NAK` to request the chunk that was sent to be
repeated. If the chunk index does not match the counter on the recipient that
increments with every valid chunk received, it should send `ENQ` with the
current counter value to restart transmission from the expected index. `CAN`
indicates that the operation has been cancelled. `CAN` can also be issued by the
initiator, although it may not be interpreted correctly if the recipient is
expecting a chunk.

The recipient has 2000ms to respond to the initial `PKT` command and 5000ms to
respond to a chunk that was sent. The initiator has 2000ms to begin sending
after the recipient has responded to the previous chunk. The timeout between
each byte received depends on the current state as described. The number of
attempts for initiating a packet transfer or sending a chunk is three. If the
attempts have been exceeded, a `CAN` command should be sent and the operation
cancelled.

Do not respond with any other command other than `ACK`, `CAN`, or `ECHO` when
`PKT` is received, otherwise unexpected behavior may be encountered. Custom
commands may be sent from the recipient during a send packet operation, but is
not encouraged. A new send packet operation cannot be initiated while one is
already ongoing.

The transfer is complete after the final chunk has been `ACK`ed, and a new
operation can begin.

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

It is unclear under what circumstances an out of sequence chunk could occur.

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

#### Custom commands

Custom commands are not operations per se, but are used as light-weight messages
when transmitting simple flags where TCP packets would incur a lot of overhead.
Custom commands should not be sent by the initiator when it is sending a packet
to the recipient as this will be mistakenly interpreted as packet data. Custom
commands do not otherwise affect protocol state.

Format for numeric arguments in custom commands are implementation-defined, but
recommended to be decimal numbers.

Unknown command handling is implementation-defined, but typically unknown
commands are ignored.

## Packet protocols

Note certain actions may be preceded with setting session ID.

### Type `0x0`: Dev test

These packets are sent from a certain dev test menu, are variably sized
depending on the target, and contain random data.

### Type `0x1`: Playdate

Consists of an exchange of ghost data, playdate data, and a couple of custom
commands. See [playdate flow document](playdate.md) for details.

### Type `0x2`: Gifts

All data aside from step 4 sent as packet transfers

1. Initiator sends the 32-bit release version (currently `1`), and the peer
   replies with its version
2. Players select items to exchange
3. The initiator (could be the other device) sends a 16-bit item ID
4. The initiator sends an echo to the peer and waits for response; if a response
   is not received, the connection is considered to have failed
5. The peer responds with its selected item ID

### Type `0x3`: Download

Downloadable content from Lab Tama. The data is saved directly to flash. If the
data size is 0x4000 or less, it is an item. Otherwise, it is a patch, up to
0x10000 bytes in length.

### Type `0xf`: Factory test

These packets are sent in test mode, and also used as part of the sequence to
enter factory mode. The packet is 256 bytes in size, and consists of either all
`0xaa` or `0x55` bytes.
