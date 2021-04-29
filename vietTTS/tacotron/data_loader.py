import random
from pathlib import Path
from typing import NamedTuple

import librosa
import numpy as np
from numpy import ndarray
from scipy.io import wavfile  # .read

from .config import *


class InputBatch(NamedTuple):
  text: ndarray
  text_len: ndarray
  wav: ndarray
  mel_len: ndarray


def load_text_wav(data_dir: Path, batch_size, pad_wav_len, pad_text_len, mode='train'):
  lines = open(data_dir / 'transcript.txt', 'r').readlines()
  lines = sorted([l.strip().split('|') for l in lines])
  rng = random.Random(42)
  if mode != 'gta':
    rng.shuffle(lines)
  L = len(lines) * 9 // 10
  data = lines[:L] if mode == 'train' else lines[L:]
  if mode == 'gta':
    data = lines

  batch = []
  cache = {}
  while True:
    if mode != 'gta':
      rng.shuffle(data)
    for ident, text in data:
      if not (ident in cache):
        sr, y = wavfile.read(data_dir / f'{ident}.wav')
        # y, sr = librosa.load(data_dir / f'{ident}.wav')
        # hop_length = int(sr * 12.5 / 1000)
        # win_length = hop_length * 4
        # y = librosa.effects.preemphasis(y, 0.85)
        wav_len = len(y)
        if len(y) > pad_wav_len:
          y = y[:pad_wav_len]
        y = np.pad(y, (0, pad_wav_len-len(y)))
        encoded_text = []
        for c in text:
          if c in FLAGS._alphabet:
            encoded_text.append(FLAGS._alphabet.index(c))
          else:
            encoded_text.append(0)
        text_len = len(encoded_text)
        encoded_text.extend([0] * (pad_text_len - len(encoded_text)))
        encoded_text = np.array(encoded_text)
        cache[ident] = (encoded_text, text_len, y, wav_len)
      else:
        encoded_text, text_len, y, wav_len = cache[ident]

      batch.append((encoded_text, text_len, y, wav_len))
      if len(batch) == batch_size:
        text, text_len, y, wav_len = zip(*batch)
        text = np.stack(text, axis=0)
        y = np.stack(y, axis=0)  # . astype(np.float) / (2**15)
        text_len = np.array(text_len)
        mel_len = np.array(wav_len) // (FLAGS.n_fft // 4)
        # print(y.shape)
        # mel = melfilter(y)
        yield InputBatch(text, text_len, y, mel_len)
        del batch
        batch = []


def load_text_wav_name(data_dir: Path, batch_size, pad_wav_len, pad_text_len, mode='train'):
  lines = open(data_dir / 'transcript.txt', 'r').readlines()
  lines = sorted([l.strip().split('|') for l in lines])
  data = lines  # [:L] if mode == 'train' else lines[L:]

  batch = []
  cache = {}
  for ident, text in data:
    if not (ident in cache):
      sr, y = wavfile.read(data_dir / f'{ident}.wav')
      # y, sr = librosa.load(data_dir / f'{ident}.wav')
      # hop_length = int(sr * 12.5 / 1000)
      # win_length = hop_length * 4
      # y = librosa.effects.preemphasis(y, 0.85)
      wav_len = len(y)
      if len(y) > pad_wav_len:
        y = y[:pad_wav_len]
      y = np.pad(y, (0, pad_wav_len-len(y)))
      encoded_text = []
      for c in text:
        if c in FLAGS._alphabet:
          encoded_text.append(FLAGS._alphabet.index(c))
        else:
          encoded_text.append(0)
      text_len = len(encoded_text)
      encoded_text.extend([0] * (pad_text_len - len(encoded_text)))
      encoded_text = np.array(encoded_text)
      cache[ident] = (encoded_text, text_len, y, wav_len)
    else:
      encoded_text, text_len, y, wav_len = cache[ident]

    batch.append((ident, encoded_text, text_len, y, wav_len))
    if len(batch) == batch_size:
      ident, text, text_len, y, wav_len = zip(*batch)
      text = np.stack(text, axis=0)
      y = np.stack(y, axis=0)  # . astype(np.float) / (2**15)
      text_len = np.array(text_len)
      mel_len = np.array(wav_len) // (FLAGS.n_fft // 4)
      # print(y.shape)
      # mel = melfilter(y)
      yield ident, InputBatch(text, text_len, y, mel_len)
      del batch
      batch = []