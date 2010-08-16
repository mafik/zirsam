# -*- coding: utf-8 -*-

import zirsam.common

DEBUG = False
def debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

"""
Match:
    {pa re ci} into <PA ...>
NoFill:
    {} into <PA ...>
NoMatch:
    {fu} info <PA ...>
"""
#Logic values
class LogicValue: #XXX bad name, pick a better one
    def __repr__(self): return self.n
    def __init__(self, n, b): self.n, self.b = n, b
    def __bool__(self): return self.b
    def __or__(self, other): return bool(self) | bool(other)
    def __ror__(self, other): return bool(self) | bool(other)
    def __and__(self, other): return bool(self) & bool(other)
    def __rand__(self, other): return bool(self) & bool(other)
    def __xor__(self, other): return bool(self) ^ bool(other)
    def __rxor__(self, other): return bool(self) ^ bool(other)
Match = LogicValue('Match', True)
NoMatch = LogicValue('NoMatch', False)
NoTake = LogicValue('NoTake', True) #A relative of NoFill? This is for Optional



BNF = None    #This must be set later on; it is used by Rule

class BnfObjectBase:
    #All bnf items will need these methods
    def __add__(self, other): #sepearted by whitespace
        return Concat(self, other)

    def __pow__(self, other): #...
        #if other != "REPEAT":
        # raise Exception("Please multiply by string 'REPEAT'")
        return Repeat(self)

    def __mul__(self, other): #&
        return AndOr(self, other)

    def __lshift__(self, other): #|
        return XOr(self, other)

    #Until I can figure out which way it's actually supposed to be!
    __sub__ = __mul__
    __truediv__ = __add__
    def match(self, tracker):
        #A debug-hookie thing.
        ret = self.test(tracker)
        #tracker.config.debug
        _self = '{0}'.format(self)
        try:
            v = tracker.valsi[tracker.current_valsi]
        except: v = ''
        #debug(' '*(tracker.depth-1),v ,':', "{0} --> {1}".format(_self, ret), sep='')
        debug(' '*(tracker.depth-1), "{0} --> {1}".format(_self, ret), sep='')
        return ret


class Term(BnfObjectBase):
    def __hash__(self):
        return hash(self.content)
    #def __eq__(self, other):
        #return hash(self) == hash(other)
    def __repr__(self):
        return self.type+'('+str(self.content)+')'
        
    def __init__(self, content):
        self.content = content
        self.type = type(self).__name__





class Terminal(BnfObjectBase):
    def __repr__(self):
        return str(self.selmaho)
    def __init__(self, selmaho):
        self.selmaho = selmaho
        #self.hit_count = 0
    def test(self, tracker):
        #self.hit_count += 1
        #if self.hit_count > 10:
            #raise Exception
        try:
            a = tracker.valsi[tracker.current_valsi] #.type
        except (EOFError, StopIteration) as e:
            #print("EOF :(")
            return NoMatch
        
        if a.type == self.selmaho:
            tracker.accept_terminal()
            tracker.node[self.selmaho.__name__] = a
            return Match
        elif type(self.selmaho) == type and isinstance(a, self.selmaho):
            tracker.accept_terminal()
            tracker.node[self.selmaho.__name__] = a
            return Match
        else:
            return NoMatch

class Rule(BnfObjectBase):
    def __init__(self, rulename):
        BnfObjectBase.__init__(common.FastString(rulename))
    def test(self, tracker):
        debug(' '*tracker.depth, '*', self, '*', sep='')
        #debug("Rule:", "entering", self)
        
        target = BNF[self]
        child_tracker = tracker.append_rule(self)
        result = target.match(child_tracker)
        #if repr(self) == 'selbri_3':
        if result == Match:
            #debug("**** Exiting Rule", self, ": ACCEPT", "with", result, 'from', target)
            tracker.accept_rule()
            tracker.node[self.name] = child_tracker
            #tracker.rules[self.name] = True
            return Match
        else:
            #debug("**** Exiting Rule", self, ": FAILURE")
            child_tracker.fail()
            #tracker.rules[self.name] = False
            return NoMatch

    def __repr__(self):
        return "Rule({0!r})".format(self.name)
    def __str__(self): return self.name
    def __hash__(self):
        return hash(self.name)
    def __eq__(self, other):
        return str(self) == str(other)
    def __init__(self, rule_name):
        self.name = rule_name
        #self.dirty = False


class Condition(BnfObjectBase):
    def __repr__(self):
        r = type(self).__name__+repr(tuple(self.terms))
        return r
    
    def __init__(self, *terms):
        self.terms = terms

    def test(self, tracker):
        raise Exception(NotImplemented)

