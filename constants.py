from fractions import Fraction

class EmbeddingTable():
  def __init__(self):
    self.keywords = []
    self.embed_key = []

  def append(self, embedding_key):
    self.keywords.append(embedding_key.key)
    self.embed_key.append(embedding_key)


class EmbeddingKey():
  def __init__(self, key_name, vec_idx, value):
    self.key = key_name
    self.vector_index = vec_idx
    self.value = value


def dynamic_table():
  embed_table = EmbeddingTable()

  embed_table.append(EmbeddingKey('ppp', 0, -0.9))
  embed_table.append(EmbeddingKey('pp', 0, -0.7))
  embed_table.append(EmbeddingKey('piano', 0, -0.4))
  embed_table.append(EmbeddingKey('p', 0, -0.4))
  embed_table.append(EmbeddingKey('mp', 0, -0.2))
  embed_table.append(EmbeddingKey('mf', 0, 0.2))
  embed_table.append(EmbeddingKey('f', 0, 0.4))
  embed_table.append(EmbeddingKey('forte', 0, 0.4))
  embed_table.append(EmbeddingKey('ff', 0, 0.7))
  embed_table.append(EmbeddingKey('fff', 0, 0.9))

  embed_table.append(EmbeddingKey('più p', 0, -0.5))
  # embed_table.append(EmbeddingKey('più piano', 0, 0.3))
  embed_table.append(EmbeddingKey('più f', 0, 0.5))
  # embed_table.append(EmbeddingKey('più forte', 0, 0.7))
  embed_table.append(EmbeddingKey('più forte possibile', 0, 1))

  embed_table.append(EmbeddingKey('cresc', 1, 0.7))
  # embed_table.append(EmbeddingKey('crescendo', 1, 1))
  embed_table.append(EmbeddingKey('allargando', 1, 0.4))
  embed_table.append(EmbeddingKey('dim', 1, -0.7))
  # embed_table.append(EmbeddingKey('diminuendo', 1, -1))
  embed_table.append(EmbeddingKey('decresc', 1, -0.7))
  # embed_table.append(EmbeddingKey('decrescendo', 1, -1))

  embed_table.append(EmbeddingKey('smorz', 1, -0.4))

  embed_table.append(EmbeddingKey('poco a poco meno f', 1, -0.2))
  embed_table.append(EmbeddingKey('poco cresc', 1, 0.5))
  embed_table.append(EmbeddingKey('molto cresc', 1, 1))

  # TODO: sotto voce, mezza voce

  embed_table.append(EmbeddingKey('fz', 2, 0.3))
  embed_table.append(EmbeddingKey('sf', 2, 0.5))
  embed_table.append(EmbeddingKey('sfz', 2, 0.7))
  embed_table.append(EmbeddingKey('ffz', 2, 0.8))
  embed_table.append(EmbeddingKey('sffz', 2, 0.9))

  embed_table.append(EmbeddingKey('con forza', 3, 0.5))
  embed_table.append(EmbeddingKey('con fuoco', 3, 0.7))
  embed_table.append(EmbeddingKey('con più fuoco possibile', 3, 1))
  embed_table.append(EmbeddingKey('sotto voce', 3, -0.5))
  embed_table.append(EmbeddingKey('mezza voce', 3, -0.3))
  embed_table.append(EmbeddingKey('appassionato', 3, 0.5))

  return embed_table


