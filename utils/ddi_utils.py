#!/usr/bin/env python3

import io
import os
import yaml

env = {'singer_id': None}


def read_str(data: io.BytesIO) -> str:
    str_size = int.from_bytes(data.read(4), byteorder='little')
    return data.read(str_size).decode()


def read_arr(data: io.BytesIO) -> bytes:
    assert data.read(4).decode() == 'ARR '
    assert int.from_bytes(data.read(4), byteorder='little') == 0
    assert int.from_bytes(data.read(8), byteorder='little') == 1
    return data.read(4)

# ----------------------------------------- #


def read_ddi(ddi_bytes: bytes, dst_path: str):
    # PHDC
    phdc_data = read_phdc(io.BytesIO(ddi_bytes))
    with open(os.path.join(dst_path, 'phdc.yml'), mode='w', encoding='utf-8') as phdc_f:
        phdc_str = yaml.dump(phdc_data, default_flow_style=False,
                             sort_keys=False)
        phdc_f.write(phdc_str)

    # TDB
    tdb_offset = ddi_bytes.find(b'\xFF'*8+b'TDB ')
    tdb_data = read_tdb(io.BytesIO(ddi_bytes[tdb_offset:]))
    with open(os.path.join(dst_path, 'tdb.yml'), mode='w', encoding='utf-8') as tdb_f:
        tdb_str = yaml.dump(tdb_data, default_flow_style=False,
                            sort_keys=False)
        tdb_f.write(tdb_str)

    # DBV
    dbv_offset = ddi_bytes.find(b'\x00'*8+b'DBV ')
    read_dbv(io.BytesIO(ddi_bytes[dbv_offset:]))

    # STA
    sta_offset = ddi_bytes.find(b'\x00'*8+b'STA ')-0x14-8
    sta_data = read_sta(io.BytesIO(ddi_bytes[sta_offset:]))
    with open(os.path.join(dst_path, 'sta.yml'), mode='w', encoding='utf-8') as sta_f:
        sta_str = yaml.dump(sta_data, default_flow_style=False,
                            sort_keys=False)
        sta_f.write(sta_str)


def read_phdc(ddi_data: io.BytesIO) -> dict:
    phdc_data = {}
    # DBSe
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
    assert ddi_data.read(4).decode() == 'DBSe'
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 1
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 3

    # PHDC
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
            if category_bytes[offset+7] == 0x40:
                value = category_bytes[offset:offset + 7]
                start_idx = 0
                for i in range(7):
                    if value[i] != 0:
                        start_idx = i
                        break
                # TODO: Need to check carefully. "b'XXX'" and we only take XXX
                value = str(value[start_idx:])[2:-1]
                category_data[key].append(value)
            else:
                assert int.from_bytes(category_bytes[offset:offset + 8],
                                      byteorder='little') == 0
                category_data[key].append('')
            offset += 8
    assert offset == len(category_bytes)
    phdc_data['category'] = category_data

    # hash string
    phdc_data['hash'] = ddi_data.read(0x20).decode()
    assert int.from_bytes(ddi_data.read(0xE0), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 2

    return phdc_data


def read_tdb(ddi_data: io.BytesIO) -> dict[str]:
    tdb_data: dict[str] = {}
    assert ddi_data.read(8) == b'\xFF'*8
    assert ddi_data.read(4).decode() == 'TDB '
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 1
    tmm_num = int.from_bytes(ddi_data.read(4), byteorder='little')
    str_list = ['pitch', 'dynamics', 'opening']
    for i in range(tmm_num):
        assert ddi_data.read(8) == b'\xFF'*8
        assert ddi_data.read(4).decode() == 'TMM '
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        assert int.from_bytes(ddi_data.read(8), byteorder='little') == 1
        idx = int.from_bytes(ddi_data.read(4), byteorder='little')
        # print(i, idx)
        str_num = int.from_bytes(ddi_data.read(4), byteorder='little')
        assert str_num == 3
        for j in range(str_num):
            assert ddi_data.read(8) == b'\xFF'*8
            assert int.from_bytes(read_arr(ddi_data), byteorder='little') == 0
            assert read_str(ddi_data) == str_list[j]
        phoneme = read_str(ddi_data)
        tdb_data[idx] = phoneme
    assert read_str(ddi_data) == 'timbre'
    return tdb_data


def read_dbv(ddi_data: io.BytesIO):
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
    assert ddi_data.read(4).decode() == 'DBV '
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 1
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 5


def read_sta(ddi_data: io.BytesIO) -> dict:
    sta_data = {'singer_id': None, 'stau': {}}
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
    assert int.from_bytes(read_arr(ddi_data), byteorder='little') == 1
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0

    assert ddi_data.read(4).decode() == 'STA '
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 1
    stau_num = int.from_bytes(ddi_data.read(4), byteorder='little')
    for i in range(stau_num):
        stau_data = {'phoneme': '', 'stap': {}}
        assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
        assert ddi_data.read(4).decode() == 'STAu'
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        assert int.from_bytes(ddi_data.read(8), byteorder='little') == 1
        stau_idx = int.from_bytes(ddi_data.read(4), byteorder='little')
        assert ddi_data.read(8) == b'\xFF'*8
        stap_num = int.from_bytes(ddi_data.read(4), byteorder='little')
        for j in range(stap_num):
            stap_data = {'snd': '', 'epr': []}
            assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
            assert ddi_data.read(4).decode() == 'STAp'
            assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
            stap_data['unknown1'] = str(ddi_data.read(0x12))[2:-1]
            assert ddi_data.read(8) == b'\x00\x00\x00\x00\x9A\x99\x19\x3F'
            singer_id = str(ddi_data.read(8))[2:-1]
            if env['singer_id'] is None:
                env['singer_id'] = singer_id
            else:
                assert env['singer_id'] == singer_id
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 2
            assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0x3D
            assert ddi_data.read(4).decode() == 'EMPT'
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert read_str(ddi_data) == 'SND'
            snd_data = int.from_bytes(ddi_data.read(8), byteorder='little')
            stap_data['snd'] = f'{snd_data:X}'
            assert ddi_data.read(4).decode() == 'EMPT'
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert read_str(ddi_data) == 'EpR'
            assert ddi_data.read(4) == b'\xFF'*4
            epr_num = int.from_bytes(ddi_data.read(4), byteorder='little')
            for k in range(epr_num):
                epr_offset = int.from_bytes(
                    ddi_data.read(8), byteorder='little')
                stap_data['epr'].append(f'{epr_offset:X}')
            assert ddi_data.read(4) == b'\x44\xAC\x00\x00'
            assert ddi_data.read(2) == b'\x01\x00'
            stap_data['unknown2'] = str(ddi_data.read(0x19))[2:-1]
            assert ddi_data.read(4) == b'\x00\x00\x00\x01'
            stap_idx = int(ddi_data.read(4).decode().strip('\x00'))
            assert stap_idx not in stau_data['stap'].keys()
            stau_data['stap'][stap_idx] = stap_data
        stau_data['stap'] = {k: stau_data['stap'][k]
                             for k in sorted(stau_data['stap'].keys())}
        stau_data['phoneme'] = read_str(ddi_data)
        sta_data['stau'][stau_idx] = stau_data
    sta_data['stau'] = {k: sta_data['stau'][k]
                        for k in sorted(sta_data['stau'].keys())}
    assert read_str(ddi_data) == 'normal'
    assert read_str(ddi_data) == 'stationary'
    sta_data['singer_id'] = env['singer_id']
    return sta_data
