#!/usr/bin/python3.0
# -*- coding: utf-8 -*-

import sys
#sys.setrecursionlimit(2000)
sys.setrecursionlimit(1000) #The default on my system
import io

from config import Configuration
from common import Buffer
import thaumatology
from bnf import BNF
import magic_bnf


def pprint(wut, first=True, html=False):
  """More complex than the one below.
  We can output in a few different ways:
    * Print the entire parse tree, including sub-rules like "sumti_6"
    * Don't print sub-rules, but print everything
    * Print only nodes that don't have 2 branches"""
  
  if isinstance(wut, MatchTracker):
    head = str(wut.rule)
    
    #wut.config._debug = False
    if head[-1] in '1234567890' and not (wut.config._debug or wut.config.full_tree):
      #It is part of a big rule
      head = ''
      for v in wut.value:
        head += pprint(v, first=False, html=html)
      while '  \n' in head:
        head = head.replace('  \n', ' \n')
      head = head.replace(' \n', '')
      return head+''
    if not html: head += ':'
    else: head = """<span class="rule {0}" title="{0}">""".format(str(wut.rule), head)
    for v in wut.value:
      for line in pprint(v, first=False, html=html).split('\n'):
        head += '\n  '+line
    head += '\n'
    if html:
      head += "</span>"
    if first:
      while ' \n' in head: head = head.replace(' \n', '\n')
      while '\n\n' in head: head = head.replace('\n\n', '\n')
      if html:
        head = """<span class="rule {0}" title="{0}">{1}</span>""".format(str(wut.rule), head)
        #head += "</span>"
      return head.strip()
    return head
  if html:
    return wut.html()+'\n'
  return str(wut)+'\n'

class MatchTracker:
  """
  A node in the parse tree. Each node coresponds to a rule. Each node keeps a list of accepted valsi and sub-nodes
  """
  def __str__(self):
    return pprint(self)
  def __repr__(self):
    #if str(self.rule)[-1] in '1234567890' and self.accepted:
    #if not self.config._debug and (len(self.value) == 1 and type(self.value[0]) == MatchTracker):
    #if not self.config._debug and (len(self.value) == 1 and type(self.value[0]) == MatchTracker):
    #  return repr(self.value)[1:-1]
    r = str(self.rule)+':{'+repr(self.value)[1:-1]+'}'+"*"*(not self.accepted) #XXX That self.accepted isn't always the same is probably indicative of a horrifying bug
    #if self.stack:
    #  r += '<'+str(self.stack)[1:-1]+'>'
    return r
  def html(self):
    return pprint(self, html=True)
  def text(self, first=True):
    #Return a string of the valsi values
    r = ''
    for child in self.value:
      if isinstance(child, MatchTracker):
        r += child.text(first=False)
      else:
        r += ' '+child.value
    if first:
      r = r.strip()
    return r
  def search(self, rule_name, first=True, stops=("text", "sentence")):
    #iter over every node in tracker, returning nodes who's rule is rule_name
    #It does not look inside of matches for more matches
    #It does not search inside of rules mentioned in stops.
    if self.rule.name == rule_name:
      yield self
    elif not first and (self.rule.name in stops):
      print("Stopping at", self.rule.name)
      return
    else:
      for val in self.value:
        if isinstance(val, MatchTracker):
          for _ in val.search(rule_name, first=False, stops=stops):
            yield _
  def pull(self, *dive_list):
    #nodes is a list of nodes to dive through, tries to descend through the tree to get it.
    #More of a pain in the ass to use, however, it is more trustworthy than search().
    # TODO: Could be implemented as a while loop?
    if dive_list:
      val = dive_list[0]
      child = self.node.get(val)
      if child:
        return child.pull(*dive_list[1:])
    else: #You called?
      return self #Ta da! :D
  def __init__(self, valsi, rule, conf=None, current_valsi=0, parent=None, depth=0):
    assert conf
    self.config = conf
    self.value = []
    self.valsi = valsi
    self.start = current_valsi
    self.current_valsi = self.start
    self.parent = parent
    self.depth = depth # TODO: Might I wish to abort at some depth?
    self.rule = rule
    self.accepted = False
    self.stack = [] #For inner-rule grammarstuffins
    self.used_rules = []
    self.node = {} # XXX TODO: Give better name.
    self.child_rules = {}
  def accept_terminal(self):
    #print("adding terminal", self.valsi[self.current_valsi])
    self.value.append(self.valsi[self.current_valsi])
    self.current_valsi += 1
  def append_rule(self, rule):
    child = MatchTracker(self.valsi, rule, current_valsi=self.current_valsi, parent=self, depth=self.depth+1, conf=self.config)
    self.value.append(child)
    return child
  def accept_rule(self):
    assert self.value
    self.accepted = True
    self.current_valsi = self.value[-1].current_valsi  #+ 1
    self.used_rules.append(self.rule.name)
    if self.parent:
      self.parent.child_rules[self.rule.name] = self.value[-1]
    #self.config.debug('ACCEPT', self)
  def fail(self):
    #A rule failed
    if self.parent:
      #if self.value:
      #self.config.debug("@@@ FAILING", self)
      self.parent.value.pop(self.parent.value.index(self))
      for rule in self.used_rules:
        if rule in self.parent.child_rules:
          del self.parent.child_rules[rule]
      #self.parent.value.pop(self.start)
    else:
      raise Exception("Tried to fail root node")
  def finalize(self):
    #Remove those valsi
    i = self.current_valsi
    #print(i)
    while i > 0:
      v = self.valsi.pop()
      #print("Losing", v)
      i -= 1
    return
  def checkin(self):
    """
    Append the current state onto a stack. This is for a rule's structure.
    """
    #self.config.debug("checkin")
    self.stack.append((self.current_valsi, list(self.value)))
    if self.config.show_progress:
      self.config.message("Parser location:", self.current_valsi, end='\r')
    #self.config.debug('---', self.stack[-1])
  def checkout(self):
    """
    Something failed. Restore an old state from the stack
    """
    #self.config.debug("popping", self.stack)
    old_valsi_state = self.stack.pop()
    (self.current_valsi, self.value ) = old_valsi_state
  def commit(self):
    """
    Something succeeded. Remove from stack
    """
    #print("commit")
    self.stack.pop()
  def get_state(self):
    """For exploring the length of branches in bnf.magic_bnf.XOr. Important to note is the fact that the first item in the tuple is the current_valsi"""
    return self.current_valsi, list(self.value), self.accepted, list(self.stack)
  def restore_state(self, state):
    self.current_valsi, self.value, self.accepted, self.stack = state

