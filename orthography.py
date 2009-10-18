#!/usr/bin/python3.0
# -*- coding: utf-8 -*-

"""
orthography.py - Handle the messy, dirty stuff of input.

This file handles the inputting of text, and the classification and grouping of characters.

TODO: unicodedata.normalize

"""
import sys

from common import Buffer
import config

class Position:
  #Stores information on which line/col/index a character is located at
  def __init__(self, _copy=None):
    if _copy:
      self.c = _copy.c
      self.col = _copy.col
      self.lin = _copy.lin
    else:
      self.c = 0
      self.col = 0
      self.lin = 0
  def __str__(self):
    return "Line {0}, Col {1}".format(self.lin, self.col)
  def __repr__(self):
    return '+{0}, {1}'.format(self.lin, self.col)
  def pushline(self):
    self.c += 1
    self.col = 0
    self.lin += 1
  def pushcol(self):
    self.c += 1
    self.col += 1



class Character:
  def clean_val(v):
    #Escapes stuff if neccessary. "\n" -> "\\n"
    return repr(v)[1:-1]
#    if '\\' in repr(v):
#      return repr(v)[1:-1]
#    else:
#      return str(v)
  
  def __str__(self):
    return Character.clean_val(self.value)
  
  def __repr__(self):
    return str(self)
    #return "{0}={1}".format(self, self.value)
    #return "<{0} {1}>".format(self.value, self.position)
  
  
  def __init__(self, c, position, config):
    self.original = c
    assert position != None
    self.position = position
    
    self.accented = False
    self.V = False
    self.C = False
    self.y = False
    self.comma = False
    self.period = False
    self.h = False
    self.whitespace = False
    self.garbage = False
    self.EOF = False
    
    
    if c == '':
      self.EOF = True
      self.value = ''
    elif c in 'AEIOU':
      self.value = c
      self.accented = True
      self.V = True
    elif c in 'aeiou':
      self.value = c
      self.V = True
    elif c in "bcdfgjklmnprstvxz":
      self.value = c.lower()
      self.C = True
    elif c in 'y':
      self.value = 'y'
      self.y = True
    elif c in ',': 
      self.value = ','
      self.comma = True
    elif c in '.':
      self.value = '.'
      self.period = True
    elif c in "'":
      self.value = "'"
      self.h = True
    elif c in ' \t\n\r':
      self.value = c
      self.whitespace = True
    else:
      self.garbage = True
      self.value = c
    



class Bit:
  """Stores a logical sequence of characters"""
  def __len__(self):
    return len(self.chars)
  def __str__(self):
    r = ''
    for c in self.chars:
      r += c.original
    return r
  def __getitem__(self, index):
    return self.chars[index]
  def __repr__(self):
    r = '<'
    for c in self.chars:
      r += str(c)
    r += '>'
    return r
  def __init__(self, fd):
    self.chars = None
    self.value = ''
    
    self.valid_cc = True
    self.valid_initial_cc = True
    
    self.C = False
    self.CC = False
    self.CCC = False
    self.CyC = False
    self.CyCC = False
    self.CCyC = False # XXX - CCyC and CyCC counts as CCC, right?
    
    self.counts_CC = False
    self.has_C = False
    self.accented = False
    
    self.V = False
    self.VV = False
    self.VhV = False
    self.counts_VV = False
    self.has_V = False
    
    self.h = False
    self.y = False
    self.comma = False
    self.period = False
    self.whitespace = False
    self.wordsep = False
    self.garbage = False
    
    first = fd.pop()
    
    if first.C:
      self.has_C = True
      if fd[0].C:
        ###if fd[1].y and fd[2].C: #CCyC
            ###self.CCyC = True
            ###self.counts_CC = True
            ###self.chars = [first, fd.pop(), fd.pop(), fd.pop()]
        ###el
        if fd[1].C: #CCC or CC CC
          if fd[2].C: #CC CC
            self.CC = True
            self.counts_CC = True
            self.chars = [first, fd.pop()]
          else: #CCC V or something
            self.CCC = True
            self.counts_CC = True
            self.chars = [first, fd.pop(), fd.pop()]
        else: #CC
          self.CC = True
          self.counts_CC = True
          self.chars = [first, fd.pop()]
      elif fd[0].y and fd[1].C and not fd[2].y: #CyC
        #if fd[2].C: 
          #self.CyCC = True
          #self.counts_CC = True
          #self.chars = [first, fd.pop(), fd.pop(), fd.pop()]
        #else:
        self.CyC = True
        self.counts_CC = True
        self.chars = [first, fd.pop(), fd.pop()]
      else:
        self.C = True
        self.chars = [first]
    elif first.V:
      self.has_V = True
      if fd[0].V:
        self.VV = True
        self.counts_VV = True
        self.chars = [first, fd.pop()]
        
      elif fd[0].h and fd[1].V:
        self.VhV = True
        self.counts_VV = True
        self.chars = [first, fd.pop(), fd.pop()]
      else:
        self.V = True
        self.chars = [first]
      #Check for accents
      for letter in self.chars:
        if letter.accented:
          self.accented = True
    elif first.whitespace:
      self.whitespace = True
      self.wordsep = True
      self.chars = [first]
      while fd[0].whitespace: # XXX - this makes evevrything unresponsive when inputting text
        self.chars.append(fd.pop())
    elif first.y:
      self.y = True
      self.chars = [first]
      #XXX I don't like this
      #while fd[0].y:
        #self.chars.append(fd.pop())
    elif first.h:
      self.h = True
      self.chars = [first]
    elif first.comma:
      self.comma = True
      self.chars = [first]
    elif first.period:
      self.wordsep = True
      self.period = True
      self.chars = [first]
      while fd[0].period:
        self.chars.append(fd.pop())
    else:
      self.garbage = True
      self.chars = [first]
      while fd[0].garbage:
        self.chars.append(fd.pop())
    
    
    assert self.chars
    self.cc_letter_counts = 0 #How many of this bit's letters count when determining if a CC is within the first 5 letters.
    for char in self.chars:
      self.value += char.value
      if char.V or char.C:
        self.cc_letter_counts += 1
    
    self.position = self.chars[0].position