def tempo_table():
  # [abs tempo, abs_tempo_added, tempo increase or decrease, sudden change]
  embed_table = EmbeddingTable()
  embed_table.append(EmbeddingKey('Freely, with expression', 0, 0.2))
  embed_table.append(EmbeddingKey('lento', 0, -0.9))
  embed_table.append(EmbeddingKey('adagio', 0, -0.7))
  embed_table.append(EmbeddingKey('andante', 0, -0.5))
  embed_table.append(EmbeddingKey('andantino', 0, -0.3))
  embed_table.append(EmbeddingKey('moderato', 0, 0))
  embed_table.append(EmbeddingKey('allegretto', 0, 0.3))
  embed_table.append(EmbeddingKey('allegro', 0, 0.5))
  embed_table.append(EmbeddingKey('vivace', 0, 0.6))
  embed_table.append(EmbeddingKey('presto', 0, 0.8))
  embed_table.append(EmbeddingKey('prestissimo', 0, 9))

  embed_table.append(EmbeddingKey('molto allegro', 0, 0.85))

  embed_table.append(EmbeddingKey('a tempo', 1, 0.05))
  embed_table.append(EmbeddingKey('meno mosso', 1, -0.8))
  embed_table.append(EmbeddingKey('ritenuto', 1, -0.5))
  embed_table.append(EmbeddingKey('animato', 1, 0.5))
  embed_table.append(EmbeddingKey('più animato', 1, 0.6))
  embed_table.append(EmbeddingKey('agitato', 1, 0.4))
  embed_table.append(EmbeddingKey('più mosso', 1, 0.8))
  embed_table.append(EmbeddingKey('stretto', 1, 0.5))
  embed_table.append(EmbeddingKey('appassionato', 1, 0.2))

  embed_table.append(EmbeddingKey('poco ritenuto', 1, -0.3))
  embed_table.append(EmbeddingKey('molto agitato', 1, 0.7))

  embed_table.append(EmbeddingKey('allargando', 2, -0.2))
  embed_table.append(EmbeddingKey('ritardando', 2, -0.5))
  embed_table.append(EmbeddingKey('rit', 2, -0.5))
  embed_table.append(EmbeddingKey('rallentando', 2, -0.5))
  embed_table.append(EmbeddingKey('rall', 2, -0.5))
  embed_table.append(EmbeddingKey('slentando', 2, -0.3))
  embed_table.append(EmbeddingKey('acc', 2, 0.5))
  embed_table.append(EmbeddingKey('accel', 2, 0.5))
  embed_table.append(EmbeddingKey('accelerando', 2, 0.5))
  embed_table.append(EmbeddingKey('smorz', 2, -0.5))

  embed_table.append(EmbeddingKey('poco rall', 2, -0.3))
  embed_table.append(EmbeddingKey('poco rit', 2, -0.3))

  return embed_table


ABS_TEMPOS = \
  ['adagio', 'lento', 'andante', 'andantino', 'moderato', 'allegretto', 'allegro', 'vivace', 'presto',
   'prestissimo', 'maestoso', 'lullaby', 'tempo i', 'Freely, with expression', 'agitato']


REL_TEMPOS = \
  ['animato', 'pesante', 'veloce', 'acc', 'accel', 'rit', 'ritardando', 'accelerando', 'rall', 'rallentando',
   'ritenuto', 'a tempo', 'stretto', 'slentando', 'meno mosso', 'più mosso', 'allargando', 'smorzando', 'appassionato']

TEMPOS = ABS_TEMPOS + REL_TEMPOS

TEMPOS_MERGED_KEY = \
  ['adagio', 'lento', 'andante', 'andantino', 'moderato', 'allegretto', 'allegro', 'vivace',
   'presto', 'prestissimo', 'animato', 'maestoso', 'pesante', 'veloce', 'tempo i', 'lullaby', 'agitato',
   ['acc', 'accel', 'accelerando'], ['rit', 'ritardando', 'rall', 'rallentando'], 'ritenuto',
   'a tempo', 'stretto', 'slentando', 'meno mosso', 'più mosso', 'allargando']

ABS_DYNAMICS = \
  ['ppp', 'pp', 'p', 'piano', 'mp', 'mf', 'f', 'forte', 'ff', 'fff', 'fp']

REL_DYNAMCIS = \
['crescendo', 'diminuendo', 'cresc', 'dim', 'dimin' 'sotto voce',
 'mezza voce', 'sf', 'fz', 'sfz', 'sffz', 'con forza', 'con fuoco', 'smorzando', 'appassionato']

DYNAMICS = ABS_DYNAMICS + REL_DYNAMCIS

DYNAMICS_MERGED_KEY = \
  ['ppp', 'pp', ['p', 'piano'], 'mp', 'mf', ['f', 'forte'], 'ff', 'fff', 'fp', ['crescendo', 'cresc'],
  ['diminuendo', 'dim', 'dimin'], 'sotto voce', 'mezza voce', ['sf', 'fz', 'sfz', 'sffz']]

TYPE_RATIO_MAP = {'maxima': Fraction(8, 1), 'long': Fraction(4, 1),
                  'breve': Fraction(2, 1), 'whole': Fraction(1, 1),
                  'half': Fraction(1, 2), 'quarter': Fraction(1, 4),
                  'eighth': Fraction(1, 8), '16th': Fraction(1, 16),
                  '32nd': Fraction(1, 32), '64th': Fraction(1, 64),
                  '128th': Fraction(1, 128), '256th': Fraction(1, 256),
                  '512th': Fraction(1, 512), '1024th': Fraction(1, 1024)}
