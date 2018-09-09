# -*- coding: utf-8 -*-

from __future__ import division

import argparse
import utils
import numpy as np
from musicXML_parser.mxp.notations import Notations
import constants
import warnings
import itertools
import random

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("--data_path", default='/dataset/chopin_cleaned')
  parser.add_argument("--save_path", default='./features')
  args = parser.parse_args()


class NoteFeatures(object):
  def __init__(self, score_note, perform_note):
    self.score_note = score_note
    self.perform_note = perform_note

    self.score_features = dict()
    self.perform_features = dict()

    self.pitch = self.score_note.pitch
    self.note_length = self.score_note.length_in_beat
    self.beat_location = self.score_note.beat_location
    self.score_ioi = None
    self.notation = self.notation_to_category()
    self.dynamic = self.dynamics_to_category()
    self.tempo = self.tempo_to_category()

  def add_pitch(self):
    self.score_features['pitch'] = self.score_note.pitch

  def notation_to_category(self):
    notation = self.score_note.note_notations
    return np.asarray([notation.is_accent or notation.is_strong_accent,
                       notation.is_fermata,
                       notation.is_staccato,
                       notation.is_tenuto]).astype(int)

  def dynamics_to_category(self):
    dynamic_embed_table = constants.dynamic_table()
    dynamic_words = utils.direction_words_flatten(self.score_note.dynamic)
    return dynamic_embedding(dynamic_words, dynamic_embed_table)

  def tempo_to_category(self):
    tempo_embed_table = constants.tempo_table()
    tempo_words = utils.direction_words_flatten(self.score_note.tempo)
    return dynamic_embedding(tempo_words, tempo_embed_table, len_vec=3)


class ScoreFeatures(object):
  def __init__(self, xml_sequence, score_pairs):
    self.xml_sequence = xml_sequence

    self.measure_positions = [el.start_xml_position for el in self.xml_sequence.xml_doc.parts[0].measures]
    self.time_signatures = self.xml_sequence.meta.time_signatures
    self.note_features = [NoteFeatures(el.score_note, el.midi_note) for el in score_pairs]
    self.note_groups = []
    # self.deprecated_add_beat_info()
    self.add_ioi_info()

  def add_ioi_info(self):
    concurrent_notes = []
    last_position = self.note_features[0].score_note.beat_position
    for n in range(len(self.note_features)):
      current_feature = self.note_features[n]
      current_position = current_feature.score_note.beat_position
      if last_position == current_position:
        concurrent_notes.append(self.note_features[n])
      else:
        for note in concurrent_notes:
          note.score_ioi = current_position - last_position
        last_position = current_position
        concurrent_notes = [current_feature]

    # handle last concurrent_notes
    self.note_groups.append(concurrent_notes)
    for note in concurrent_notes:
      note.score_ioi = np.inf

  def deprecated_add_beat_info(self):
    for note_feature in self.note_features:
      measure_number = note_feature.score_note.measure_number
      measure_start = self.measure_positions[measure_number]
      current_time_sig_idx = utils.find_le_idx([el.xml_position for el in self.time_signatures], measure_start)
      current_time_sig = self.time_signatures[current_time_sig_idx]
      beat_length = (current_time_sig.state.divisions / current_time_sig.denominator * 4)
      note_feature.note_length = note_feature.score_note.note_duration.duration / beat_length
      note_feature.beat_location = (note_feature.score_note.note_duration.xml_position - measure_start) / beat_length

  def deprecated_add_ioi_info(self):
    concurrent_notes = []
    last_position = self.note_features[0].score_note.note_duration.xml_position
    for n in range(len(self.note_features)):
      current_feature = self.note_features[n]
      current_position = current_feature.score_note.note_duration.xml_position
      if last_position == current_position:
        concurrent_notes.append(self.note_features[n])
      else:
        last_position = current_position
        last_feature = concurrent_notes[-1]
        if last_feature.score_note.measure_number == current_feature.score_note.measure_number:
          for note in concurrent_notes:
            note.score_ioi = current_feature.beat_location - last_feature.beat_location
        else:
          for note in concurrent_notes:
            # TODO: what if time signature change?
            note.score_ioi = (last_feature.score_note.state.time_signature.numerator *
                              (current_feature.score_note.measure_number - last_feature.score_note.measure_number)
                              + current_feature.beat_location
                              - last_feature.beat_location)
        self.note_groups.append(concurrent_notes)
        concurrent_notes = [current_feature]

    # handle last concurrent_notes
    self.note_groups.append(concurrent_notes)
    for note in concurrent_notes:
      note.score_ioi = np.inf


