Instructions to build interpreters with AddressSanitizer
--------------------------------------------------------

You can actually build not only with AddressSanitizer, there are more options
to choose from: http://clang.llvm.org/docs/index.html. Also I prefer Clang.

Update clang to the latest available version:
```
$ sudo apt-get install clang-3.4
```
or
```
$ sudo apt-get install clang-3.5
```

Add symbolizer path:
```
$ export ASAN_SYMBOLIZER_PATH=/usr/bin/llvm-symbolizer-3.4
```

## Building PHP

Download PHP source code, extract.

Install build dev tools for PHP:
```
$ sudo apt-get build-dep php5
$ sudo apt-get -y install libfcgi-dev libfcgi0ldbl libjpeg62-dbg libmcrypt-dev libssl-dev

$ export CC="/usr/bin/clang -fsanitize=address -fsanitize-blacklist=blacklist.txt"
$ export CXX="/usr/bin/clang++ -fsanitize=address"
$ configure (whatever you want...) --disable-phar
$ make
```

Contents of blacklist.txt:
```
src:Zend/zend_hash.c
```

Make sure you provide correct paths, otherwise blacklist will not apply.

Blacklist file "blacklist.txt" and "--disable-phar" are required because PHP
will crash either during build time, or right upon start.

After build your binary will be located in: ./sapi/cli/php


## Building Perl

Download Perl source code, extract.

```
$ ./Configure -des -Doptimize="-g -O1" -DEBUGGING=both -Accflags=-fsanitize=address -Aldflags=-fsanitize=address -Alddlflags=-fsanitize=address -Dusethreads -Dusemultiplicity -Dusesitecustomize -Dusedevel -Uversiononly -Dcc=clang
$ make
$ make (second make required when makefile has been changed)
```

I recommend running build first without -fsanitize=address to avoid build
issues. After first dry-run you can build with AddressSanitizer. 

After build your binary will be located in: ./perl


## Building Python

https://docs.python.org/devguide/clang.html#building-python

After build your binary will be located in: ./Python

## Notes

I have been building on Ubuntu 12.0, clang 3.4., also clean Ubuntu 14.0, clang 3.4.
