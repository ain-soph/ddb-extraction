#!/usr/bin/env python3

import argparse
import io
import os
import wave
import zipfile

from wave import Wave_write

start_encode = 'SND '.encode()
wav_params = (1, 2, 44100, 0, 'NONE', 'NONE')


def parse_args(args=None):  # : list[str]
    # initialize parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--src-path', required=True,
                        help='source ddb file path')
    parser.add_argument('--dst-path',
                        help='destination extract path, default to be "./[name]/wav.zip (merge.wav)"')
    parser.add_argument('--merge', help='enable to generate a merged large wav file',
                        action='store_true')
    parser.add_argument('--silence-interval', help='silence interval seconds when "merge" is enabled, default to be 0',
                        type=float, default=0.0)

    # parse args
    args = parser.parse_args(args)
    src_path: str = os.path.normpath(args.src_path)
    dst_path: str = args.dst_path
    merge: bool = args.merge
    silence_interval: float = args.silence_interval
    silence_bytes = int(wav_params[1]*wav_params[2]*silence_interval)

    if dst_path is None:
        src_dir, src_filename = os.path.split(src_path)
        src_name, src_ext = os.path.splitext(src_filename)
        dst_filename = 'merge.wav' if merge else 'wav.zip'
        dst_path = os.path.join(src_dir, src_name, dst_filename)
    dst_path: str = os.path.normpath(dst_path)
    assert dst_path.endswith('.wav') or dst_path.endswith('.zip')

    # make dirs
    dir_path = os.path.dirname(dst_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)

    return src_path, dst_path, merge, silence_bytes


def main():
    src_path, dst_path, merge, silence_bytes = parse_args()
    with open(src_path, 'rb') as ddb_f:
        ddb_data = ddb_f.read()
    length = len(ddb_data)

    merge_f: Wave_write = None
    zip_f: zipfile.ZipFile = None
    if merge:
        merge_f = wave.open(dst_path, 'wb')
        merge_f.setparams(wav_params)
    else:
        zip_f = zipfile.ZipFile(dst_path, 'w', compression=zipfile.ZIP_STORED)

    counter = 0
    offset = 0
    while(True):
        if (start_idx := ddb_data.find(start_encode, offset)) == -1:
            break

        file_length = int.from_bytes(ddb_data[start_idx+4:start_idx+8],
                                     byteorder='little')
        """
        4 bytes of "SND "
        4 bytes of size
        4 bytes of frame rate
        2 bytes of 01 00 (channel?)
        4 bytes of unknown
        [data]
        """
        offset = start_idx+file_length
        if offset > length:
            break
        pcm_data = ddb_data[start_idx+18: offset]
        identifier = int.from_bytes(ddb_data[start_idx+14:start_idx+18],
                                    byteorder='little')

        counter += 1
        print(f'{counter:<10d} progress: {offset:0>8x} / {length:0>8x}')

        if merge:
            merge_f.writeframes(pcm_data)
            merge_f.writeframes(b'\x00'*silence_bytes)
        else:
            bytes_f = io.BytesIO()
            # TODO: the filename should be reconsidered.
            file_path = f'wav/{start_idx+0x12:016x}_{identifier:08x}.wav'
            with wave.open(bytes_f, 'wb') as wav_f:
                wav_f: Wave_write
                wav_f.setparams(wav_params)
                wav_f.writeframes(pcm_data)
            zip_f.writestr(file_path, bytes_f.getvalue())
            bytes_f.close()
            print('    wav saved at: ', file_path)
    if merge:
        merge_f.close()
        print('merged wav saved at: ', dst_path)
    else:
        zip_f.close()
        print('zip file saved at: ', dst_path)


if __name__ == '__main__':
    main()
