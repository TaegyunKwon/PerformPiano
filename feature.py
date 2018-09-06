# -*- coding: utf-8 -*-

from __future__ import division

import argparse
import utils


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("--data_path", default='/dataset/chopin_cleaned')
  parser.add_argument("--save_path", default='./features')
  args = parser.parse_args()


class NoteFeatures(object):
  def __init__(self, score_note, perform_note):
    self.score_note = None
    self.perform_note = None

    self.features = dict()

  def add_pitch(self):
    self.features['pitch'] = self.score_note.pitch


class ScoreFeatures(object):
  def __init__(self, xml_sequence, pairs):
    self.xml_sequence = xml_sequence
    self.note_features = NoteFeatures(pairs)

    self.measure_positions = [el.start_xml_position for el in self.xml_sequence.xml_Doc.parts[0].measures]
    self.time_signatures = self.xml_sequence.meta.time_signatures

    self.add_beat_info()


  def add_beat_info(self):
    measure_positions = [el.start_xml_position for el in self.xml_sequence.xml_Doc.parts[0].measures]
    time_signatures = self.xml_sequence.meta.time_signatures
    self.features['beat_info'] = []
    for pair in self.pairs.score_pairs:
      measure_start = measure_positions[pair.score_note.measure_number - 1]
      current_time_sig_idx = utils.find_le_idx([el.xml_position for el in time_signatures], measure_start)
      current_time_sig = time_signatures[current_time_sig_idx]
      beat_length = (current_time_sig.state.divisions / current_time_sig.denominator * 4)
      beat_loc = (pair.score_note.note_duration.time_position - measure_start) / beat_length
      self.features['beat_info'].append((beat_loc, beat_length, current_time_sig))


class Features(ScoreFeatures):
  def __init__(self, xml_sequence, pairs):
    super(Features, self).__init__(xml_sequence, pairs)


  def beat_level_tempo(self):
    on_beat_pairs = [el for el in self.pairs.score_pairs if abs(el.beat_loc % 1) <= 0.1]
    tempos = []
    for n in range(len(on_beat_pairs)):
      for m in range(n, len(on_beat_pairs)):
        if on_beat_pairs[n].
    pass


def deviation_tempo(xml_sequence, perform_pair):
  pass


def deviation_from_first_onset(xml_sequence, perform_pair):
  pass


def beat_level_velocity(xml_sequence, perform_pair):
  pass


def velocity_deviation(xml_sequence, perform_pair):
  pass


def articaulation(xml_sequence, perform_pair):
  pass


def pedal_features(xml_sequence, perform_pair, midis):
  pass