Tamagotchi Paradise Archive Format
==================================

The archive format is used to store main game data and also used to package
downloadable items. The variant as used in Tamagotchi Paradise is similar to
previous archive formats used with this engine, except the header has changed. 

All values are in little endian.

Header
------

The header consists of four words:

```c
struct arc2_header_t {
    uint32_t magic;
    uint32_t checksum;
    uint32_t length;
    uint32_t num_files;
};
```

- `magic`: the value `0x32435241`, or `ARC2` in ASCII
- `checksum`: literal sum of each byte following this field
- `length`: length of package, less size of this header
- `num_file`: number of files in package

File entries
------------

Following the header are file entries. Each entry has this format:

```c
struct arc2_entry_t {
    uint32_t flags;
    uint32_t offset;
    uint32_t compressed_length;
    uint32_t uncompressed_length;
};
```

- `flags`: usually used to indicate the compression method used, but compression
  is not supported as implemented in Tamagotchi Paradise, so it is always `0`
- `offset`: the data's offset, relative to the start of the header
- `compressed_length`: typically the compressed length of the data, but since
  compression is not supported, it's just the aligned length of the data
- `uncompressed_length`: actual length of the data

Data
----

Data follows the file entries, and can be addressed as per the offset in the
entries. Data is 32-bit aligned.

Note that an archive can contain other archives, to form pseudo-directories.
