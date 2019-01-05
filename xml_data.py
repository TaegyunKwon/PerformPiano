#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import copy
import warnings
import utils
from utils import find_le_idx
from musicXML_parser.mxp import MusicXMLDocument
import constants
import pretty_midi
from midi_utils import midi_utils
from fractions import Fraction


class XmlNoteSequence(object):
  def __init__(self, xml_file):
    self.xml_path = xml_file
    self.xml_doc = MusicXMLDocument(xml_file)
    self.notes = []
    self.rests = []
    self.meta = XmlMeta(self.xml_doc)
    self._process_notes()
    self._apply_meta_to_notes()

    self.total_length = self.cal_total_xml_length(self.notes)
    self.num_notes = len(self.notes)

  def _process_notes(self):
    processed_notes = XmlNotes(self.xml_doc)
    self.notes = processed_notes.notes
    self.rests = processed_notes.rests

  def _apply_meta_to_notes(self):
    def _divide_cresc_staff(note):
      # check the note has both crescendo and diminuendo (only wedge type)
      cresc = False
      dim = False
      for rel in note.dynamic.relative:
        if rel.type['type'] == 'crescendo':
          cresc = True
        elif rel.type['type'] == 'diminuendo':
          dim = True

      if cresc and dim:
        delete_list = []
        for i in range(len(note.dynamic.relative)):
          rel = note.dynamic.relative[i]
          if rel.type['type'] in ['crescendo', 'diminuendo']:
            if (rel.placement == 'above' and note.staff == 2) or (rel.placement == 'below' and note.staff == 1):
              delete_list.append(i)
        for i in sorted(delete_list, reverse=True):
          del note.dynamic.relative[i]

      return note

    time_signatures = self.meta.time_signatures
    abs_dynamics = self.meta.abs_dynamics
    abs_tempos = self.meta.abs_tempo

    for note in self.notes:
      note_position = note.note_duration.xml_position

      idx = find_le_idx([el.xml_position for el in abs_dynamics], note_position)
      if idx is not None:
        note.dynamic.absolute = abs_dynamics[idx].type['content']

      idx = find_le_idx([el.xml_position for el in abs_tempos], note_position)
      if idx is not None:
        note.tempo.absolute = abs_tempos[idx].type['content']

      idx = find_le_idx([el.xml_position for el in time_signatures], note_position)
      if idx is not None:
        note.tempo.time_numerator = time_signatures[idx].numerator
        note.tempo.time_denominator = time_signatures[idx].denominator

      # have to improve algorithm
      for rel in self.meta.rel_dynamics:
        try:
          rel.end_xml_position
        except:
          print(rel.__dict__)
        if rel.xml_position <= note_position <= rel.end_xml_position:
          note.dynamic.relative.append(rel)
      if len(note.dynamic.relative) > 1:
        note = _divide_cresc_staff(note)

      for rel in self.meta.rel_tempo:
        if rel.xml_position <= note_position < rel.end_xml_position:
          note.tempo.relative.append(rel)

  @staticmethod
  def cal_total_xml_length(xml_notes):
    latest_end = 0
    latest_start = 0
    xml_len = len(xml_notes)
    for i in range(1, xml_len):
      note = xml_notes[-i]
      current_end = note.note_duration.xml_position + note.note_duration.duration
      if current_end > latest_end:
        latest_end = current_end
        latest_start = note.note_duration.xml_position
      elif current_end < latest_start - note.note_duration.duration * 4:
        break
    return latest_end

  @staticmethod
  def save_to_midi(xml_notes, save_path, quantize_pedal=True, disklavier=True):
    mid = pretty_midi.PrettyMIDI()
    program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
    instrument = pretty_midi.Instrument(program=program)

    for note in xml_notes:
      if note.is_overlapped:  # ignore overlapped notes.
        continue

      pitch = note.pitch[1]
      start = note.note_duration.time_position
      end = start + note.note_duration.seconds
      if note.note_duration.seconds < 0.005:
        end = start + 0.005
      elif note.note_duration.seconds > 10:
        end = start + 10
      velocity = int(min(max(note.velocity, 0), 127))
      midi_note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=start, end=end)

      midi_note.pedal_at_start = note.pedal.at_start
      midi_note.pedal_at_end = note.pedal.at_end
      midi_note.pedal_refresh = note.pedal.refresh
      midi_note.pedal_refresh_time = note.pedal.refresh_time
      midi_note.pedal_cut = note.pedal.cut
      midi_note.pedal_cut_time = note.pedal.cut_time
      midi_note.soft_pedal = note.pedal.soft
      instrument.notes.append(midi_note)

    mid.instruments.append(instrument)

    mid = midi_utils.save_note_pedal_to_CC(mid)
    if quantize_pedal:
      pedals = mid.instruments[0].control_changes
      for pedal in pedals:
        if pedal.value < 75:
          pedal.value = 0

    if disklavier:
      pedals = mid.instruments[0].control_changes
      pedals.sort(key=lambda x: x.time)
      previous_off_time = 0
      for pedal in pedals:
        if pedal.time < 0.3:
          continue
        if pedal.value < 75:
          previous_off_time = pedal.time
        else:
          time_passed = pedal.time - previous_off_time
          if time_passed < 0.3:
            pedals.remove(pedal)
      mid.instruments[0].control_changes = pedals
    mid.write(save_path)


