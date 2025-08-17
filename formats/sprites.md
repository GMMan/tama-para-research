# Tamagotchi Paradise Sprite Format

Because Tamagotchi Paradise runs on hardware that does not include a hardware
PPU, it uses a different, yet simpler format for storing sprites.

All data are to be read in little endian order.

## Sprite package

The sprite package consists simply of a table of offsets and the sprite data
joined together. Each offset is 32-bit. There is no number of sprites or size,
but you can deduce that by noting how many offsets there are before the first
sprite data, and each sprite data starts with the size of said data.

## Sprite concepts

Before introducing the data format, here are some terms used in this document:

- Sprite: image data that can be displayed on-screen. Typically square.
- Subimage: a presentation of sprites. Subimages may consist of one sprite,
  or a grid of sprites, depending on the size requirements of the subimage.
- Palette: a set of colors that pixel data will index into
- Palette set: a collection of palettes
- Image: a collection of subimages. All subimages in the image have the same
  dimensions.

## Sprite data

Each sprite data consists of a header, a palette, and collection of pixel data.
The header is as follows:

```c
struct sprite_img_def_t {
    uint32_t data_length;
    uint8_t flag_unknown01 : 1;
    uint8_t flag_unknown02 : 1;
    uint8_t flag_has_transparency : 1;
    uint8_t flag_unknown08 : 1;
    uint8_t flag_unknown10 : 1;
    uint8_t flag_compression_bytewise : 1;
    uint8_t flag_compression_wordwise : 1;
    uint8_t flag_encrypted : 1;
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
```

- `data_length`: the length of the entire sprite data
- `flag_unknown01`: unknown flag, always `1`
- `flag_unknown02`: unknown flag, always `1`
- `flag_has_transparency`: whether the sprite uses transparency
- `flag_unknown08`: unknown flag, always `0`
- `flag_unknown10`: unknown flag, always `0`
- `flag_compression_bytewise`: is using bytewise compression. Exclusive of
  `flag_compression_wordwise`.
- `flag_compression_wordwise`: is using wordwise compression. Exclusive of
  `flag_compression_bytewise`.
- `flag_encrypted`: pixel data is encrypted
- `bpp`: indicates number of bits per pixel in pixel data.
  - `0`: 1 bpp
  - `1`: 2 bpp
  - `2`: 4 bpp
  - `3`: 8 bpp
  - `16` or higher: direct color in pixel data
- `num_sprites`: number of sprites in image
- `sprite_width_px`: width of each sprite in pixels
- `sprite_height_px`: height of each sprite in pixels
- `offset_x`: horizontal offset to sprite's anchor from center of sprite
- `offset_y`: vertical offset to sprite's anchor from center of sprite
- `image_width`: width of each subimage in number of sprites
- `image_height`: height of each subimage in number of sprites
- `unknown`: unknown field, always `17`
- `num_palette_sets`: number of palette sets in image
- `transparent_color_index`: index of color to be interpreted as transparent
- `palette_offset`: offset to palettes relative to start of sprite data
- `pixel_data_offset`: offset to pixel data relative to start of sprite data
- `padding`: not used, always `0`

To get the number of subimages in the image, divide `num_sprites` by
`image_width` and `image_height`.

Palettes are stored in sets after the header, where each set consists of the
maximum number of colors indexable with the `bpp`. That is, 2 colors for 1 bpp,
4 colors for 2 bpp, 16 colors for 4 bpp, and 256 colors for 8 bpp. Each color
is in RGB565 format, with the R component on the most significant end of the
word.

Pixel data consists of an array of indexes into palettes, and may be optionally
compressed and encrypted. Each element of the array consists of the number of
bits specified by the `bpp` field, read from the least significant end of each
byte. For `bpp` >= `16`, palettes are not used and instead each pixel is read
as RGB565 directly from the pixel data.

For transparent pixels, when using palette, `transparent_color_index` contains
the index of the palette entry to be considered as transparent. When using
direct colors, `transparent_color_index` is the RGB565 color that is considered
to be transparent.

If pixel data is compressed, there is a list of offsets and lengths at
`pixel_data_offset`. Offsets and lengths are both 32-bit, and offsets are
relative to `pixel_data_offset`. Lengths are the lengths of the compressed data,
not the decompressed data. If the top bit of the offset is set, that means the
data is not compressed and should be read as is (of course, unset the top bit
first). Compressed data should be 32-bit aligned.

Data compression is accomplished by RLE encoding, and can be bytewise or wordwise.
Bytewise compression iterates through bytes, while wordwise compression iterates
through 32-bit words. For each iteration, read one control byte/word. If the top
bit of the byte/word is set, the next `n` bytes/words are literals. `n` is
the control byte `& 0x7f` for bytewise compression, and the control word
`& 0x0fffffff` for wordwise compression. If the top bit of the control byte/word
is not set, then the next byte/word is read and `n` bytes/words are repeated
with this value, where `n` is the control byte/word. If the control byte/word
is `0`, decompression is finished.

Encryption is just XOR with the byte `0x53` when reading the data. For compressed
pixel data, the encryption is applied on the compressed data, not decompressed.
Encryption is not available for `bpp` >= `16`.
