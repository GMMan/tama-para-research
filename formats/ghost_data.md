Tamagotchi Paradise Ghost Data and Screenshots
==============================================

Tamagotchi Paradise uses ghost data to transfer and retain character data
for playdates and genes. Screenshots are used for the friend planets list in the
connection menu.

## Ghost package

The ghost package contains the ghost data, composite definitions, and sprites.
It starts with the ghost data, followed by 54 * 5 composite definitions,
followed by sprites.

There are two ghost package types. Type 0 (as indicated by the `type` field in
the ghost data) is a full package and includes all sprites. It is up to
`0x1b000` bytes in size. Type 1 only contains the eyes sprites, and can be up
to `0x4000` bytes in size.

### Ghost data

Ghost data has a fixed length of 0x600 bytes, however only 0x180 bytes are used.
It has the following layout:

```c
#pragma pack(push, 2)
struct ghost_data_t {
    uint32_t checksum;
    uint32_t checksum_complement;
    union {
        struct {
            uint16_t type:2;
        };
        uint32_t flags;
    };
    uint16_t chara_id;
    uint16_t eye_chara_id;
    uint8_t color;
    // note alignment padding
    str_char_t name[9][13];
    uint16_t stage;
    uint16_t species_rank;
    struct chara_flags_t chara_flags;
    uint32_t reserved1;
    uint32_t reserved2;
    uint32_t total_length;
    struct data_entry_t sprite_locations[2][3];
    palette_color_t body_palette[16];
    palette_color_t mouth_palette[16];
    uint8_t unused[1152];
};
#pragma pack(pop)
```

- `checksum`: the checksum calculated across the ghost package; will be
  explained later
- `checksum_complement`: the negative of `checksum`
- `type`: ghost package type
  - `0`: full package, including all character sprites
  - `1`: genes package, including only eye sprites
- `flags`: the field is 32-bit wide, so this is to keep more space than the
  default alignment will allocate
- `chara_id`: the character's definition ID
- `eye_chara_id`: the definition ID of the character that the eyes were
  inherited from
- `color`: `0`-`15` for predefined palette, `0xff` for original palette from
  character sprites
- `name`: up to 12 characters of character name, for each of the 9 languages,
  stored using the text rendering system's character encoding
- `stage`: character's growth stage, `1-5`
- `species_rank`: value that represents the care effort required to obtain the
  character
- `chara_flags`: character flags that can influence playdates (values will be
  moved to a different document when it's written)
  - `is_consumer = 1`: Consumer, may eat other tamas in playdate
  - `is_consumee = 2`: Consumee, may be eaten in playdate
  - `is_unbreedable = 4`: Cannot be bred with
- `reserved1`: unreferenced
- `reserved2`: unreferenced
- `total_length`: total length of ghost package
- `sprite_locations`: stores the offset and length of sprite images in the ghost
  package. Offsets that are `0` means the sprite is not included. The first
  dimension represents whether the sprites are for the Tama zoom level or the
  field zoom level. The second dimension represents the body, eyes, and mouth
  sprites.
- `body_palette`: body palette copied from sprites and color selection
- `mouth_palette` mouth palette copied from sprites and color selection
- `unused`: reserved space

```c
struct data_entry_t {
    uint32_t offset;
    uint32_t length;
};
```

- `offset`: offset of sprite image relative to start of package
- `length`: length of sprite image

### Composite definitions

These show where sprites are supposed to be placed when drawing the character.
Will be described in another document later. The definitions are stored
as instances instead of in its serialized form. Each definition is `0x16` bytes
long.

### Sprites

The sprites are in the [usual format](sprites.md), and are referenced by the
`sprite_locations` in the ghost data.

### Checksum

The checksum for the ghost package consists of the sum of 32-bit words, and is
calculated over all used data in the package. That includes:

- 0x180 bytes of the ghost data
- 0x1734 bytes of composite definitions
- All referenced sprite data

The order you calculate the sum does not matter because it's just adding numbers
together. The checksum is truncated to 32-bits before storing, and its
complement is the negative of the value. That is,
`checksum + checksum_complement = 0`.

## Screenshot

A screenshot stores a prerendered sprite image and a name. It is used for
displaying both the planet and tama in the friend planets list under the
connections menu. Each screenshot is allocated a total of 0x5000 bytes.
It has this format:

```c
struct screenshot_data_t {
    uint32_t sprite_checksum;
    uint32_t checksum_complement;
    uint32_t magic;
    uint32_t size;
    str_char_t name[9][13];
    uint8_t unused[262];
};
```

- `sprite_checksum`: the sprite data's checksum, calculated as a sum of each
  32-bit word in the sprite image data. This checksum does not include this
  header.
- `checksum_complement`: the inverse of the checksum, i.e.
  `sprite_checksum + checksum_complement = 0xffffffff`
- `magic`: the value `0x54485353` (`SSHT` in big endian order)
- `size`: the size of the screenshot, including the header and the sprite data
- `name`: up to 12 characters to display with the screenshot, for each of the 9
  languages, stored using the text rendering system's character encoding
- `unused`: reserved space

The sprite image comes immediately after the header. The screenshot is 8bpp,
bytewise-compressed, but not encrypted. There is only one subimage captured, and
it can have a transparent background.
