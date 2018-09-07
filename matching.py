import xml_data
import os
import ntpath
import shutil
import subprocess
from musicXML_parser.mxp.note import Note
import pretty_midi
import utils

ALIGN_TOOL_DIR = '/home/ilcobo2/AlignmentTool_v2'


class PerformPair(object):
  def __init__(self, xml_sequence, perform_midi_path):
    self.pairs = []
    self.score_pairs = []
    self.extra_pairs = []

    score_folder, _ = ntpath.split(xml_sequence.xml_path)
    xml_midi_path = os.path.join(score_folder, 'score.mid')
    if not os.path.isfile(xml_midi_path):
      xml_sequence.save_to_midi(xml_sequence.notes, xml_midi_path)

    if not os.path.isfile(os.path.join(score_folder, 'score_fmt3x.txt')):
      try:
        match(xml_midi_path, perform_midi_path)
      except:
        pass
    score_maps = read_corresp(perform_midi_path.replace('.mid', '_corresp.txt'))
    match_pairs = read_match(perform_midi_path.replace('.mid', '_match.txt'))

    perform_midi = pretty_midi.PrettyMIDI(perform_midi_path)
    perform_notes = perform_midi.instruments[0].notes
    perform_notes.sort(key=lambda note: note.start)

    for pair in match_pairs:
      if pair.perform_second is not None:
        cand_idx = utils.find_le_idx([el.start for el in perform_notes], pair.perform_second - 0.01)
        if cand_idx is None:
          cand_idx = 0
        for n in range(cand_idx, len(perform_notes)):
          cand_note = perform_notes[n]
          if cand_note.start - pair.perform_second > 0.01:
            break
          if cand_note.pitch == pair.perform_pitch:
            pair.midi_note = cand_note
            break
        if pair.midi_note is None:
          print(cand_idx)
          raise RuntimeError('No matching perform_second: {:.4f}, perform note: {}'.format(perform_notes[cand_idx].start, pair.__dict__))
      if pair.score_id is not None:
        score_info = score_maps[pair.score_id]
        pair.score_pitch = score_info[0]
        pair.score_second = score_info[1]
        cand_idx = utils.find_le_idx([el.note_duration.time_position for el in xml_sequence.notes],
                                     pair.score_second - 0.01)

        if cand_idx is None:
          cand_idx = 0
        for n in range(cand_idx, len(xml_sequence.notes)):
          cand_note = xml_sequence.notes[n]
          if cand_note.note_duration.time_position - pair.score_second >= 0.01:
            break
          if cand_note.pitch[1] == pair.score_pitch:
            pair.score_note = cand_note
            break

        if pair.score_note is None:
          print(cand_idx)
          raise RuntimeError('No matching score_second: {:.4f}, perform note: {}'.
                             format(xml_sequence.notes[cand_idx].note_duration.time_position, pair.__dict__))
      if pair.score_note is not None:
        self.score_pairs.append(pair)
      else:
        self.extra_pairs.append(pair)

    self.sort_pairs()
    self.pairs = self.score_pairs + self.extra_pairs

  def sort_pairs(self):
    self.score_pairs.sort(key=lambda x: (x.score_note.note_duration.xml_position,
                                         x.score_note.note_duration.grace_order,
                                         -x.score_note.pitch[1]))
    self.extra_pairs.sort(key=lambda x: (x.midi_note.start, -x.midi_note.pitch))


class Pair(object):
  def __init__(self):
    self.score_note = None
    self.score_note_idx = None
    self.midi_note_idx = None
    self.midi_note = None
    self.score_id = None
    self.score_pitch = None
    self.score_second = None
    self.perform_pitch = None
    self.perform_second = None


def match(score_midi, perform_midi):
  score_midi = os.path.abspath(score_midi)
  perform_midi = os.path.abspath(perform_midi)
  shutil.copy(perform_midi, os.path.join(ALIGN_TOOL_DIR, 'perform.mid'))
  shutil.copy(score_midi, os.path.join(ALIGN_TOOL_DIR, 'score.mid'))
  current_path = os.getcwd()
  os.chdir(ALIGN_TOOL_DIR)
  try:
    subprocess.check_call(["sudo", "sh", "MIDIToMIDIAlign.sh", "score", "perform"])
  except:
    print('Error to process {}'.format(perform_midi))
  else:
    score_subfolder, _ = ntpath.split(score_midi)
    shutil.move('score_fmt3x.txt', os.path.join(score_subfolder, 'score_fmt3x.txt'))
    shutil.move('perform_match.txt', perform_midi.replace('.mid', '_match.txt'))
    shutil.move('perform_corresp.txt', perform_midi.replace('.mid', '_corresp.txt'))
    os.chdir(current_path)


def read_corresp(corresp_file):
  score_map = dict()
  f = open(corresp_file, 'r')
  lines = f.readlines()
  f.close()
  for line in lines[1:]:
    els = line.split()
    if els[5] == '*':
      continue
    second = float(els[6])
    id = els[5]
    pitch = int(els[8])
    score_map[id] = (pitch, second)

  return score_map


def read_fmt3x(fmt3x_file):
  score_map = dict()
  f = open(fmt3x_file, 'r')
  lines = f.readlines()
  f.close()
  tpqn = float(lines[0].split()[-1])
  for line in lines[2:]:
    els = line.split()
    second = int(els[0]) / tpqn
    n_notes = int(els[8])
    for n in range(n_notes):
      id = els[-(1+n)].split('-')[-1]
      pitch_word = els[-(1 + 2*n_notes + n)]
      pitch = pitch_word_to_pitch(pitch_word)

      score_map[id] = (pitch, second)

  return score_map


def read_match(match_file):
  matches = []
  f = open(match_file, 'r')
  lines = f.readlines()
  f.close()
  for line in lines[4:]:
    pair = Pair()
    els = line.split()
    if els[0] == '//Missing':
      pair.score_id = els[-1].split('-')[-1]
    else:
      pair.perform_second = float(els[1])
      pair.perform_pitch = pitch_word_to_pitch(els[3])
      if els[9] != '*':
        pair.score_id = els[9].split('-')[-1]
      else:
        pass
    matches.append(pair)
  return matches


def pitch_word_to_pitch(word):
  if len(word) == 3:
    if word[1] == '#':
      alter = 1
    elif word[1] == 'b':
      alter = -1
    else:
      print(word)
      raise ValueError
  else:
    alter = 0
  return Note.pitch_to_midi_pitch(word[0], alter, word[-1])