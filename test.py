#!/usr/bin/env python3

import yaml

data: dict = yaml.load(open('./ddi_data/Luotianyi_CHN_Meng/art.yml', 'r').read(), yaml.FullLoader)
snd = [artp['snd'] for art in data.values() if 'artu' in art.keys() for artu in art['artu'].values()
       for artp in artu['artp'].values()]
print(sorted(snd))
