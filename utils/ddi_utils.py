#!/usr/bin/env python3

import io
import os
import yaml

env = {'unknown': None, 'ddi_bytes': None}


def bytes_to_str(data: bytes) -> str:
    return ' '.join([f'{piece:02x}' for piece in list(data)])


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

    env['ddi_bytes'] = ddi_bytes
    ddi_data = io.BytesIO(ddi_bytes)
    # PHDC
    phdc_data = read_phdc(ddi_data)
    with open(os.path.join(dst_path, 'phdc.yml'), mode='w', encoding='utf-8') as phdc_f:
        phdc_str = yaml.dump(phdc_data, default_flow_style=False,
                             sort_keys=False)
        phdc_f.write(phdc_str)

    # TDB
    tdb_offset = ddi_bytes.find(b'\xFF'*8+b'TDB ')
    ddi_data.seek(tdb_offset)
    tdb_data = read_tdb(ddi_data)
    with open(os.path.join(dst_path, 'tdb.yml'), mode='w', encoding='utf-8') as tdb_f:
        tdb_str = yaml.dump(tdb_data, default_flow_style=False,
                            sort_keys=False)
        tdb_f.write(tdb_str)

    # DBV
    dbv_offset = ddi_bytes.find(b'\x00'*8+b'DBV ')
    ddi_data.seek(dbv_offset)
    read_dbv(ddi_data)

    # STA
    sta_offset = ddi_bytes.find(b'\x00'*8+b'STA ')-0x14-8
    ddi_data.seek(sta_offset)
    sta_data = read_sta(ddi_data)
    with open(os.path.join(dst_path, 'sta.yml'), mode='w', encoding='utf-8') as sta_f:
        sta_str = yaml.dump(sta_data, default_flow_style=False,
                            sort_keys=False)
        sta_f.write(sta_str)

    # ART
    art_offset = ddi_bytes.find(b'\x00'*8+b'ART ')-0x14-8
    ddi_data.seek(art_offset)
    art_data = read_art(ddi_data)
    with open(os.path.join(dst_path, 'art.yml'), mode='w', encoding='utf-8') as art_f:
        art_str = yaml.dump(art_data, default_flow_style=False,
                            sort_keys=False)
        art_f.write(art_str)

    # VQM
    vqm_offset = ddi_bytes.find(b'\xFF'*8+b'VQM ')
    vqm_data = None
    if vqm_offset != -1:
        vqm_offset -= 0xC2
        ddi_data.seek(vqm_offset)
        vqm_data = read_vqm(ddi_data)
        with open(os.path.join(dst_path, 'vqm.yml'), mode='w', encoding='utf-8') as vqm_f:
            vqm_str = yaml.dump(vqm_data, default_flow_style=False,
                                sort_keys=False)
            vqm_f.write(vqm_str)

    # DDI convert
    ddi_data = {
        'sta': {},
        'art': {},
    }

    if vqm_data is not None:
        ddi_data = {
            'vqm': {},
            'sta': {},
            'art': {},
        }

    vqm_dict = {}
    for idx, vqmp in vqm_data.items():
        vqm_dict[idx] = {'snd': vqmp['snd'], 'epr': vqmp['epr']}
    ddi_data['vqm'] = {'vqm': vqm_dict}

    sta_dict = {}
    for stau in sta_data.values():
        stau_dict = {}
        for idx, stap in stau['stap'].items():
            stau_dict[idx] = {'snd': stap['snd'], 'epr': stap['epr']}
        sta_dict[stau['phoneme']] = stau_dict
    ddi_data['sta'] = {key: sta_dict[key] for key in sorted(sta_dict.keys())}

    art_dict = {}
    for art in art_data.values():
        if 'artu' in art.keys():
            for artu in art['artu'].values():
                key = art['phoneme']+' '+artu['phoneme']
                art_dict[key] = []
                for artp in artu['artp'].values():
                    art_dict[key].append({'snd': artp['snd'], 'epr': artp['epr']})
        if 'art' in art.keys():
            for sub_art in art['art'].values():
                if 'artu' in sub_art.keys():
                    for artu in sub_art['artu'].values():
                        key = art['phoneme']+' '+sub_art['phoneme']+' '+artu['phoneme']
                        art_dict[key] = []
                        for artp in artu['artp'].values():
                            art_dict[key].append({'snd': artp['snd'], 'epr': artp['epr']})
    ddi_data['art'] = {key: art_dict[key] for key in sorted(art_dict.keys())}

    with open(os.path.join(dst_path, 'ddi.yml'), mode='w', encoding='utf-8') as ddi_f:
        ddi_str = yaml.dump(ddi_data, default_flow_style=False,
                            sort_keys=False)
        ddi_f.write(ddi_str)


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
                value = bytes_to_str(value[start_idx:])
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
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    tmm_num = int.from_bytes(ddi_data.read(4), byteorder='little')
    str_list = ['pitch', 'dynamics', 'opening']
    for i in range(tmm_num):
        assert ddi_data.read(8) == b'\xFF'*8
        assert ddi_data.read(4).decode() == 'TMM '
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
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
    sta_data = {}
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
    assert int.from_bytes(read_arr(ddi_data), byteorder='little') == 1
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0

    assert ddi_data.read(4).decode() == 'STA '
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    stau_num = int.from_bytes(ddi_data.read(4), byteorder='little')
    for i in range(stau_num):
        stau_data = {'phoneme': '', 'stap': {}}
        assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
        assert ddi_data.read(4).decode() == 'STAu'
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        stau_idx = int.from_bytes(ddi_data.read(4), byteorder='little')
        assert ddi_data.read(8) == b'\xFF'*8
        stap_num = int.from_bytes(ddi_data.read(4), byteorder='little')
        for j in range(stap_num):
            stap_data = {'snd': '', 'snd_unknown': '', 'epr': []}
            assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
            assert ddi_data.read(4).decode() == 'STAp'
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
            stap_data['unknown1'] = bytes_to_str(ddi_data.read(0x12))
            assert ddi_data.read(8) == b'\x00\x00\x00\x00\x9A\x99\x19\x3F'
            unknown = bytes_to_str(ddi_data.read(4))
            if env['unknown'] is None:
                env['unknown'] = unknown
            else:
                assert env['unknown'] == unknown
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 2
            assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0x3D
            assert ddi_data.read(4).decode() == 'EMPT'
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert read_str(ddi_data) == 'SND'
            unknown_snd = int.from_bytes(ddi_data.read(4), byteorder='little')
            stap_data['snd_unknown'] = f'{unknown_snd:08x}'
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert ddi_data.read(4).decode() == 'EMPT'
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert read_str(ddi_data) == 'EpR'
            assert ddi_data.read(4) == b'\xFF'*4
            epr_num = int.from_bytes(ddi_data.read(4), byteorder='little')
            epr_list: list[str] = []
            for k in range(epr_num):
                epr_offset = int.from_bytes(ddi_data.read(8), byteorder='little')
                epr_list.append(f'{epr_offset:0>8x}')
            stap_data['epr'] = epr_list
            assert ddi_data.read(4) == b'\x44\xAC\x00\x00'
            assert ddi_data.read(2) == b'\x01\x00'
            snd_identifier = int.from_bytes(ddi_data.read(4), byteorder='little')
            # TODO: why this number?
            snd_offset = int.from_bytes(ddi_data.read(8), byteorder='little')
            stap_data['snd'] = f'{snd_offset-0x812:016x}_{snd_identifier:08x}'

            stap_data['unknown2'] = bytes_to_str(ddi_data.read(0xD))
            assert ddi_data.read(4) == b'\x00\x00\x00\x01'
            stap_idx = int(ddi_data.read(4).decode().strip('\x00'))
            assert stap_idx not in stau_data['stap'].keys()
            stau_data['stap'][stap_idx] = stap_data
        stau_data['stap'] = {k: stau_data['stap'][k]
                             for k in sorted(stau_data['stap'].keys())}
        stau_data['phoneme'] = read_str(ddi_data)
        sta_data[stau_idx] = stau_data
    sta_data = {k: sta_data[k] for k in sorted(sta_data.keys())}
    assert read_str(ddi_data) == 'normal'
    assert read_str(ddi_data) == 'stationary'
    return sta_data