class Features(ScoreFeatures):
  def __init__(self, xml_sequence, score_pairs):
    super(Features, self).__init__(xml_sequence, score_pairs)
    self.duration = None
    self.moving_dynamics = None
    self.moving_tempo = None
    self.global_tempo = None

    self.calculate_base_tempo()
    self.calculate_tempo()
    self.interpolate_tempo()
    # self.calculate_dynamics()

  def calculate_base_tempo(self):
    # calculate mean tempo per abs_tempo region
    abs_tempos = self.xml_sequence.meta.abs_tempos
    tempo_region = [el.xml_position for el in abs_tempos]
    if tempo_region[0] != 0:
      tempo_region.insert(0, 0)

    nth_tempo = 0
    note_start = None
    note_end = None
    note_in_region = []
    for n in range(len(self.note_features)):
      note_feature = self.note_features[n]
      if tempo_region[nth_tempo] <= note_feature.score_note.note_duration.xml_position\
          or n == len(self.note_features) - 1:
        nth_tempo += 1
        for note in note_in_region:
          if note.perform_note:
            note_start = note
            break
        for note in reversed(note_in_region):
          if note.perform_note:
            if note.perform_note:
              note_end = note
              break
        if note_start is None or note_end is None:
          warnings.warn('no perform match in tempo area')
        else:
          beat_interval = note_end.score_note.beat_position - note_start.score_note.beat_position
          if beat_interval != 0:
            base_tempo = 60 * beat_interval / (note_end.perform_note.start - note_start.perform_note.start)
          else:
            warnings.warn('no proper perform match (only same beat) in tempo area')
        for note in note_in_region:
          note.perform_features['base_tempo'] = base_tempo
          note_in_region = [note_feature]
      else:
        note_in_region.append(note_feature)

  def calculate_tempo(self):
    def _safe_average_tempo(tempos):
      tempos = [el for el in tempos if 50 < el < 180]
      if not tempos:
        return None
      else:
        med_tempo = np.median(tempos)
        tempos = [el for el in tempos if med_tempo*0.8 > el > med_tempo*1.2]
        return np.mean(tempos)

    for n_group in range(len(self.note_groups)-1):
      current_group = self.note_groups[n_group]
      next_group = self.note_groups[n_group + 1]
      beat_interval = next_group[0].score_note.beat_position - current_group[0].score_note.beat_position
      current_time = [el.perform_note.start for el in current_group if el.perform_note is not None]
      next_time = [el.perform_note.start for el in next_group if el.perform_note is not None]

      if current_time and next_time:
        time_diffs = list(itertools.product(current_time, next_time))
        tempo = _safe_average_tempo([60 * beat_interval / (el[1] - el[0]) for el in time_diffs])
        for note in current_group:
          note.perform_features['local_tempo'] = tempo
      else:
        for note in current_group:
          note.perform_features['local_tempo'] = None

  def interpolate_tempo(self):
    def _interpolate_groups_in_region(note_groups):
      # interpolate first/last tempos
      if note_groups[0].perform_features['local_tempo'] is None:
        for n in range(len(note_groups)):
          if note_groups[n][0].perform_features['local_tempo'] is not None:
            local_tempo = note_groups[n][0].perform_features['local_tempo']
            for m in range(n - 1):
              fluctuation = (0.2 * random.random() + 0.9)
              for note in note_groups[m]:
                note.perform_features['local_tempo'] = local_tempo * fluctuation
            break

      elif note_groups[-1][0].perform_features['local_tempo'] is None:
        for n in reversed(range(len(note_groups))):
          if note_groups[n][0].perform_features['local_tempo'] is not None:
            local_tempo = note_groups[n][0].perform_features['local_tempo']
            for m in range(n + 1, len(note_groups)):
              fluctuation = (0.2 * random.random() + 0.9)
              for note in note_groups[m]:
                note.perform_features['local_tempo'] = local_tempo * fluctuation
            break

      groups_to_interpolate = []
      interpolate_start = 0
      for n in range(len(note_groups)):
        if note_groups[n][0].perform_features['local_tempo'] is None:
          groups_to_interpolate.append(note_groups)
        else:
          if groups_to_interpolate is not None:
            interpol_start_group = note_groups[interpolate_start]
            interpol_end_group = note_groups[n]

            beat_interval = interpol_end_group[0].beat_position - interpol_start_group[0].beat_position
            for group in groups_to_interpolate:
              interpol_ratio = (group[0].beat_position - interpol_start_group[0].beat_position) / beat_interval
              interpol_tempo = interpol_ratio * interpol_end_group[0].perform_features['local_tempo'] + \
                               (1 - interpol_ratio) * interpol_start_group[0].perform_features['local_tempo']
              fluctuation = (0.2 * random.random() + 0.9)
              for note in group:
                note.perform_features['local_tempo'] = interpol_tempo * fluctuation
          groups_to_interpolate = []
          interpolate_start = n

    # group tempo by abs tempo
    abs_tempos = self.xml_sequence.meta.abs_tempos
    tempo_region = [el.xml_position for el in abs_tempos]
    if tempo_region[0] != 0:
      tempo_region.insert(0, 0)
    group_xml_positions = [el[0].score_note.note_duration.xml_position for el in self.note_groups]
    note_groups_index_in_regions = [utils.find_ge_idx(group_xml_positions, el) for el in tempo_region]
    note_groups_in_regions = []
    for n in range(len(note_groups_index_in_regions)):
      if n != len(note_groups_index_in_regions) -1:
        note_groups_in_regions.append(
          self.note_groups[note_groups_index_in_regions[n]: note_groups_index_in_regions[n+1]])
      else:
        note_groups_in_regions.append(self.note_groups[note_groups_index_in_regions[n]:])
    for groups in note_groups_in_regions:
      _interpolate_groups_in_region(groups)

  def add_velocity(self):
    for note_feature in self.note_features:
      if note_feature.perform_note is not None:
        note_feature.perform_features['velocity'] = note_feature.perform_note.velocity
      else:
        note_feature.perform_features['velocity'] = None

  

