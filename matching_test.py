import xml_data
import matching
import pretty_midi
test_xml = 'ballade/ballade1/musicxml_cleaned.musicxml'
test_perform = 'ballade/ballade1/Ali01.mid'

xml_sequence = xml_data.XmlNoteSequence(test_xml)
perform_pair = matching.PerformPair(xml_sequence, test_perform)