class XmlMeta(object):
  def __init__(self, xml_doc):
    self.xml_doc = xml_doc
    self.directions, self.time_signatures = self.extract_directions()
    self.abs_dynamics, self.rel_dynamics = self.get_dynamics()
    self.abs_tempo, self.rel_tempo = self.get_tempos()

  def extract_directions(self):
    directions = []
    for part in self.xml_doc.parts:
      for measure in part.measures:
        for direction in measure.directions:
          directions.append(direction)

    directions.sort(key=lambda x: x.xml_position)
    cleaned_direction = []
    for i in range(len(directions)):
      direction = directions[i]
      if direction.type is not None:
        if direction.type['type'] == "none":
          for j in range(i):
            prev_dir = directions[i - j - 1]
            if 'number' in prev_dir.type.keys():
              prev_key = prev_dir.type['type']
              prev_num = prev_dir.type['number']
            else:
              continue
            if prev_num == direction.type['number']:
              if prev_key == "crescendo":
                direction.type['type'] = 'crescendo'
                break
              elif prev_key == "diminuendo":
                direction.type['type'] = 'diminuendo'
                break
        cleaned_direction.append(direction)
      else:
        warnings.warn("direction with empty type.\n{}".format(vars(direction.xml_direction)), RuntimeWarning)

    time_signatures = self.xml_doc.get_time_signatures()
    return cleaned_direction, time_signatures

  def get_tempos(self):
    absolute_tempos = utils.extract_directions_by_keywords(self.directions, constants.ABS_TEMPOS)
    relative_tempos = utils.extract_directions_by_keywords(self.directions, constants.REL_TEMPOS)

    absolute_tempos_position = [tmp.xml_position for tmp in absolute_tempos]
    num_abs_tempos = len(absolute_tempos)
    num_rel_tempos = len(relative_tempos)

    for tempo in absolute_tempos:
      if 'tempo i' in tempo.type['content'].lower():
        tempo.type['content'] = absolute_tempos[0].type['content']

    for i in range(num_rel_tempos):
      rel = relative_tempos[i]
      if i + 1 < num_rel_tempos:
        rel.end_xml_position = relative_tempos[i + 1].xml_position
      index = find_le_idx(absolute_tempos_position, rel.xml_position)
      if index is None:
        warnings.warn("No abs_tempo found before rel_tempo." +
                      "\nabsolute_tempo_position: {}".format(absolute_tempos_position) +
                      "\nrel_tempo: {}".format(rel.__dict__), RuntimeWarning)
        continue
      rel.previous_tempo = absolute_tempos[index].type['content']
      if index + 1 < num_abs_tempos:
        rel.next_tempo = absolute_tempos[index + 1].type['content']
        if not hasattr(rel, 'end_xml_position') or rel.end_xml_position > absolute_tempos_position[index + 1]:
          rel.end_xml_position = absolute_tempos_position[index + 1]
      if not hasattr(rel, 'end_xml_position'):
        rel.end_xml_position = float("inf")

    return absolute_tempos, relative_tempos

  def get_dynamics(self):
    def _merge_start_end_of_direction(directions):
      for i in range(len(directions)):
        current_direction = directions[i]
        type_name = current_direction.type['type']
        if type_name in ['crescendo', 'diminuendo', 'pedal'] and current_direction.type['content'] == "stop":
          for j in range(i):
            prev_dir = directions[i - j - 1]
            prev_type_name = prev_dir.type['type']
            if type_name == prev_type_name and prev_dir.type['content'] == "start" and current_direction.staff == prev_dir.staff:
              prev_dir.end_xml_position = current_direction.xml_position
              break
      dir_dummy = []
      for current_direction in directions:
        type_name = current_direction.type['type']
        if type_name in ['crescendo', 'diminuendo', 'pedal'] and current_direction.type['content'] != "stop":
          # directions.remove(dir)
          dir_dummy.append(current_direction)
        elif type_name == 'words':
          dir_dummy.append(current_direction)
      directions = dir_dummy
      return directions

    temp_abs_key = constants.ABS_DYNAMICS
    temp_abs_key.append('dynamic')  # TODO: what's the purpose?

    absolute_dynamics = utils.extract_directions_by_keywords(self.directions, temp_abs_key)
    relative_dynamics = utils.extract_directions_by_keywords(self.directions, constants.REL_DYNAMCIS)
    abs_dynamic_dummy = []
    for abs in absolute_dynamics:
      if abs.type['content'] in ['sf', 'fz', 'sfz', 'sffz']:
        relative_dynamics.append(abs)
      else:
        abs_dynamic_dummy.append(abs)
        if abs.type['content'] == 'fp':
          abs.type['content'] = 'f sfz'
          abs2 = copy.copy(abs)
          abs2.xml_position += 1
          abs2.type = copy.copy(abs.type)
          abs2.type['content'] = 'p'
          abs_dynamic_dummy.append(abs2)

    absolute_dynamics = abs_dynamic_dummy

    relative_dynamics.sort(key=lambda x: x.xml_position)
    relative_dynamics = _merge_start_end_of_direction(relative_dynamics)
    absolute_dynamics_position = [dyn.xml_position for dyn in absolute_dynamics]

    for rel in relative_dynamics:
      index = find_le_idx(absolute_dynamics_position, rel.xml_position)
      if index is None:
        warnings.warn("No abs_dynamic found before rel_dynamic." +
                      "\nabsolute_dynamics_position: {}".format(absolute_dynamics_position) +
                      "\nrel_dynamic: {}".format(rel.__dict__), RuntimeWarning)
        rel.previous_dynamic = None
        index = 0
      else:
        rel.previous_dynamic = absolute_dynamics[index].type['content']
      if rel.type['type'] == 'dynamic':  # sf, fz, sfz
        rel.end_xml_position = rel.xml_position
      if index + 1 < len(absolute_dynamics):
        rel.next_dynamic = absolute_dynamics[index + 1].type['content']
        if not hasattr(rel, 'end_xml_position'):
          rel.end_xml_position = absolute_dynamics_position[index + 1]
      if not hasattr(rel, 'end_xml_position'):
        rel.end_xml_position = float("inf")
    return absolute_dynamics, relative_dynamics