def read_art(ddi_data: io.BytesIO) -> dict:
    total_art_data = {}
    assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
    assert int.from_bytes(read_arr(ddi_data), byteorder='little') != 0
    while(True):
        start = ddi_data.read(8)
        if not (start in [b'\x00'*8, b'\xFF'*8]):
            offset = ddi_data.tell()-8
            ddi_data.seek(offset)
            assert read_str(ddi_data) == 'articulation'
            break
        assert ddi_data.read(4).decode() == 'ART '
        art_idx, art_data = read_art_block(ddi_data)
        total_art_data[art_idx] = art_data
    total_art_data = {key: total_art_data[key] for key in sorted(total_art_data.keys())}
    return total_art_data


def read_art_block(ddi_data: io.BytesIO) -> tuple[int, dict]:
    art_data = {'phoneme': '', 'artu': {}, 'art': {}}
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    art_idx = int.from_bytes(ddi_data.read(4), byteorder='little')
    artu_num = int.from_bytes(ddi_data.read(4), byteorder='little')
    i = -1
    for i in range(artu_num):
        artu_data = {'phoneme': '', 'artp': {}}
        assert int.from_bytes(ddi_data.read(8), byteorder='little') == 0
        block_type = ddi_data.read(4).decode()
        if block_type == 'ART ':
            sub_art_idx, sub_art_data = read_art_block(ddi_data)
            art_data['art'][sub_art_idx] = sub_art_data
            continue
        else:
            assert block_type == 'ARTu'
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        artu_idx = int.from_bytes(ddi_data.read(4), byteorder='little')
        # TODO: why to be 1?
        assert int.from_bytes(ddi_data.read(8),
                              byteorder='little') in [0, 1]
        assert ddi_data.read(8) == b'\xFF'*8
        artp_num = int.from_bytes(ddi_data.read(4), byteorder='little')
        for j in range(artp_num):
            artp_data = {'snd': '', 'snd_unknown': '', 'epr': []}
            artp_data['unknown0'] = bytes_to_str(ddi_data.read(8))
            assert ddi_data.read(4).decode() == 'ARTp'
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
            artp_data['unknown1'] = bytes_to_str(ddi_data.read(0x12))
            assert ddi_data.read(8) == b'\x00\x00\x00\x00\x9A\x99\x19\x3F'
            unknown = bytes_to_str(ddi_data.read(4))
            if env['unknown'] is None:
                env['unknown'] = unknown
            else:
                assert env['unknown'] == unknown
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 2
            # TODO: This doesn't seem to be an index actually
            artp_idx = int.from_bytes(ddi_data.read(8), byteorder='little')
            assert ddi_data.read(4).decode() == 'EMPT'
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert read_str(ddi_data) == 'SND'
            unknown_snd = int.from_bytes(ddi_data.read(4), byteorder='little')
            artp_data['snd_unknown'] = f'{unknown_snd:08x}'
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert ddi_data.read(4).decode() == 'EMPT'
            assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
            assert read_str(ddi_data) == 'EpR'
            epr_num = int.from_bytes(ddi_data.read(4), byteorder='little')
            epr_list: list[str] = []
            for k in range(epr_num):
                epr_offset = int.from_bytes(ddi_data.read(8), byteorder='little')
                epr_list.append(f'{epr_offset:0>8x}')
            artp_data['epr'] = epr_list
            assert ddi_data.read(4) == b'\x44\xAC\x00\x00'
            assert ddi_data.read(2) == b'\x01\x00'
            snd_identifier = int.from_bytes(ddi_data.read(4), byteorder='little')
            # TODO: why this number?
            snd_offset = int.from_bytes(ddi_data.read(8), byteorder='little')
            artp_data['snd'] = f'{snd_offset-0x12:016x}_{snd_identifier:08x}'
            assert int.from_bytes(ddi_data.read(8), byteorder='little') == snd_offset+0x800

            ddi_bytes: bytes = env['ddi_bytes'][ddi_data.tell():]
            unknown2_length = ddi_bytes.find(b'default')-4
            artp_data['unknown2'] = bytes_to_str(ddi_data.read(unknown2_length))
            # print(f'{unknown2_length:x}')
            assert read_str(ddi_data) == 'default'

            assert artp_idx not in artu_data['artp'].keys()
            artu_data['artp'][artp_idx] = artp_data
        artu_data['artp'] = {k: artu_data['artp'][k]
                             for k in sorted(artu_data['artp'].keys())}
        artu_data['phoneme'] = read_str(ddi_data)
        art_data['artu'][artu_idx] = artu_data
    art_data['artu'] = {k: art_data['artu'][k]
                        for k in sorted(art_data['artu'].keys())}
    art_data['art'] = {k: art_data['art'][k]
                       for k in sorted(art_data['art'].keys())}
    art_data['phoneme'] = read_str(ddi_data)
    if len(art_data['art'].keys()) == 0:
        del art_data['art']
    if len(art_data['artu'].keys()) == 0:
        del art_data['artu']
    return art_idx, art_data


