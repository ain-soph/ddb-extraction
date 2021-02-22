# ddb-extraction

Extract the samples of a `ddb/ddi` Vocaloid file.

## Usage:

```
usage: extract_ddi.py [-h] --src-path SRC_PATH

optional arguments:
  -h, --help           show this help message and exit
  --src-path SRC_PATH  source ddi file path
```

```
usage: extract_wav.py [-h] --src-path SRC_PATH [--dst-path DST_PATH] [--merge] [--silence-interval SILENCE_INTERVAL]

optional arguments:
  -h, --help            show this help message and exit
  --src-path SRC_PATH   source ddb file path
  --dst-path DST_PATH   destination extract path, default to be "./[name]/wav.zip (merge.wav)"
  --merge               enable to generate a merged large wav file
  --silence-interval SILENCE_INTERVAL
                        silence interval seconds when "merge" is enabled, default to be 0
```


```
usage: extract_frm2.py [-h] --src-path SRC_PATH [--dst-path DST_PATH]

optional arguments:
  -h, --help           show this help message and exit
  --src-path SRC_PATH  source ddb file path
  --dst-path DST_PATH  destination extract path, default to be "./[name]/frm2.zip"
```