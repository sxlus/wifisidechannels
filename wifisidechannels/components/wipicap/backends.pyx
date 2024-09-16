# Author: S. Kato (Graduate School of Information Technology and Science, Osaka University)
# Version: 2.0
# License: MIT License

# cython: linetrace=True


import wifisidechannels.models.models as models

import cython
from datetime import datetime
from loguru import logger
import re

import numpy as np
import pyshark
#from tqdm import tqdm

cimport numpy as cnp
from libc.stdint cimport uint8_t

ctypedef cnp.float64_t DOUBLE
ctypedef cnp.int64_t INT64

cdef double PI = np.pi


hex_to_bin = str.maketrans(
    {
        "0": "0000",
        "1": "0001",
        "2": "0010",
        "3": "0011",
        "4": "0100",
        "5": "0101",
        "6": "0110",
        "7": "0111",
        "8": "1000",
        "9": "1001",
        "a": "1010",
        "b": "1011",
        "c": "1100",
        "d": "1101",
        "e": "1110",
        "f": "1111",
    }
)


def get_v_matrix(
    packets: list[models.Packet],
    verbose=False):
    """
        needs uniform packets with respect to cbr
        make sure Nc, Nr, Bw, and type are the same for all
        else error because of dimensionality
    """

    # sequentially process packets
    if verbose:
        logger.info("parsing packet data...")

    # output
    ts = []
    vs = []
    #print("\n\n\nENTER\n\n\n")
    for i, packet in enumerate(packets):

        # get values
        mimo_control: dict = packet.DATA.get(models.ExtractorField.VHT_MIMO_CONTROL.value, {})
        #print(mimo_control)
        if not mimo_control:
            continue
        timestamp = float(packet.DATA.get(models.TsharkField.FRAME_TIME.value))
        nc: int = mimo_control.get("Nc", 0)
        nr: int = mimo_control.get("Nr", 0)
        #print(nc, nr)
        #chanwidth: int = mimo_control.get("channel_width", 0)
        #if chanwidth != bw:
        #    continue
        num_snr = nc
        (phi_size, psi_size) = mimo_control.get("codebook", {}).get("psi"), mimo_control.get("codebook", {}).get("phi")
        num_subc = mimo_control.get("Ns", 0)
        cbr_hex = packet.DATA.get(models.TsharkField.VHT_CBR.value, "")
        if not cbr_hex:
            continue

        # calc binary splitting rule

        angle_bits_order = []
        angle_type = []
        angle_index = []
        phi_indices = [0, 0]
        psi_indices = [1, 0]

        angle_bits_order_len = min([nc, nr - 1]) * (2 * (nr - 1) - min(nc, nr - 1) + 1)
        cnt = nr - 1
        while len(angle_bits_order) < angle_bits_order_len:
            for i in range(cnt):
                angle_bits_order.append(phi_size)
                angle_type.append("phi")
                angle_index.append([phi_indices[0] + i, phi_indices[1]])
            phi_indices[0] += 1
            phi_indices[1] += 1
            for i in range(cnt):
                angle_bits_order.append(psi_size)
                angle_type.append("psi")
                angle_index.append([psi_indices[0] + i, psi_indices[1]])
            psi_indices[0] += 1
            psi_indices[1] += 1
            cnt -= 1
        #print(phi_indices, psi_indices)
        #print(num_snr)
        split_rule = np.zeros(angle_bits_order_len + 1)
        split_rule[1:] = np.cumsum(angle_bits_order)
        #print(np.cumsum(angle_bits_order))
        split_rule = split_rule.astype(np.int32)
        angle_seq_len = split_rule[-1]
        #print(f"sub_c_len: ", angle_seq_len)
        cbr, snr = binary_to_quantized_angle(
            cbr_hex, num_snr, num_subc, angle_seq_len, split_rule
        )
        #print("cbr: ", cbr, len(cbr))
        #print("snr: ", snr)
        # V matrix recovery
        v = np.zeros((num_subc, nr, nc), dtype=complex)
        subc_len = len(angle_type)
        for subc in range(num_subc):
            #print(f"SUB: {subc}")
            angle_slice = cbr[subc * subc_len : (subc + 1) * subc_len]
            #print("\t", angle_slice)
            angle_slice = [quantized_angle_formulas(t, a, phi_size, psi_size) for t, a in zip(angle_type, angle_slice)]
            #print("\t", angle_slice)
            
            mat_e = inverse_givens_rotation(
                nr, nc, angle_slice, angle_type, angle_index
            )
            v[subc, ...] = mat_e
            #print(mat_e)
            # check if v is unitary
            assert np.all((np.sum(np.abs(mat_e)**2, axis=0)-1)<1e-5), f"v is not unitary {np.sum(np.abs(mat_e)**2, axis=0)}"
        packet.DATA[models.ExtractorField.VHT_STEERING_MATRIX.value] = v[np.newaxis, ...]
        vs.append(v[np.newaxis, ...])
        ts.append(timestamp)
    #print(len(vs))
    if vs:
        vs = np.concatenate([v for v in vs], axis=0)
        ts = np.array(ts)

    if verbose:
        logger.info(f'{len(ts)} packets are parsed.')
    return vs, ts

