from bisect import bisect_right


def find_le_idx(alist, item):
  """Find index of rightmost value  less than or equal to x"""
  i = bisect_right(alist, item)
  if i:
    return i-1
  return None


def extract_directions_by_keywords(directions, keywords):
  return [el for el in directions if check_direction_by_keywords(el, keywords)]


def check_direction_by_keywords(dir, keywords):
  def _standardize(word):
    return word.replace(',', '').replace('.', '').lower()

  if dir.type['type'] in keywords:
    return True
  elif dir.type['type'] == 'words':
    if _standardize(dir.type['content']) in keywords:
      return True
    else:
      word_split = _standardize(dir.type['content']).split(' ')
      for w in word_split:
        if w in keywords:
          # dir.type[keywords[0]] = dir.type.pop('words')
          # dir.type[keywords[0]] = w
          return True

    for key in keywords:  # words like 'sempre più mosso'
      if len(key) > 2 and key in dir.type['content']:
        return True


def find_index_list_of_list(element, in_list):
  # isuni = isinstance(element, unicode) # for python 2.7
  if element in in_list:
    return in_list.index(element)
  else:
    for li in in_list:
      if isinstance(li, list):
        # if isuni:
        #     li = [x.decode('utf-8') for x in li]
        if element in li:
          return in_list.index(li)

  return None


def direction_words_flatten(note_attribute):
  flatten_words = note_attribute.absolute
  if not note_attribute.relative == []:
    for rel in note_attribute.relative:
      if rel.type['type'] == 'words':
        flatten_words = flatten_words + ' ' + rel.type['content']
      else:
        flatten_words = flatten_words + ' ' + rel.type['type']
  return flatten_words