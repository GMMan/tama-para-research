Tamagotchi Paradise Flash Layout
================================

Flash chip used is [KH25L12833FM2I-10G](https://www.macronix.com/en-us/products/NOR-Flash/Serial-NOR-Flash/Pages/spec.aspx?p=MX25L12833F&m=Serial%20NOR%20Flash&n=PM2517)

Firmware
- `0x0` - `0xfff`: firmware header
- `0x1000` - `0x10fff`: firmware in PRAM (encrypted)
- `0x11000` - `0x10ffff`: XIP firmware
- `0x110000` - `0x110fff`: DPD firmware
- `0x111000` - `0x8286c3`: assets
- `0x8286c4` - `0xd48fff`: unused
- `0xd49000` - `0xde9fff`: version info

User data
- `0xd4a000` - `0xd4dfff`: downloadable item staging
- `0xd4e000` - `0xdedfff`: stored downloadable items
- `0xdee000` - `0xe45fff`: ghost data
- `0xe46000` - `0xe65fff`: ghost data/patch reception
- `0xe66000` - `0xe85fff`: ghost data export
- `0xe86000` - `0xefdfff`: friends screenshots
- `0xefe000` - `0xefefff`: save data main
- `0xeff000` - `0xefffff`: save data backup
- `0xf00000` - `0xffffff`: reserved
