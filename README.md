# ddb-extraction
![python>=3.10](https://img.shields.io/badge/python->=3.10.0-informational.svg)

Extract the samples of a `ddb/ddi` Vocaloid file.

## Usage:

```
usage: extract_ddi.py [-h] --src_path SRC_PATH

optional arguments:
  -h, --help           show this help message and exit
  --src_path SRC_PATH  source ddi file path
  --save_temp          save temp files
  --cat_only           only concat ddi.yml, assuming temp files exist.
```

```
usage: extract_wav.py [-h] --src_path SRC_PATH [--dst_path DST_PATH] [--merge] [--silence_interval SILENCE_INTERVAL]

optional arguments:
  -h, --help            show this help message and exit
  --src_path SRC_PATH   source ddb file path
  --dst_path DST_PATH   destination extract path, default to be "./[name]/wav.zip (merge.wav)"
  --merge               enable to generate a merged large wav file
  --silence_interval SILENCE_INTERVAL
                        silence interval seconds when "merge" is enabled, default to be 0
```


```
usage: extract_frm2.py [-h] --src_path SRC_PATH [--dst_path DST_PATH]

optional arguments:
  -h, --help           show this help message and exit
  --src_path SRC_PATH  source ddb file path
  --dst_path DST_PATH  destination extract path, default to be "./[name]/frm2.zip"
```

```
usage: rename_wav.py [-h] --work_dir WORK_DIR

optional arguments:
  -h, --help           show this help message and exit
  --work_dir WORK_DIR  working directory containing "ddi.yml" and "wav.zip".
```

# ddi.yml
`ddi.yml` file strucutre:
```
{
  'vqm': {
          'vqm': [
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
          ],
          }

  'sta': {
          'phoneme': [
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
          ],
          'phoneme': [
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
          ],
          }

  'art': {
          'phoneme[space]phoneme': [
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
          ],
          'phoneme[space]phoneme': [
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
          ],
          'phoneme[space]phoneme[space]phoneme': [
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
              {'snd': XXX, 'epr': [XXX,XXX,...]},
          ],
          }
}
```