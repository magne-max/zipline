# -*- coding: utf-8 -*-
"""
```
# 1.
$ cp -r ~/.zipline/data/quandl-xjpx/2016-12-28T08\;14\;58.046694 \
        /tmp/quandl-xjpx/

# 2.
$ python transform_quandl_xjpx_archive.py
```
"""
import tarfile


with tarfile.open('/tmp/quandl-xjpx.tar', 'w') as f:
    f.add('/tmp/quandl-xjpx')
