#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 gr-teleskop author.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import os
import numpy as np
import scipy as sc
from gnuradio import gr
from guppi import guppi
from .tools import RingBuffer

class reader(gr.basic_block):
    """
    docstring for block reader
    """
    def __init__(self, filename, pol, lochan, hichan, dtype, repeat, aspect):
        self.pol = pol
        self.npol = 2 if pol == "XY" else 1
        self.lochan = lochan
        self.hichan = hichan
        self.dtype = dtype
        self.filename = filename
        self.repeat = repeat
        self.aspect = aspect
        self.first = True

        self._start_reader()

        if self.raw.nbeams != -1:
            self.NASPC = self.raw.nbeams

        if self.raw.nants != -1 and self.raw.nbeams == -1:
            self.NASPC = self.raw.nants
        else:
            self.NASPC = 1

        self.NFREQ = int(self.raw.obsnchan / self.NASPC)

        print("FILE METADATA", "=" * (80 - 14))
        print(f"Filename: {self.filename}")
        print(f"NANTS: {self.raw.nants}")
        print(f"NBEAMS: {self.raw.nbeams}")
        print(f"NBITS: {self.raw.nbits}")
        print(f"BLOCSIZE: {self.raw.blocsize}")
        print(f"OBSNCHAN: {self.raw.obsnchan}")
        print(f"NPOL: {self.raw.npol}")

        if self.aspect > self.NASPC - 1:
            raise AssertionError(f"Aspect index requested ({self.aspect}) larger than "
                                 f"the number of aspects indexes provided by the GUPPI file "
                                 f"({self.NASPC - 1}).")

        if self.npol > self.raw.npol:
            raise AssertionError(f"Number of polarizations requested ({self.npol}) larger than "
                                 f"the one provided by the GUPPI file ({self.raw.npol}).")

        if self.lochan == 0 and self.hichan == 0:
            self.lochan = 0
            self.hichan = self.NFREQ

        if self.lochan > self.hichan:
            raise AssertionError(f"Invalid channel selection.")

        if self.lochan < 0 or self.hichan > self.NFREQ:
            raise AssertionError(f"Channel bounds requested ({self.lochan}, {self.hichan}) "
                                 f"incompatible with the GUPPI file (0, {self.NFREQ}).")

        self._start_buffer()

        gr.basic_block.__init__(self,
            name="reader",
            in_sig=[],
            out_sig=[np.complex64] * self.npol)

    def _start_reader(self):
        if not os.path.isfile(self.filename):
            raise IOError(f"File doesn't exist: {self.filename}")

        self.raw = guppi.Guppi(self.filename)

    def _start_buffer(self):
        self.buffer_size = self.NFREQ * self.raw.nsamps_per_block

        self.buffer = []
        for _ in range(self.npol):
            self.buffer.append(RingBuffer(self.buffer_size * 2, dtype=self.dtype))

    def forecast(self, noutput_items, ninputs):
        ninput_items_required = [noutput_items] * ninputs
        return ninput_items_required

    def _parse_data(self, data):
        tmp = data[self.lochan:self.hichan, :]
        tmp = np.transpose(tmp)
        tmp = np.fft.ifftshift(tmp)
        tmp = sc.fft.ifft(tmp, workers=4)
        tmp = tmp.flatten()
        return tmp

    def general_work(self, _, output_items):
        if self.buffer[0].occupancy < self.buffer_size:
            hdr, data = self.raw.read_next_block()

            if self.first:
                s_freq = hdr['OBSFREQ'] - (hdr['OBSBW'] / 2)
                lo_freq = s_freq + (self.lochan * hdr['CHAN_BW'])
                hi_freq = s_freq + (self.hichan * hdr['CHAN_BW'])
                md_freq = (lo_freq + hi_freq) / 2 

                print("FILE HEADER", "=" * (80 - 12))
                for key, value in hdr.items():
                    print(f"{key}: {value}")
                print("OUTPUT INFO", "=" * (80 - 12))
                print(f"Output lower frequency: {lo_freq}")
                print(f"Output middle frequency: {md_freq}")
                print(f"Output higher frequency: {hi_freq}")
                print("=" * 80)

                self.first = False

            if data is None:
                if self.repeat:
                    self._start_reader()
                return 0

            if len(data.shape) == 4:
                data = data[self.aspect, ...]

            if self.pol == "X":
                self.buffer[0].put(self._parse_data(data[:, :, 0]))

            if self.pol == "Y":
                self.buffer[0].put(self._parse_data(data[:, :, 1]))

            if self.pol == "XY":
                self.buffer[0].put(self._parse_data(data[:, :, 0]))
                self.buffer[1].put(self._parse_data(data[:, :, 1]))

        if len(output_items[0]) > self.buffer[0].occupancy:
            return 0 

        for p in range(self.npol):
            self.buffer[p].get(output_items[p])

        return len(output_items[0])