cdef binary_to_quantized_angle(
    str binary,
    int num_snr,
    int num_subc,
    int angle_seq_len,
    cnp.ndarray[int] split_rule,
):
    cdef:
        str cbr_hex_join, cbr_bin, snr_bin
        list cbr_subc_split, angle_dec, hex_split
        list cbr = []
        list snr = []
        int snr_idx, i, start, max_length
        cnp.ndarray[int] angle_bits_order

    hex_split = re.findall(r"..", binary)
    cbr_hex_join = "".join(hex_split)
    cbr_bin = cbr_hex_join.translate(hex_to_bin)

    # broken
    #ohex_split = re.findall(r"..", binary)[::-1]
    #ocbr_hex_join = "".join(ohex_split)
    #cbr_bin = ocbr_hex_join.translate(hex_to_bin)[::-1]
#
    #print("orig:", ocbr_bin)
    #print(cbr_bin)
    cbr_bin = "".join([ cbr_bin[x: x+8][::-1] for x in range(0, len(cbr_bin), 8) ]) 
    #print(cbr_bin)

    for i in range(num_snr):
        snr_bin = cbr_bin[i * 8 : (i + 1) * 8][::-1]
        if snr_bin[0] == "0":
            snr_idx = <int>int(snr_bin, 2)
        else:
            snr_idx = -(<int>int(snr_bin, 2) ^ 0b11111111)
        snr.append(-(-128 - snr_idx) * 0.25 - 10)

    cbr_bin = cbr_bin[num_snr * 8 :]
    max_length = num_subc * angle_seq_len
    #print(angle_bits_order)
    angle_bits_order = split_rule[1:] - split_rule[:-1]
    #print(angle_bits_order)
    for s in [cbr_bin[i : i + angle_seq_len] for i in range(0, max_length, angle_seq_len)]:
        #print(s, len(s))
        if len(s) != split_rule[-1]:
            continue
        angle_dec = [None] * (len(angle_bits_order))
        #print(angle_bits_order)
        start = 0
        for i in range(0, len(angle_bits_order)):
            angle_dec[i] = <int>int(s[start : start + angle_bits_order[i]][::-1], 2)
            #print("size", angle_bits_order[i], "\tdec", s[start : start + angle_bits_order[i]][::-1])
            start += angle_bits_order[i]
        #exit()
        cbr.extend(angle_dec)

    return cbr, snr


cdef inverse_givens_rotation(int nrx, int ntx, list angles, list angle_types, list angle_indices):
    cdef:
        cnp.ndarray[complex, ndim=2] mat_e = np.eye(N=nrx, M=ntx, dtype=complex)
        cnp.ndarray[complex, ndim=2] d_li = np.eye(N=nrx, M=nrx, dtype=complex)
        cnp.ndarray[complex, ndim=2] g_li = np.eye(nrx, nrx, dtype=complex)
        INT64 idx
        str a_t
        list a_i
        DOUBLE cos_val, sin_val
    #print(nrx,ntx,angles,angle_types,angle_indices)
    reverse_mat = []
    first = True
    for idx in range(len(angles)):
        last = angle_types[idx]
        if idx > 0:
            last = angle_types[idx-1]
        a_t = angle_types[idx]
        a_i = angle_indices[idx]
        #print(a_t, a_i)
        if a_t == "phi":
            if last != a_t:
                d_li = np.eye(nrx, nrx, dtype=complex)
            d_li[a_i[0], a_i[0]] = np.exp(1j * angles[idx])
            #print(f"D_{idx}: ", d_li)
        elif a_t == "psi":
            if last != a_t:
                if first:
                    mat_e = d_li
                    first = False
                else:
                    mat_e = mat_e @ d_li
                #print("RES_TEMP_PHI_TO_PSI: ", mat_e)
            cos_val = np.cos(angles[idx])
            sin_val = np.sin(angles[idx])
            g_li[a_i[1], a_i[1]] = cos_val
            g_li[a_i[1], a_i[0]] = sin_val
            g_li[a_i[0], a_i[1]] = -sin_val
            g_li[a_i[0], a_i[0]] = cos_val
            #print("G_li:",idx, g_li)
            mat_e = mat_e @ g_li.T 
            #print("RES: ", mat_e)

            g_li = np.eye(nrx, nrx, dtype=complex)
        else:
            raise ValueError("inverse_givens_rotation(): invalid angle type")

    return mat_e @ np.eye(N=nrx, M=ntx, dtype=complex)


cdef quantized_angle_formulas(str angle_type, int angle, int phi_size, int psi_size):
    angle_funcs = {
        "phi": lambda x: PI * x / (2.0 ** (phi_size - 1.0)) + PI / (2.0 ** (phi_size)),
        "psi": lambda x: PI * x / (2.0 ** (psi_size + 1.0))
        + PI / (2.0 ** (psi_size + 2.0)),
    }
    return angle_funcs[angle_type](angle)

