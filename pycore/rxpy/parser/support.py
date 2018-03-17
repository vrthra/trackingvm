
# The contents of this file are subject to the Mozilla Public License
# (MPL) Version 1.1 (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License
# at http://www.mozilla.org/MPL/                                      
#                                                                     
# Software distributed under the License is distributed on an "AS IS" 
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See 
# the License for the specific language governing rights and          
# limitations under the License.                                      
#                                                                     
# The Original Code is RXPY (http://www.acooke.org/rxpy)              
# The Initial Developer of the Original Code is Andrew Cooke.         
# Portions created by the Initial Developer are Copyright (C) 2010
# Andrew Cooke (andrew@acooke.org). All Rights Reserved.               
#                                                                      
# Alternatively, the contents of this file may be used under the terms 
# of the LGPL license (the GNU Lesser General Public License,          
# http://www.gnu.org/licenses/lgpl.html), in which case the provisions 
# of the LGPL License are applicable instead of those above.           
#                                                                      
# If you wish to allow use of your version of this file only under the 
# terms of the LGPL License and not to allow others to use your version
# of this file under the MPL, indicate your decision by deleting the   
# provisions above and replace them with the notice and other provisions
# required by the LGPL License.  If you do not delete the provisions    
# above, a recipient may use your version of this file under either the 
# MPL or the LGPL License.               

'''
Support classes for parsing.
'''                               


ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ascii_letters = ascii_lowercase + ascii_uppercase
digits = '0123456789'
from rxpy.alphabet.ascii import Ascii
from rxpy.alphabet.unicode import Unicode
from rxpy.graph.post import resolve_group_names, post_process
from rxpy.parser.error import SimpleGroupException
from rxpy.lib import _FLAGS, RxpyException, refuse_flags


OCTAL = '01234567'
ALPHANUMERIC = digits + ascii_letters


class ParserState(object):
    '''
    Encapsulate state needed by the parser.  This includes information 
    about flags (which may change during processing and is related to 
    alphabets) and groups.
    '''
    
    (I, M, S, U, X, A, _L, _C, _E, _U, _G, IGNORECASE, MULTILINE, DOTALL, UNICODE, VERBOSE, ASCII, _LOOP_UNROLL, _CHARS, _EMPTY, _UNSAFE, _GROUPS) = _FLAGS
    
    def __init__(self, flags=0, alphabet=None, hint_alphabet=None,
                 require=0, refuse=0):
        '''
        `flags` - initial flags set by user (bits as int)
        
        `alphabet` - optional alphabet (if given, checked against flags; if not
        given inferred from flags and hint) 
        
        `hint_alphabet` - used to help auto-detect ASCII and Unicode in 2.6
        
        `require` - fkags required by the alphabet
        
        `refuse` - flags refused by the alphabet
        '''
        
        self.__new_flags = 0
        self.__initial_alphabet = alphabet
        self.__hint_alphabet = hint_alphabet
        self.__require = require
        self.__refuse = refuse
        
        flags = flags | require
        # default, if nothing specified, is unicode
        if alphabet is None and not (flags & (ParserState.ASCII | ParserState.UNICODE)):
            alphabet = hint_alphabet if hint_alphabet else Unicode()
        # else, if alphabet given, set flag
        elif alphabet:
            if isinstance(alphabet, Ascii): flags |= ParserState.ASCII
            elif isinstance(alphabet, Unicode): flags |= ParserState.UNICODE
            elif flags & (ParserState.ASCII | ParserState.UNICODE):
                raise RxpyException('The alphabet is inconsistent with the parser flags')
        # if alphabet missing, set from flag
        else:
            if flags & ParserState.ASCII: alphabet = Ascii()
            if flags & ParserState.UNICODE: alphabet = Unicode()
        # check contradictions
        if (flags & ParserState.ASCII) and (flags & ParserState.UNICODE):
            raise RxpyException('Cannot specify Unicode and ASCII together')
        refuse_flags(flags & refuse)
        
        self.__alphabet = alphabet
        self.__flags = flags
        self.groups = GroupState()
        self.__comment = False  # used to track comments with extended syntax
        self.__unwind_credit = 10
        
    def deep_eq(self, other):
        '''
        Used only for testing.
        '''
        def eq(a, b):
            return a == b == None or (a and b and type(a) == type(b))
        return self.__new_flags == other.__new_flags and \
            eq(self.__initial_alphabet, other.__initial_alphabet) and \
            eq(self.__hint_alphabet, other.__hint_alphabet) and \
            self.__require == other.__require and \
            self.__refuse == other.__refuse and \
            eq(self.__alphabet, other.__alphabet) and \
            self.__flags == other.__flags and \
            self.groups == other.groups and \
            self.__comment == other.__comment and \
            self.__unwind_credit == other.__unwind_credit
        
    @property
    def has_new_flags(self):
        '''
        Have flags change during parsing (possible when flags are embedded in
        the regular expression)?
        '''
        return bool(self.__new_flags & ~self.__flags)
    
    def clone_with_new_flags(self):
        '''
        This discards group information because the expression will be parsed
        again with new flags.
        '''
        return ParserState(alphabet=self.__initial_alphabet, 
                           flags=self.__flags | self.__new_flags, 
                           hint_alphabet=self.__hint_alphabet,
                           require=self.__require, refuse=self.__refuse)
        
    def next_group_index(self, name=None):
        '''
        Get the index number for the next group, possibly associating it with
        a name.
        '''
        return self.groups.new_index(name, self.flags & self._GROUPS)
    
    def index_for_name_or_count(self, name):
        '''
        Given a group name or index (as text), return the group index (as int).
        First, we parse as an integer, then we try as a name.
        '''
        return self.groups.index_for_name_or_count(name)
        
    def new_flag(self, flag):
        '''
        Add a new flag (called by the parser for embedded flags).
        '''
        self.__new_flags |= flag
        
    def significant(self, character):
        '''
        Returns false if character should be ignored (extended syntax). 
        '''
        if self.__flags & self.VERBOSE:
            if character == '#':
                self.__comment = True
                return False
            elif self.__comment:
                self.__comment = character != '\n'
                return False
            elif self.__alphabet.space(character):
                return False
            else:
                return True
        else:
            return True
        
    def unwind(self, count):
        '''
        Allow limited unwinding of loops.  This is to limit unwinding in case
        of nested repeats.  Unfortunately, because the parser is L to R, it 
        will be applied to the outer loop (although this is not for direct 
        speed as much as letting the simple engine work, so that may not be
        a serious issue). 
        '''
        if count <= self.__unwind_credit:
            self.__unwind_credit -= count
            return True
        else:
            return False
        
    @property
    def alphabet(self):
        '''
        The alphabet to be used.
        '''
        return self.__alphabet
    
    @property
    def flags(self):
        '''
        Current flags (this does not change as new flags are added; instead
        the entire expression must be reparsed if `has_new_flags` is True.
        '''
        return self.__flags
    
    