__VALID_INIT_CC = "bl br cf ck cl cm cn cp cr ct dj dr dz fl fr gl gr jb jd jg jm jv kl kr ml mr pl pr sf sk sl sm sn sp sr st tc tr ts vl vr xl xr zb zd zg zm zv".split(' ')
def valid_init_cc(bit):
  if type(bit) == list:
    assert len(bit) == 2
    assert all(type(x) == str for x in bit)
    return (bit[0]+bit[1]) in __VALID_INIT_CC
  if len(bit.chars) == 4: #CCyC or CyCC
    l, x, z, n = bit.chars
    if x.value == 'y':
      return (z.value+n.value) in __VALID_INIT_CC
    elif z.value == 'y':
      return (l.value+x.value) in __VALID_INIT_CC
    else:
      raise Exception("Miscall with " + str(bit))
    
  elif len(bit.chars) == 3:
    l, m, n = bit.chars
    if l.C and m.y and n.C:
      return True
    elif (l.value+m.value) in __VALID_INIT_CC and (m.value+n.value) in __VALID_INIT_CC:
      return True
    return False
  elif len(bit.chars) == 2:
    m, n = bit.chars
    m, n = m.value, n.value
    v = m+n
    return v in __VALID_INIT_CC
  raise Exception("Miscall with " + str(bit))

class __NiceStdin:
  #Use the input() function to get data; this allows editing of text
  def __init__(self):
    self.chars = ''
  def read(self, i=1):
    if len(self.chars) == 0:
      if 1: #not self.EOF or 1:
        try:
          l = input() #like python2.x's raw_input()
          l += '\n' #input() strips the newline
        except EOFError:
          l = ''
        self.chars += l
      else:
        return ''
    x = self.chars[:i]
    self.chars = self.chars[i:]
    return x
    

def stream_char(fd, config):
  #XXX TODO: Use EncodingTable
  p = Position()

  while 1:
    #c = fd.read(1)
    #This is where we do that GlyphTable stuff
    c = config.glyph_table.get_char(fd, p)
    #assert c.lower() in "bcdfgjklmnprstvxz \n ',. aeiouy"

    if c in '':
      yield Character('\n', Position(p), config) # haXXX, if morphology doesn't get a whitespace at the end it doesn't give up the last token
      yield Character('', Position(p), config)
      break
    else:
      for _c in c:
        yield Character(_c, Position(p), config)

def stream_bit(fd):
  while 1:
    if fd.EOF:
      break
    yield Bit(fd)

def Stream(conf=None, stdin=None):
  if conf == None:
    conf = config.Configuration()
  if stdin == None:
    stdin = sys.stdin
  
  if stdin.isatty() and conf.permit_readline: #Should we enable GNU readline?
    try:
      import readline
      #If this succeeds, then it is enabled for the input() function
      stdin = __NiceStdin()
    except ImportError:
      pass
  charbuf = Buffer(stream_char(stdin, conf), conf)
  bitbuf = Buffer(stream_bit(charbuf), conf)
  return bitbuf

if __name__ == '__main__':
  print("Shows how the clusters of letters are viewed internally to the parser.", file=sys.stderr)
  bitbuf = Stream()
  i = []
  for bit in bitbuf:
    i.append(bit)
    print(bit.position, ": ", repr(bit), sep='')
  print()
