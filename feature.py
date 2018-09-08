# -*- coding: utf-8 -*-

from __future__ import division

import argparse
import utils
import numpy as np
from musicXML_parser.mxp.notations import Notations
import constants

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
    self.note_length = None
    self.beat_location = None
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
    self.add_beat_info()
    self.add_ioi_info()

  def add_beat_info(self):
    for note_feature in self.note_features:
      measure_number = note_feature.score_note.measure_number
      measure_start = self.measure_positions[measure_number]
      current_time_sig_idx = utils.find_le_idx([el.xml_position for el in self.time_signatures], measure_start)
      current_time_sig = self.time_signatures[current_time_sig_idx]
      beat_length = (current_time_sig.state.divisions / current_time_sig.denominator * 4)
      note_feature.note_length = note_feature.score_note.note_duration.duration / beat_length
      note_feature.beat_location = (note_feature.score_note.note_duration.xml_position - measure_start) / beat_length

  def add_ioi_info(self):
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


'''
class Features(ScoreFeatures):
  def __init__(self, xml_sequence, score_pairs):
    super(Features, self).__init__(xml_sequence, score_pairs)


  def beat_level_tempo(self):
    on_beat_pairs = [el for el in self.pairs.score_pairs if abs(el.beat_loc % 1) <= 0.1]
    tempos = []
    for n in range(len(on_beat_pairs)):
      for m in range(n, len(on_beat_pairs)):
        if on_beat_pairs[n].
    pass
'''

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