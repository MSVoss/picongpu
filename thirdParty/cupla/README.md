**cupla** - C++ User interface for the Platform Independent Library alpaka
==========================================================================

[![Code Status master](https://gitlab.com/hzdr/crp/cupla/badges/master/pipeline.svg?key_text=master)](https://gitlab.com/hzdr/crp/cupla/pipelines/master/latest)
[![Code Status dev](https://gitlab.com/hzdr/crp/cupla/badges/dev/pipeline.svg?key_text=dev)](https://gitlab.com/hzdr/crp/cupla/pipelines/dev/latest)

![cupla Release](doc/logo/cupla_logo_320x210.png)

**cupla** [[qχɑpˈlɑʔ]](https://en.wiktionary.org/wiki/Qapla%27) is a simple user
interface for the platform independent parallel kernel
acceleration library
[**alpaka**](https://github.com/alpaka-group/alpaka).
It follows a similar concept as the
[NVIDIA® CUDA® API](https://developer.nvidia.com/cuda-zone) by
providing a software layer to manage accelerator devices.
**alpaka** is used as backend for **cupla**.

Please keep in mind that a first, ["find & replace"](doc/PortingGuide.md) port
from **CUDA to cupla(x86)** will result in rather bad performance. In order to
reach decent performance on x86 systems you just need to add the **alpaka**
[element level](doc/TuningGuide.md) to your kernels.

(*Read as:* add some *tiling* to your CUDA kernels by letting the same thread
compute a fixed number of elements (N=4..16) instead of just computing one
*element* per thread. Also, make the number of elements in your tiling a
*compile-time constant* and your CUDA code (N=1) will just stay with the
very same performance while adding single-source performance portability for,
e.g., x86 targets).


Software License
----------------

**cupla** is licensed under **LGPLv3** or later.

For more information see [LICENSE.md](LICENSE.md).


Dependencies
------------

- **cmake 3.15.0**
- **[alpaka 0.6.X](https://github.com/alpaka-group/alpaka/)**
  - alpaka is loaded as `git subtree` within **cupla**, see [INSTALL.md](INSTALL.md)

Usage
-----

- See our notes in [INSTALL.md](INSTALL.md).
- Checkout the [guide](doc/PortingGuide.md) how to port your project.
- Checkout the [tuning guide](doc/TuningGuide.md) for a step further to performance
  portable code.

[cupla can be used as a header-only library and without the CMake build system](doc/ConfigurationHeader.md)

Authors
-------

### Maintainers* and Core Developers

- [Dr. Sergei Bastrakov](https://github.com/sbastrakov)*
- [Dr. Andrea Bocci](https://github.com/fwyzard)
- [Simeon Ehrig](https://github.com/SimeonEhrig)
- [Matthias Werner](https://github.com/tdd11235813)*
- [Rene Widera](https://github.com/psychocoderHPC)*

### Former Members, Contributions and Thanks

- [Dr. Michael Bussmann](https://www.hzdr.de/db/!ContMan.Visi.Card?pUser=4167&pNid=0)
- [Dr. Axel Huebl](https://github.com/ax3l)
- [Maximilian Knespel](https://github.com/mxmlnkn)
- [Vincent Ridder](https://github.com/vincentridder)


Trademarks Disclaimer
---------------------

All product names and trademarks are the property of their respective owners.
CUDA® is a trademark of the NVIDIA Corporation.
