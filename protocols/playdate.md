Tamagotchi Paradise Playdate Flow
=================================

This document describes how playdates work from a communication standpoint on
Tamagotchi Paradise.

## Overview

A playdate exchange consists of several phases.

1. Initial data exchange. Both peers send their ghost data, planet screenshot,
   and playdate data.
2. Calculate friendship level and update. Initiator received peer's friendship
   level from the playdate data, recalculates new friendship level, and sends
   the updated value back.
3. Send playdate result after the animation has finished on the initiator. This
   can also include a prompt to breed.
4. Breeding. The peers sync whether each side wants to accept breeding.

## Phase 1

In phase 1, the initiator sends the ghost package, planet screenshot, and
playdate data. All the data is sent as a single packet with all the pieces
joined together, for a total of `0x20014` bytes. For more information about
ghost data and screenshots, see [here](/formats/ghost_data.md). The ghost
package sent is type 0.

This is the format of the playdate data:

```c
#pragma pack(push, 2)
struct playdate_data_t {
    uint16_t force_send_away;
    uint16_t rom_type;
    struct friend_t friend_data;
    uint8_t hunger;
    uint8_t happiness;
    uint16_t is_in_love:1;
};
#pragma pack(pop)
```

- `force_send_away`: forces playdate to happen on the peer that sent this data.
  It is not set on normal Paradise units, only from the Lab Tama. Main reason
  for using this is because the Lab Tama does not send every frame of a
  character's sprite, so in case the player's device becomes the initiator, it
  would result in weird looking frames with the default animations.
- `rom_type`: the peer's device type:
  - `1`: Land
  - `2`: Water
  - `3`: Sky
- `friend_data`: a copy of the peer's friend record. See below
- `hunger`: the peer's hunger level, `0-6`
- `happiness`: the peer's happiness level, `0-20`
- `is_in_love`: does the peer have love status, gained by consuming the
  Love-Love Ice Cream

```c
struct friend_t {
    uint32_t device_uid;
    uint32_t chara_uid;
    uint16_t friendship;
    uint16_t result;
};
```

- `device_uid`: the device UID created when the name of the planet was first set
- `chara_uid`: the generated UID for the current character
- `friendship`: the friendship level that was recorded for the peer this data
  is being sent to. Not valid for the initiator when first sending to the peer,
  and will be updated afterwards.
- `result`: last playdate result, values to be covered later

After the phase 1 data is sent by the initiator to the peer, the recipient
processes the data to fetch its record of the previous playdate (if it has any),
and updates its own copy of the playdate data with the friendship level with
the initiator. The phase 1 data from the recipient side is sent over to the
initiator.

## Phase 2

After the initiator receives the recipient's phase 1 data, it calculates the
friendship level and sends it over to the recipient. This data is a 16-bit
value and represented in the same way as found in `struct friend_t`. Both sides
will use the same friendship level.

## Phase 3

The initiator selects the play type, and plays out the animation. The initiator
sends the result when the animation finishes. The recipient waits for the
initiator to respond with the play result before completing the playdate. 

The playdate result data is in this format:

```c
#pragma pack(push, 2)
struct playdate_result_t {
    uint16_t result;
    uint16_t can_breed:1;
};
#pragma pack(pop)
```

- `result`: the play result
  - `0`: played
  - `1`: fought
  - `2`: ate
  - `3`: eaten
- `can_breed`: whether breeding is possible

## Phase 4

If breeding is available, then both peers prompt the players whether to breed.
The recipient sends the custom command `BREED` to indicate the player's choice.

- `BREED 0`: breeding rejected
- `BREED 1`: breeding accepted

Note that only the recipient sends the `BREED` command. The initiator will
capture the player's response locally.

After the choices have been made, each side waits for sync by sending and
receiving the `SYNC 1` custom command. The flow will continue only after both
sides have synced.

The initiator then sends the playdate result, with the `result` field updated
to `4` if breeding proceeds. If the value is not `4`, breeding does not proceed.

If breeding proceeds, then the initiator plays the associated animation,
and at the end of the animation, sends the `SYNC 2` custom command. Both sides
need to send the `SYNC 2` command before the playdate session is completed. Note
that if breeding did not proceed, then the sync is not required.
