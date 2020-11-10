
def get_reverse(self):
    self.sequence = self.sequence.replace('A', '%%').replace('T', 'A').replace('%%', 'T')
    self.sequence = self.sequence.replace('G', '%%').replace('C', 'G').replace('%%', 'C')
    self.sequence = self.sequence.replace('a', '##').replace('t', 'a').replace('##', 't')
    self.sequence = self.sequence.replace('g', '##').replace('c', 'g').replace('##', 'c')
    self.sequence = self.sequence[::-1]