class XmlNotes(object):
  def __init__(self, xml_doc):
    self.xml_doc = xml_doc
    self.notes, self.rests = self.read_notes()
    self.mark_after_grace_note_to_chord_notes()
    self.remove_tied_notes()
    self.notes.sort(key=lambda x: (x.note_duration.xml_position, x.note_duration.grace_order, -x.pitch[1]))
    self.mark_duplicate_notes()
    # self.apply_rest_to_note()
    # self.rearrange_chord_index()

  def read_notes(self):
    def duration_ratio(grace_note):
      duration_ratio = Fraction(1, 1)
      type_ratio = constants.TYPE_RATIO_MAP[grace_note.note_duration._type]

      # Compute tuplet ratio
      duration_ratio /= grace_note.note_duration.tuplet_ratio
      type_ratio /= grace_note.note_duration.tuplet_ratio

      # Add augmentation dots
      one_half = Fraction(1, 2)
      dot_sum = Fraction(0, 1)
      for dot in range(grace_note.note_duration.dots):
        dot_sum += (one_half ** (dot + 1)) * type_ratio

      ratio = type_ratio + dot_sum

      return ratio.numerator / ratio.denominator

    def _order_grace_notes(note, previous_grace_notes):
      rest_grc = []
      added_grc = []
      sec_to_following = 0
      beat_to_following = 0
      # xml_time_to_following = 0
      for (grace_order, grc) in enumerate(reversed(previous_grace_notes)):
        if grc.voice == note.voice:
          note.note_duration.after_grace_note = True
          grc.note_duration.grace_order = -(1 + grace_order)  # start from -1

          dur_seconds = duration_ratio(grc) * grc.state.seconds_per_quarter
          # dur_xml_time = duration_ratio(grc) * (grc.state.divisions / grc.state.time_signature.denominator * 4)
          grc.note_duration.time_position -= sec_to_following + dur_seconds
          grc.beat_position -= beat_to_following + grc.length_in_beat
          grc.beat_location -= beat_to_following + grc.length_in_beat
          # grc.note_duration.xml_position -= xml_time_to_following + dur_xml_time
          sec_to_following += dur_seconds
          beat_to_following += grc.length_in_beat
          # xml_time_to_following += dur_xml_time

          grc.following_note = note
          added_grc.append(grc)
        else:
          rest_grc.append(grc)
      num_added = len(added_grc)
      for grc in added_grc:
        grc.note_duration.num_grace = num_added
      return rest_grc

    parts = self.xml_doc.parts[0]
    notes = []
    previous_grace_notes = []
    rests = []
    measure_beat_position = 0
    for measure in parts.measures:
      measure.beat_position = measure_beat_position
      measure_start = measure.start_xml_position
      time_sig = measure.state.time_signature
      beat_length = (time_sig.state.divisions / time_sig.denominator * 4)
      for note in measure.notes:
        note.length_in_beat = note.note_duration.duration / beat_length
        note.beat_location = (note.note_duration.xml_position - measure_start) / beat_length
        note.beat_position = measure_beat_position + note.beat_location
        if note.note_duration.is_grace_note:
          previous_grace_notes.append(note)
          notes.append(note)

        elif not note.is_rest:
          notes.append(note)
          if previous_grace_notes:
            previous_grace_notes = _order_grace_notes(note, previous_grace_notes)

        else:
          assert note.is_rest
          if note.is_print_object:
            rests.append(note)

      measure_beat_position += measure.duration / beat_length
    return notes, rests

  def mark_after_grace_note_to_chord_notes(self):
    after_grace_notes = [el for el in self.notes if el.note_duration.after_grace_note]
    for note in after_grace_notes:
      onset = note.note_duration.xml_position
      voice = note.voice
      chords = [el for el in self.notes if (el.note_duration.xml_position == onset and el.voice == voice)]
      for chord_note in chords:
        chord_note.note_duration.after_grace_note = True

  def remove_tied_notes(self):
    removed_forward = []
    for i in range(len(self.notes)):
      current_note = self.notes[i]
      if current_note.note_notations.tied_stop:
        for j in reversed(range(len(removed_forward))):
          if removed_forward[j].note_notations.tied_start and \
             removed_forward[j].pitch[1] == current_note.pitch[1]:
            removed_forward[j].note_duration.seconds += current_note.note_duration.seconds
            removed_forward[j].note_duration.duration += current_note.note_duration.duration
            removed_forward[j].note_duration.midi_ticks += current_note.note_duration.midi_ticks
            removed_forward[j].length_in_beat += current_note.length_in_beat
            break
          if j == 0:
            warnings.warn("Any note found to match tied_stop. note: {:d}".format(i), RuntimeWarning)
      else:
        removed_forward.append(self.notes[i])
    self.notes = removed_forward

  def mark_duplicate_notes(self):
    previous_onset = -1
    notes_on_onset = []
    pitches = []
    for note in self.notes:
      if note.note_duration.is_grace_note:
        continue  # does not count grace note, because it can have same pitch on same xml_position
      if note.note_duration.xml_position > previous_onset:
        previous_onset = note.note_duration.xml_position
        pitches = []
        pitches.append(note.pitch[1])
        notes_on_onset = []
        notes_on_onset.append(note)
      else:  # note has same xml_position
        if note.pitch[1] in pitches:  # same pitch with same
          index_of_same_pitch_note = pitches.index(note.pitch[1])
          previous_note = notes_on_onset[index_of_same_pitch_note]
          if previous_note.note_duration.duration > note.note_duration.duration:
            note.is_overlapped = True
          else:
            previous_note.is_overlapped = True
        else:
          pitches.append(note.pitch[1])
          notes_on_onset.append(note)

  def apply_rest_to_note(self):
    xml_positions = [note.note_duration.xml_position for note in self.notes]
    # concat continuous rests
    previous_rest = self.rests[0]
    new_rests = []
    for rest in self.rests:
      previous_end = previous_rest.note_duration.xml_position + previous_rest.note_duration.duration
      if previous_rest.voice == rest.voice and \
          previous_end == rest.note_duration.xml_position:
        previous_rest.note_duration.duration += rest.note_duration.duration
      else:
        new_rests.append(rest)
        previous_rest = rest

    self.rests = new_rests

    for rest in self.rests:
      rest_position = rest.note_duration.xml_position
      closest_note_index = find_le_idx(xml_positions, rest_position)
      # TODO: what if closest_note_index == None?
      search_index = 1
      while closest_note_index - search_index >= 0:
        prev_note = self.notes[closest_note_index - search_index]
        prev_note_end = prev_note.note_duration.xml_position + prev_note.note_duration.duration
        if prev_note_end == rest_position and prev_note.voice == rest.voice:
          prev_note.following_rest_duration = rest.note_duration.duration
          break
        search_index += 1

  def omit_trill_notes(self):
    def apply_wavy_lines(xml_notes, wavy_lines):
      xml_positions = [x.note_duration.xml_position for x in xml_notes]
      num_notes = len(xml_notes)
      omit_indices = []
      for wavy in wavy_lines:
        index = find_le_idx(xml_positions, wavy.xml_position)
        # TODO: what if closest_note_index == None?
        while abs(xml_notes[index].pitch[1] - wavy.pitch[1]) > 3 and index > 0 \
            and xml_notes[index - 1].note_duration.xml_position == xml_notes[
          index].note_duration.xml_position:
          index -= 1
        note = xml_notes[index]
        wavy_duration = wavy.end_xml_position - wavy.xml_position
        note.note_duration.duration = wavy_duration
        trill_pitch = note.pitch[1]
        next_idx = index + 1
        while next_idx < num_notes and xml_notes[next_idx].note_duration.xml_position < wavy.end_xml_position:
          if xml_notes[next_idx].pitch[1] == trill_pitch:
            omit_indices.append(next_idx)
          next_idx += 1

      omit_indices.sort()
      if len(omit_indices) > 0:
        for idx in reversed(omit_indices):
          del xml_notes[idx]

    def combine_wavy_lines(wavy_lines):
      num_wavy = len(wavy_lines)
      for i in reversed(range(num_wavy)):
        wavy = wavy_lines[i]
        if wavy.type == 'stop':
          for j in range(1, i + 1):
            prev_wavy = wavy_lines[i - j]
            if prev_wavy.type == 'start' and prev_wavy.number == wavy.number:
              prev_wavy.end_xml_position = wavy.xml_position
              wavy_lines.remove(wavy)
              break
      return wavy_lines

    num_notes = len(self.notes)
    omit_index = []
    trill_sign = []
    wavy_lines = []
    for i in range(num_notes):
      note = self.notes[i]
      if not note.is_print_object:
        omit_index.append(i)
        if note.note_notations.is_trill:
          trill = {'xml_pos': note.note_duration.xml_position, 'pitch': note.pitch[1]}
          trill_sign.append(trill)
      if note.note_notations.wavy_line:
        wavy_line = note.note_notations.wavy_line
        wavy_line.xml_position = note.note_duration.xml_position
        wavy_line.pitch = note.pitch
        wavy_lines.append(wavy_line)

    wavy_lines = combine_wavy_lines(wavy_lines)

    for index in reversed(omit_index):
      note = self.notes[index]
      self.notes.remove(note)

    if len(trill_sign) > 0:
      for trill in trill_sign:
        for note in self.notes:
          if note.note_duration.xml_position == trill['xml_pos'] and abs(note.pitch[1] - trill['pitch']) < 4 \
             and not note.note_duration.is_grace_note:
            note.note_notations.is_trill = True
            break

    apply_wavy_lines(self.notes, wavy_lines)

  def rearrange_chord_index(self):
    previous_position = [-1]
    max_chord_index = [0]
    for note in self.notes:
      voice = note.voice - 1
      while voice >= len(previous_position):
        previous_position.append(-1)
        max_chord_index.append(0)
      if note.note_duration.is_grace_note:
        continue
      if note.staff == 1:
        if note.note_duration.xml_position > previous_position[voice]:
          previous_position[voice] = note.note_duration.xml_position
          max_chord_index[voice] = note.chord_index
          note.chord_index = 0
        else:
          note.chord_index = (max_chord_index[voice] - note.chord_index)
      else:  # note staff == 2
        pass
