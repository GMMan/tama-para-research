# Tamagotchi Paradise Sprite Format

Because Tamagotchi Paradise runs on hardware that does not include a hardware
PPU, it uses a different, yet simpler format for storing sprites.

All data are to be read in little endian order.

## Sprite package

The sprite package consists simply of a table of offsets and the sprite data
joined together. Each offset is 32-bit, relative to the start of the package,
and in ascending order. There is no explicit number of sprites or size. To find
the number of sprites, note the value of the first offset, and read offsets
until you are at the position indicated in the initial offset. The number of
offsets you read is the number of sprites.

## Sprite concepts

Before introducing the data format, here are some terms used in this document:

- Sprite: image data that can be displayed on-screen. Typically square.
- Subimage: a presentation of sprites. Subimages may consist of one sprite, or a
  grid of sprites, depending on the size requirements of the subimage.
- Palette: a set of colors that pixel data will index into
- Palette set: a collection of palettes
- Image: a collection of subimages. All subimages in the image have the same
  dimensions.

## Sprite data

Each sprite data consists of a 24-byte header, a palette, and collection of
pixel data. The header, in little endian, is as follows:

```c
#pragma pack(push, 1)
struct sprite_img_def_t {
    uint32_t data_length;
    uint8_t flags; // see sprite_img_flags_t
    uint8_t bpp;
    uint16_t num_sprites;
    uint8_t sprite_width_px;
    uint8_t sprite_height_px;
    int8_t offset_x;
    int8_t offset_y;
    uint8_t image_width;
    uint8_t image_height;
    uint8_t unknown;
    uint8_t num_palette_sets;
    uint16_t transparent_color_index;
    uint16_t palette_offset;
    uint16_t pixel_data_offset;
    uint16_t padding;
};
#pragma pack(pop)

enum sprite_img_flags_t {
    flag_unknown01 = 1 << 0,
    flag_unknown02 = 1 << 1,
    flag_has_transparency = 1 << 2,
    flag_unknown08 = 1 << 3,
    flag_unknown10 = 1 << 4,
    flag_compression_bytewise = 1 << 5,
    flag_compression_wordwise = 1 << 6,
    flag_encrypted = 1 << 7,
};
```

- `data_length`: the length of the entire sprite data, including header. This
  may sometimes be `0`, in which case the size will need to be manually
  determined by adding to `pixel_data_offset` the last offset and length `&
  0x7fffffff` for compressed pixel data or the amount of space the pixel data
  will take up for uncompressed pixel data.
- `flags`
  - `flag_unknown01`: unknown flag, always set to `1` and ignored on read
  - `flag_unknown02`: unknown flag, always set to `1` and ignored on read
  - `flag_has_transparency`: whether the sprite uses transparency
  - `flag_unknown08`: unknown flag, always set to `0` and ignored on read
  - `flag_unknown10`: unknown flag, always set to `0` and ignored on read
  - `flag_compression_bytewise`: is using bytewise compression
  - `flag_compression_wordwise`: is using wordwise compression
  - `flag_encrypted`: pixel data is encrypted
  - Note: `flag_compression_bytewise` and `flag_compression_wordwise` are
    mutually exclusive. Any file with both flags set are invalid.
- `bpp`: indicates number of bits per pixel in pixel data.
  - `0`: 1 bpp
  - `1`: 2 bpp
  - `2`: 4 bpp
  - `3`: 8 bpp
  - `16` or higher: direct color in pixel data, always 16 bpp
- `num_sprites`: number of sprites in image
- `sprite_width_px`: width of each sprite in pixels
- `sprite_height_px`: height of each sprite in pixels
- `offset_x`: horizontal offset to sprite's anchor from center of sprite; right
  is positive
- `offset_y`: vertical offset to sprite's anchor from center of sprite; up is
  positive
- `image_width`: width of each subimage in number of sprites
- `image_height`: height of each subimage in number of sprites
- `unknown`: unknown field, always set to `17` and ignored on read
- `num_palette_sets`: number of palette sets in image
- `transparent_color_index`: index of color in every palette set to be
  interpreted as transparent
- `palette_offset`: offset to palettes relative to start of sprite data
- `pixel_data_offset`: offset to pixel data relative to start of sprite data
- `padding`: not used, always set to `0` and ignored on read

To get the number of subimages in the image, divide `num_sprites` by
`image_width` and `image_height`.

Palettes are stored in sets after the header, where each set consists of the
maximum number of colors indexable with the `bpp`. That is, 2 colors for 1 bpp,
4 colors for 2 bpp, 16 colors for 4 bpp, and 256 colors for 8 bpp. Each color is
in RGB565 format, with the R component on the most significant end of the word.
Palette sets apply to all sprites for a given sprite file.

If encryption is enabled, it is applied to the pixel data only, starting after
the list of offsets and lengths if pixel data is compressed (see below).
Encryption is just XOR with the byte `0x53` over each byte of the data. If
compression is used, encryption is applied after compression. Encryption is also
applied if compression is used but the current sprite is not compressed.
Encryption is not available for `bpp` >= `16`.

Pixel data consists of an array of indexes into palettes, left to right and top
to bottom, and may be optionally compressed and encrypted. The elements are
packed into a bitstream read from the least significant end of each byte, with
each element being `bpp` bits long. When reading the element, shift each bit
into the least significant end of your holding variable. For `bpp` >= `16`,
palettes are not used and instead each pixel is read as 16-bit RGB565 directly
from the pixel data. Sprites are stored sequentially, and subimages are composed
of sprites in left to right, top to bottom order.

For transparent pixels, when using palette, `transparent_color_index` contains
the index of the palette entry to be considered as transparent. When using
direct colors, `transparent_color_index` is the RGB565 color that is considered
to be transparent.

If pixel data is compressed, there is a list of `num_sprites` offsets and
lengths at `pixel_data_offset`. Offsets and lengths are both 32-bit and in
bytes, and offsets are relative to `pixel_data_offset`. Lengths are the lengths
of the compressed data, not the decompressed data. If the top bit of the offset
is set, that means the data is not compressed and should be read as is (of
course, unset the top bit first). The start of compressed data should be 32-bit
aligned relative to the start of the header. If the pixel data is not
compressed, there is no list of offsets and lengths, and the pixel data is
stored directly and sequentially at `pixel_data_offset`, and there is no
alignment requirement. Compression is not available for `bpp` >= `16`.

Data compression is accomplished by RLE encoding, and can be bytewise or
wordwise. Bytewise compression iterates through bytes, while wordwise
compression iterates through 32-bit words. For each iteration, read one control
byte/word. If the top bit of the byte/word is set, the next `n` bytes/words are
literals. `n` is the control byte `& 0x7f` for bytewise compression, and the
control word `& 0x0fffffff` for wordwise compression. If the top bit of the
control byte/word is not set, then the next byte/word is read and `n`
bytes/words are repeated with this value, where `n` is the control byte/word.
Note for wordwise compression, bits 28-30 are ignored. If the top bit is set but
`n` is `0`, then this is a no-op. If the control byte/word is exactly `0`,
decompression is finished and any trailing compressed data ignored.
Decompression should also stop if there is no more compressed data available per
the length for the current sprite in the offsets and lengths list.
