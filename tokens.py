# -*- coding: utf-8 -*-

#Different kinds of tokens


from selmaho import *

class Token:
  #The items below are a hack for dealing with morphology. With these values, nobody will try to re-tokenize it.
  wordsep = True
  h = False
  y = False
  counts_CC = False

  def __repr__(self):
    r = type(self).__name__+'('
    for i in self.bits:
      r += repr(i)
    return r+repr(self.bits[0].position)+')'

  def __str__(self):
    #r = ''
    #for b in self.bits:
      #r += str(b)
    return "{0}({1})".format(type(self).__name__, self.value)

  def calculate_value(self):
    """
    Return the ascii value of the token
    """
    #Assemble a string out of the values of every bit
    v = ''
    for bit in self.bits:
      v += bit.value
    #Check for irregular stress. If the stress is regular, then we can do str.lower()
    #We want penultimate stress.
    stressed_regularly = ...
    i = len(self.bits)
    encountered_vowels = 0
    while i >= 0:
      i -= 1
      if self.bits[i].has_V:
        encountered_vowels += 1
      if self.bits[i].accented and encountered_vowels != 2:
        stressed_regularly = False

    if stressed_regularly:
      return v.lower() #Eliminates unecessary accents
    return v #Keep the given accents

  def __init__(self, bits, config):
    self.bits = bits
    if not len(bits):
      config.error("Trying to tokenize nothing!")
    self.position = self.bits[0].position
    self.value = self.calculate_value()
    if isinstance(self, CMAVO):
      #All cmavo should have a value
      self.type = SELMAHO[self.value]
    else:
      self.type = type(self)


class VALSI(Token): pass

class CMENE(VALSI): pass
class CMAVO(VALSI): pass
class SELBRI(VALSI): pass
#class GISMU(SELBRI): pass
#class LUJVO(SELBRI): pass
#class FUHIVLA(SELBRI): pass

class boring(Token): pass #Ignore
class WHITESPACE(boring): pass
class HESITATION(boring): pass


class extra(Token): pass
class GARBAGE(extra): pass
class PERIOD(extra, boring): pass