class GroupState(object):
    
    def __init__(self):
        self.__name_to_index = {}
        self.__index_to_name = {}
        
    def index_for_name_or_count(self, name):
        '''
        Given a group name or index (as text), return the group index (as int).
        First, we parse as an integer, then we try as a name.
        '''
        try:
            index = int(name)
            if index not in self.__index_to_name:
                raise RxpyException('Unknown index ' + str(name))
            else:
                return index
        except ValueError:
            if name not in self.__name_to_index:
                raise RxpyException('Unknown name ' + str(name))
            else:
                return self.__name_to_index[name]
            
    def new_index(self, name=None, extended=False):
        
        def next_index():
            index = 1
            while index in self.__index_to_name:
                index += 1
            return index
        
        if extended:
            # allow aliasing and numbers as names
            if not name:
                name = str(next_index())
            index = None
            try:
                index = self.index_for_name_or_count(name)
            except RxpyException:
                try:
                    index = int(name)
                except ValueError:
                    index = next_index()
            else:
                return index
        else:
            # names are not numbers and cannot repeat
            index = next_index()
            if name:
                try:
                    int(name)
                    raise SimpleGroupException('Invalid group name ' + name)
                except ValueError:
                    if name in self.__name_to_index:
                        raise SimpleGroupException('Repeated group name ' + name)
            else:
                name = str(index)
                
        self.__index_to_name[index] = name
        self.__name_to_index[name] = index
        return index
    
    def __eq__(self, other):
        return isinstance(other, GroupState) and \
            self.__index_to_name == other.__index_to_name
            
    @property
    def count(self):
        return len(self.__index_to_name)
    
    @property
    def names(self):
        '''
        Map from group names to index.  Warning - for efficiency, exposed raw.
        '''
        return self.__name_to_index
    
    @property
    def indices(self):
        '''
        Map from group index to name.  Warning - for efficiency, exposed raw.
        '''
        return self.__index_to_name
        
        
class Builder(object):
    '''
    Base class for states in the parser (called Builder rather than State
    to avoid confusion with the parser state).
    
    The parser can be though of as a state machine, implemented via a separate 
    loop (`parse()`) that repeatedly calls `.append_character()` on the current
    state, using whatever is returned as the next state.
    
    The graph is assembled within the states, which either assemble locally 
    or extend the state in a "parent" state (so states may reference parent
    states, but the evaluation process remains just a single level deep).
    
    It is also possible for one state to delegate to the append_character
    method of another state (escapes are handled in this way, for example).
    
    After all characters have been parsed, `None` is used as a final character
    to flush any state that is waiting for lookahead.
    '''
    
    def __init__(self, state):
        self._state = state
    
    def append_character(self, character, escaped=False):
        '''
        Accept the given character, returning a new builder.  A value of
        None is passed at the end of the input, allowing cleanup.
        
        If escaped is true then the value is always treated as a literal.
        '''

        
def parse(text, state, class_, mutable_flags=True):
    '''
    Parse the text using the given builder.
    
    If the expression sets flags then it is parsed again.  If it changes flags
    on the second parse then an error is raised.
    '''
    try:
        graph = class_(state).parse(text)
    except RxpyException:
        # suppress error if we will parse again
        if not (mutable_flags and state.has_new_flags):
            raise
    if mutable_flags and state.has_new_flags:
        state = state.clone_with_new_flags()
        graph = class_(state).parse(text)
    graph = post_process(graph, resolve_group_names(state))
    if state.has_new_flags:
        raise RxpyException('Inconsistent flags')
    return (state, graph)