class OptimizedCondition(Condition):
    def __init__(self, A, B):
        if type(A) == type(self):
            #We can make a little optimization: f(f(a, b), c) --> f(a, f(b, c))
            args = A.terms[0], A.terms[1], B
            A.terms = args[1:]
            B = A
            A = args[0]
        Condition.__init__(self, A, B)


class AndOr(OptimizedCondition):
    def test(self, tracker):
        A = self.terms[0].match(tracker)
        B = self.terms[1].match(tracker)
        if A == Match or B == Match:
            return Match
        else:
            return NoMatch

class XOr(OptimizedCondition): #Bad name, it belies its' true function, should be "Alternation" TODO, tho shortness is nice.
    #def __repr__(self):
        #return " {0}\n    |{1}".format(*self.terms)
    def test(self, tracker):
        #XXX And for NoTake?
        """
        Okay, so.
        Check A.
        Success?
            Check B.
            Use the MatchTracker of the longest.
        No?
            Check B.
        
        Since both children may match, we'll have to pick our favorite based on valsi matched. If our second child is shorter, we'll have to discard that match data and use the first's. So
        """
        tracker.checkin()
        O_state = tracker.get_state()
        a = self.terms[0].match(tracker)
        if a == Match:
            A_state = tracker.get_state()
            #Got to check B
            tracker.restore_state(O_state)
            b = self.terms[1].match(tracker)
            ##B_state = tracker.get_state() #XXX may rm later
            if b == Match:
                if tracker.current_valsi == A_state[0]:
                    msg = "@@@@@@@@@@@@@@@@@@@@@@@@@\n!!!!AMBIGIOUS GRAMMAR!!!!\n@@@@@@@@@@@@@@@@@@@@@@@@@\ntracker.valsi: {}\nself:{}\ntracker.get_state():{}\n\nContact your grammar provider.".format(tracker.valsi, self, tracker.get_state())
                    import sys, time
                    print(msg, file=sys.stderr)
                    time.sleep(3)
                    raise Exception(msg)
                if A_state[0] > tracker.current_valsi:
                    tracker.restore_state(A_state)
            else:
                tracker.restore_state(A_state)
            tracker.commit()
            return Match
        tracker.checkout()
        tracker.checkin()
        b = self.terms[1].match(tracker)
        
        if b:
            tracker.commit()
            return Match
        tracker.checkout()
        return NoMatch

class Concat(OptimizedCondition):
    def test(self, tracker):
        """
        Used to be, Match NoFill (e.g, "Match NoMatch...") would get 'Match'. But that isn't working with a bit in sumti-6, so it should be NoFill? NO! That doesn't work! Why doesn't that work? It is quite likely that I will need to implement Yet Another LogicValue....
        Okay, let's try this. BIAS. Yes, sir, biased against Repeat.
        Nope, that didn't work either. Bah. Okay, so....
        let's try having a special Repeat. This will involve haxxing up the BNF, sadly.
        
        Okay, so, perhaps then Repeat must require 1 or more matches! Ahhmmmm...
        
        XXX - Delete this stupid talking-to-self when fixed
        """
        a = self.terms[0].match(tracker)
        tracker.checkin()
        if a == NoMatch:
            tracker.checkout() #A
            #print('aww')
            return NoMatch
        b = self.terms[1].match(tracker)
        if b == NoMatch:
            tracker.checkout()
            return b
        #if b == Match:
        tracker.commit()
        return Match
        
        
        
    

class Repeat(Condition):
    def test(self, tracker):
        """
        Return either NoFill or Match.
        If it matches more than once, return Match
        
        """
        term = self.terms[0]
        t1 = term.match(tracker)
        if t1 == Match:
            #We are golden, no matter what
            i = 1
            while term.match(tracker) == Match:
                #Continue matching
                i += 1
                #if i == 100:
                    #raise Exception("A repeat of more than {0} items is ridiculous. (in {1})".format(i, self)) #For debugging
            return Match
        else:
            if t1 == NoTake:
                return Match
            return NoMatch

class Elidable(Condition):
    def test(self, tracker):
        #XXX Maybe I'll have to do some tracking here? This could probably use some testing
        term = self.terms[0]
        v = term.match(tracker)
        return Match
    #def __repr__(self):
        #r = "/%s/" % self.terms
        #return r

class Optional(Condition):
    def test(self, tracker):
        term = self.terms[0]
        ocv = tracker.current_valsi
        tracker.checkin()
        r = term.match(tracker)
        if r:
            tracker.commit()
            return r
        else:
            tracker.checkout()
            
            #if 'A(e)' in str(tracker):
                #import code
                #ic = code.InteractiveConsole(locals())
                #ic.interact()
            return NoTake #XXXXXXXXXX I'm not so sure about killing this one now. :/
    #def __repr__(self):
        #r = "[%s]" % self.terms
        #return r


