Tamagotchi Paradise Research Folder
===================================

This repo contains documentation on various aspects of Tamagotchi Paradise.

## Formats
- [Sprites](formats/sprites.md)
- [Archive](formats/archive.md)
- [Archive structure](formats/archive_structure.md)
- [CJK charset](formats/cjk_charset.txt): consists of 2350 Korean character blocks, Zhuyin symbols,
  parenthesized ideographs, and ~7000 most common Chinese characters (actually somewhat less)
  - For the Chinese characters, see "Unicodeの中の各国重要漢字（色付き、JIS、KS、GBのみ）" on
    https://cjk-code.com/
- [Ghost data and screenshots](formats/ghost_data.md)

## Gameplay
- [Items list](https://github.com/GMMan/tama-paradise-items-list/blob/main/index.md)
- [Playdates](gameplay/playdate.md)

## Protocols
- [TCP](protocols/tcp.md)
- [tamacom library](https://github.com/GMMan/tamacom): Python library for TCP
- [Secret code](protocols/secret_code.md) and [accompanying Python script](protocols/secret_code.py)
- [Playdates](protocols/playdate.md)

## Hardware
- [SNC73410 product page](https://www.sonix.com.tw/article-en-5180-42810): find microcontroller datasheet and SDK here
- [Test pad mapping](hardware/testpads.txt)
- [SNC7320/7330 firmware decrypter](https://github.com/GMMan/sonix-boot-decrypter)
- [Extracting Hidden Bootrom from Sonix SNC7330](https://github.com/GMMan/snc7330-hidden-rom)
- [Flash layout](hardware/flash_layout.md)

Follow me on [Twitter](https://x.com/GMMan_BZFlag) and [Bluesky](https://bsky.app/profile/sudo.caralynx.com)
for progress.