def read_vqm(ddi_data: io.BytesIO) -> dict:
    vqm_data = {}
    assert ddi_data.read(8) == b'\xFF'*8
    assert int.from_bytes(read_arr(ddi_data), byteorder='little') == 3
    assert ddi_data.read(8) == b'\xFF'*8
    assert int.from_bytes(read_arr(ddi_data), byteorder='little') == 0
    assert read_str(ddi_data) == 'notetonote'
    assert ddi_data.read(8) == b'\xFF'*8
    assert int.from_bytes(read_arr(ddi_data), byteorder='little') == 0
    assert read_str(ddi_data) == 'attack'
    assert ddi_data.read(8) == b'\xFF'*8
    assert int.from_bytes(read_arr(ddi_data), byteorder='little') == 0
    assert read_str(ddi_data) == 'release'
    assert read_str(ddi_data) == 'note'
    assert ddi_data.read(8) == b'\xFF'*8
    assert int.from_bytes(read_arr(ddi_data), byteorder='little') == 0
    assert read_str(ddi_data) == 'vibrato'
    assert ddi_data.read(8) == b'\xFF'*8

    assert ddi_data.read(4).decode() == 'VQM '
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
    assert ddi_data.read(8) == b'\xFF'*8

    assert ddi_data.read(4).decode() == 'VQMu'
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0

    vqmp_num = int.from_bytes(ddi_data.read(4), byteorder='little')
    assert int.from_bytes(ddi_data.read(4), byteorder='little') == vqmp_num
    for i in range(vqmp_num):
        vqmp_data = {'snd': '', 'epr': []}
        assert ddi_data.read(8) == b'\xFF'*8
        assert ddi_data.read(4).decode() == 'VQMp'
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 1
        vqmp_data['unknown'] = bytes_to_str(ddi_data.read(0x12))
        assert ddi_data.read(8) == b'\x00\x00\x00\x00\x9A\x99\x19\x3F'
        bytes_to_str(ddi_data.read(4))    # TODO: that may not be same as env['unknown']
        assert int.from_bytes(ddi_data.read(4), byteorder='little') == 0
        assert ddi_data.read(4) == b'\xFF'*4
        epr_num = int.from_bytes(ddi_data.read(4), byteorder='little')
        epr_list: list[str] = []
        for k in range(epr_num):
            epr_offset = int.from_bytes(ddi_data.read(8), byteorder='little')
            epr_list.append(f'{epr_offset:0>8x}')
        vqmp_data['epr'] = epr_list
        assert ddi_data.read(4) == b'\x44\xAC\x00\x00'
        assert ddi_data.read(2) == b'\x01\x00'
        snd_identifier = int.from_bytes(ddi_data.read(4), byteorder='little')
        snd_offset = int.from_bytes(ddi_data.read(8), byteorder='little')
        vqmp_data['snd'] = f'{snd_offset:016x}_{snd_identifier:08x}'
        assert ddi_data.read(0x10) == b'\xFF'*0x10
        vqmp_idx = int(read_str(ddi_data))
        vqm_data[vqmp_idx] = vqmp_data
    assert read_str(ddi_data) == 'GROWL'
    assert read_str(ddi_data) == 'vqm'
    assert read_str(ddi_data) == 'voice'
    return vqm_data