'''
      def get_state(self):
    """For exploring the length of branches in bnf.magic_bnf.XOr. Important to note is the fact that the first item in the tuple is the current_valsi"""
    
    if self.parent:
      papa = self.parent.get_state()
    else: papa = None
    #return self.current_valsi, self.value, self.accepted, self.stack, papa
    return self.current_valsi, self.accepted, self.stack, papa
  def restore_state(self, state):
    #self.current_valsi, self.value, self.accepted, self.stack, papa = state
    self.current_valsi, self.accepted, self.stack, papa = state
    if self.parent:
      self.parent.restore_state(papa)'''

class GrammarParser:
  def __init__(self, token_iter, config):
    self.valsi = token_iter
    self.config = config
    self.good_parse = False

  def __iter__(self):
    #yield ROOT_TOKENs
    root_rule = magic_bnf.Rule(self.config.parsing_unit)
    root_value = BNF[root_rule]
    while 1:
      
      tracker = MatchTracker(self.valsi, root_rule, conf=self.config)
      try:
        v = root_value.match(tracker)
      except (EOFError, StopIteration) as e:
        input("EXCEPTION: Hit the end (press enter)")
        raise e
      
      tracker.finalize()
      if v:
        tracker.accept_rule()
      else:
        break
      
      if tracker.current_valsi == 0:
        #Pretty much fail. Try, uh, try getting rid of that token maybe there's something good behind it
        try:
          dacheated = self.valsi.pop(0)
          self.config.warn("Unable to parse anything, dropping this token", dacheated.position)
        except (EOFError, StopIteration):
          break
        continue
      
      yield tracker
      
      try:
        self.valsi[0]
      except (EOFError, StopIteration):
        self.good_parse = True
        break
      #break #XXX Only do one for now



def parse(string):
  main(Stream(Configuration(stdin=io.StringIO(string))))

def Stream(conf=None):
  if conf == None:
    conf = Configuration()
  de_debug = conf._debug
  conf._debug = False
  valsibuff = thaumatology.Stream(conf)
  treebuff = GrammarParser(valsibuff, conf)
  conf._debug = de_debug
  return Buffer(treebuff, conf)

def main(_stream):
  #Returns, Was_A_Satisfactory_Parse, Parsed_Texts
  r = []
  #r = 
  #print('='*70)
  for i in _stream:
    #print('*************************\n', pprint(i), '\n-------------------------')
    if not _stream.config.html:
      print()
      print(pprint(i))
    r.append(i)
    #print(i)
  if _stream.config.html:
    print("Converting to html...", file=sys.stderr)
    print("""<html>
<style>
.brivla {
color: red;
}
.cmavo {
color: blue;
}
.sumti {
border-bottom-width: 1px;
border-bottom-style: solid;
border-color: black;
}
.sumti .sumti { border-color: gray; }
.sumti .sumti .sumti { border-color: red; }
.sumti .sumti .sumti .sumti { border-color: orange; }
.sumti .sumti .sumti .sumti .sumti { border-color: yellow; }
.sumti .sumti .sumti .sumti .sumti .sumti { border-color: green; }
.sumti .sumti .sumti .sumti .sumti .sumti .sumti { border-color: blue; }
.sumti .sumti .sumti .sumti .sumti  .sumti .sumti .sumti { border-color: purple; }
.rule {
/*border-style-left:solid;
border-width-left:1px;
margin-left: 2px;
padding-left: 1px;*/
}
</style>
<body>""")
    for i in r:
      print("""<div class="text">""")
      print(pprint(i, html=True))
      print("""</div>""")
    print("""</body></html>""")
  else:
    if not r:
      print(r, '(empty)')
  return _stream.orig.good_parse and len(r) == 1, r


if __name__ == '__main__':
  val, r = main(Stream())
  #print('--->', val)
  raise SystemExit(not val)
  #if r:
    #return True
