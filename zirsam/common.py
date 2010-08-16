# -*- coding: utf-8 -*-

"""
There are several modules with fancy latinesque names. Each handles a
different phase of parsing, and they depend on a module below them.
Each module functions independantly of the one above it

    orthography
            Converts arbitrary alphabets into latin. Then it determines
            the type of the letter. Then it groups the vowels and
            the consonants together.

    morphology
            Creates individual valsi using the BRKWORDS morphology algo

    thaumatology
            Does pre-processing for dendrography; it handles erasures,
            quoting, UI....

    dendrography
            Uses the BNF to create a parse tree, and then sorts it
            out to make it nice and pretty. All of the actual parsing
            happens in bnf/magic_bnf.py .
    
    [As of writing, the modules below aren't implemented]
    
    semasiology
            Re-structures the tree. Changes pro-valsi to original values,
            check that selbri are real words (Actually, maybe
            'is-a-real-selbri' could happen even earlier, when they
            are tokenized?

There are other files:
    config
            Handles command-line arguments, parser settings
    selmaho, tokens
            Creates token objects
"""

import inspect
#from zirsam import config
import zirsam.config
#Contains the Buffer, a class used by every layer of the parser


class Buffer:
    """
    A nice interface for an iterator.
    """
    #TODO: If this class used less methods, the stack would be shorter
    def __repr__(self):
        return "<Buffered {0}>".format(type(self.orig).__name__)
    def __init__(self, iterable, conf=None):
        if conf == None:
            conf = zirsam.config.Configuration()
        if not hasattr(iterable, '__next__'):
            #raise Exception("Wrap in an iterator plz")
            self.orig = iterable
            iterable = iter(iterable)
        else:
            self.orig = iterable
        if conf.full_buffer:
            items = []
            conf.debug("{0} filling buffer".format(self))
            
            try:
                for i in iterable:
                    items.append(i)
            except EOFError:
                pass
            
            conf.debug("{0} got {1}\n--------------".format(self, items))
            self.iterable = iter(items)

        else:
            self.iterable = iterable
        self.buffer = []
        self.EOF = False
        self.config = conf

    def __feed_buffer(self):
        """Add a single item to the buffer"""
        if self.EOF:
            raise EOFError()
        #self.config.debug("Adding an item to {0}".format(self))
        try:
            self.buffer.append(self.iterable.__next__())
        except (EOFError, StopIteration) as error:
            self.config.debug("{0} got exception {1!r}".format(self, error))
            self.EOF = True
        finally:
            if self.EOF:
                raise EOFError()

    def __fill_to(self, index):
        """
        Make sure we have at least index items
        """
        while index + 1 > len(self.buffer):
            self.__feed_buffer()

    def insert(self, index, value):
        """
        Stick a value into the buffer.
        """
        self.config.debug("Inserting {0} into {1}".format(value, index))
        if hasattr(value, 'position'):
            self.config.debug("(Originally located at {0})".format(value.position))
        self.__fill_to(index)
        if index > len(self.buffer):
            raise Exception("Can't insert item {0} at position {1} because "
                            "that is at the end of the file".format(index,
                            value))
        self.buffer.insert(index, value)

    def __iter__(self):
        i = 0
        while 1:
            try:
                yield self[i]
            except EOFError:
                break
            i += 1

    def items(self, num):
        """
        Return a copy of the items
        """
        self.__fill_to(num)
        return self.buffer[:num]

    def __getitem__(self, index):
        assert index >= 0
        self.__fill_to(index)
        return self.buffer[index]

    def pop(self, i=0):
        """
        Remove an item from the buffer. By default, the first item is removed.
        """
        self.__fill_to(i)
        return self.buffer.pop(i)

class Position:
    """
    Stores information on which line/col/index a character is located at
    """
    def __init__(self, _copy=None):
        if _copy:
            self.offset = _copy.offset
            self.col = _copy.col
            self.lin = _copy.lin
        else:
            self.offset = 0 #The byte offset
            self.col = 0
            self.lin = 0
    def __str__(self):
        return "Line {0}, Col {1}".format(self.lin, self.col)
    def __repr__(self):
        return '+{0} {1}'.format(self.lin, self.col)
    def pushline(self):
        """
        Call when encountering a newline.
        """
        self.offset += 1
        self.col = 0
        self.lin += 1
    def pushcol(self):
        """
        Call when reading any non-newline character.
        """
        self.offset += 1
        self.col += 1

def lineno():
    """Returns the current line number in our program. Debug thing."""
    return inspect.currentframe().f_back.f_lineno



class FastString(str):
    """A string that pre-calculates its' hash."""
    def __init__(self, val):
        str.__init__(val)
        self.__value = val
        self.__hash = hash(val)
    def __hash__(self):
        return self.__hash
    def __eq__(self, other):
        return self.__hash == hash(other)



def Stream(conf=None):
    """
    This function will be found in each module that handles a level of parsing.
    Its job is to return a Buffer that will be used by the next client.
    This one doesn't actually do anything though. :P
    (Maybe it could return a stdin buffer? TODO)
    """
    if conf == None:
        conf = config.Configuration()

