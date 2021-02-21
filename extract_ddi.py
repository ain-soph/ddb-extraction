#!/usr/bin/env python3

import argparse
import io
import os
import yaml


def read_str(data: io.BytesIO) -> str:
    str_size = int.from_bytes(data.read(4), byteorder='little')
    return data.read(str_size).decode()


def parse_args(args: list[str] = None):
    # initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--src-path', help='source ddi file path')

    # parse args
    args = parser.parse_args(args)
    src_path: str = os.path.normpath(args.src_path)
    assert os.path.isfile(src_path)

    src_dir, src_filename = os.path.split(src_path)
    src_name, src_ext = os.path.splitext(src_filename)
    dst_path = os.path.join(src_dir, src_name)
    if not os.path.isdir(dst_path):
        os.makedirs(dst_path)
    return src_path, dst_path


def read_phdc(ddi_data: io.BytesIO) -> dict:
    # DBSe
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
    assert ddi_data.read(4).decode() == 'DBSe'
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 1
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 3

    # PHDC
    phdc_data = {}
    phoneme_data: dict[int, list[str]] = {0: [], 1: []}
    assert ddi_data.read(4).decode() == 'PHDC'
    phdc_size = int.from_bytes(ddi_data.read(4), byteorder='little')
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 4
    phoneme_num = int.from_bytes(ddi_data.read(4), byteorder='little')
    for i in range(phoneme_num):
        bytes_str = ddi_data.read(0x1F)
        assert bytes_str[-1] in [0, 1]
        real_data = bytes_str[:-1].decode().strip('\x00')
        phoneme_data[bytes_str[-1]].append(real_data)
    phdc_data['phoneme'] = phoneme_data

    # PHG2
    phg2_data: dict[str, dict[int, str]] = {}
    assert ddi_data.read(4).decode() == 'PHG2'
    phg2_size = int.from_bytes(ddi_data.read(4), byteorder='little')
    phg2_category_num = int.from_bytes(ddi_data.read(4), byteorder='little')
    for i in range(phg2_category_num):
        phg2_key = read_str(ddi_data)
        phg2_data[phg2_key] = {}
        temp_num = int.from_bytes(ddi_data.read(4), byteorder='little')
        for j in range(temp_num):
            idx = int.from_bytes(ddi_data.read(4), byteorder='little')
            phg2_data[phg2_key][idx] = read_str(ddi_data)
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    phdc_data['phg2'] = phg2_data

    # category
    category_data: dict[str, list[str]] = {}
    category_num = int.from_bytes(ddi_data.read(4), byteorder='little')
    category_size = phdc_size-phg2_size-0x10-0x1F*phoneme_num-4
    category_bytes = ddi_data.read(category_size)
    offset = 0
    for i in range(category_num):
        key = category_bytes[offset:offset+0x20].decode().strip('\x00')
        assert int.from_bytes(category_bytes[offset+0x20:offset+0x24],
                              byteorder='little') == 4
        category_data[key] = []
        offset += 0x24
        while(offset < len(category_bytes) and category_bytes[offset] == 0):
            value = category_bytes[offset:offset + 7]
            start_idx = 0
            for i in range(7):
                if category_bytes[i] != 0:
                    start_idx = 0
                    break
            value = value[start_idx:]
            if category_bytes[offset+7] == 0x40:
                category_data[key].append(value)
            else:
                assert int.from_bytes(category_bytes[offset:offset + 8],
                                      byteorder='little') == 0
            offset += 8

    # hash string
    phdc_data['hash'] = ddi_data.read(0x20).decode()
    assert int.from_bytes(ddi_data.read(0xE0), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 2

    return phdc_data


def main():
    src_path, dst_path = parse_args()
    with open(src_path, 'rb') as ddi_f:
        ddi_bytes = ddi_f.read()
    ddi_data = io.BytesIO(ddi_bytes)

    phdc_data = read_phdc(ddi_data)
    dst_f = open(os.path.join(dst_path, 'phdc.yml'),
                 mode='w', encoding='utf-8')
    phdc_str = yaml.dump(phdc_data, default_flow_style=False, sort_keys=False)
    dst_f.write(phdc_str)


if __name__ == '__main__':
    main()
