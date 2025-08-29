Tamagotchi Paradise Playdate Logic
==================================

This document outlines the logic for what goes on within playdates. Please see
the [communication description](/protocols/playdate.md) for how playdate data
is transmitted.

## Friendship level

Friendship level is determined by what is recorded through previous playdates
with a particular Paradise character, identified by its device UID and character
UID. If this is the first time a playdate is being done with a particular
character, then a base friendship level is determined. Note that the character
UID stays constant between evolutions, only changing when a new egg is started.

The base friendship level is determined through the characters' species rank.
The species rank is a rough indication of the amount of care required to
obtain the character, and ranks from 0 to 5. Baby to young stages have a rank of
0, and adults rank from 1-4 based on how many care mistakes they require, with
less care mistakes ranking higher. Secret characters are rank 5.

If either of the characters in the playdate are rank 5, then the base friendship
level is 4. If either are rank 0, then the base friendship level is 1.
Otherwise, the base friendship level is the difference between the ranks,
subtracted from 4. E.g. for a rank 2 and a rank 3 character, the base
friendship level is 3.

The highest friendship level, either calculated from 

## Play type

Play type is decided by several factors.

### Eat or be eaten

If either character's hunger level is not full, and one has the `is_consumer`
attribute and the other has the `is_consumee` attribute, the consumer will eat
the consumee. Typically, if one of the flags are set, the other is not set,

### Fighting

If both characters have hunger of 2 or less or happiness of 5 or less (either
of those conditions on each side, does not have to be the same low hunger or
happiness on both sides), then the characters will fight each other.

### Normal play

Depending on the happiness level, a different animation will be shown, from
both sides disliking each other, to dancing together. There are four separate
animations, each based on the friendship level.

## Breeding

After normal play, if both characters are adults, have a friendship level of 4,
and are not unbreedable (set via character attributes, in which only Bbmarutchi
currently has), then the option to breed is presented. Both parties must accept
for breeding to finish.

## Post-playdate friendship update

After the playdate, the friendship level is updated independently on each peer.
If friendship level is at 0 or normal play did not occur, the friendship level
does not increase. Otherwise, the increase depends on whether the love status
is set on each side. If neither side has the status, then friendship level
increases by 1. If one side has the status, the friendship level increases by
2. If both sides have the status, the friendship level increases by 3. The
increase is added to the recorded friendship level, but capped at a maximum of
4.

The device type of the peer is also registered at this stage for the purposes
of determining whether secret character evolution is available.