def dynamic_embedding(dynamic_word, embed_table, len_vec=4):
  dynamic_vector = [0] * len_vec
  dynamic_vector[0] = 0.5
  keywords = embed_table.keywords

  if dynamic_word == None:
    return dynamic_vector
  if dynamic_word in embed_table.keywords:
    index = utils.find_index_list_of_list(dynamic_word, keywords)
    vec_idx = embed_table.embed_key[index].vector_index
    dynamic_vector[vec_idx] = embed_table.embed_key[index].value

  # for i in range(len(keywords)):
  #     keys = keywords[i]
  #     if type(keys) is list:
  #         for key in keys:
  #             if len(key)>2 and (key.encode('utf-8') in
  word_split = dynamic_word.replace(',', ' ').replace('.', ' ').split(' ')
  for w in word_split:
    index = utils.find_index_list_of_list(w.lower(), keywords)
    if index:
      vec_idx = embed_table.embed_key[index].vector_index
      dynamic_vector[vec_idx] = embed_table.embed_key[index].value

  for key in keywords:
    if isinstance(key, str) and len(key) > 2 and key in dynamic_word:
      # if type(key) is st and len(key) > 2 and key in attribute:
      index = keywords.index(key)
      vec_idx = embed_table.embed_key[index].vector_index
      dynamic_vector[vec_idx] = embed_table.embed_key[index].value

  return dynamic_vector


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