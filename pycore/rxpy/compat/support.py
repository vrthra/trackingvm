
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

ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
ascii_letters = ascii_lowercase + ascii_uppercase
digits = '0123456789'

from rxpy.alphabet.ascii import Ascii
from rxpy.alphabet.unicode import Unicode
from rxpy.parser.pattern import parse_pattern, parse_groups
from rxpy.compat.replace import compile_repl
from rxpy.lib import RxpyException


_ALPHANUMERICS = ascii_letters + digits


def compile(pattern, flags=None, alphabet=None, engine=None):
    require_engine(engine)
    if isinstance(pattern, RegexObject):
        if flags is not None and flags != pattern.flags:
            raise ValueError('Changed flags')
        if alphabet is not None and alphabet != pattern.alphabet:
            raise ValueError('Changed alphabet')
    else:
        if flags is None:
            flags = 0
        if isinstance(pattern, str):
            hint_alphabet = Ascii()
        elif isinstance(pattern, unicode):
            hint_alphabet = Unicode()
        else:
            hint_alphabet = None
        pattern = RegexObject(parse_pattern(pattern, engine, flags=flags, 
                                            alphabet=alphabet, 
                                            hint_alphabet=hint_alphabet),
                              pattern, engine=engine)
    return pattern


class RegexObject(object):
    
    def __init__(self, parsed, pattern=None, engine=None):
        require_engine(engine)
        self.__parsed = parsed
        self.__pattern = pattern
        self.__engine = engine
        
    def deep_eq(self, other):
        '''
        Used only for testing.
        '''
        return self.__parsed[0].deep_eq(other.__parsed[0]) and \
            self.__parsed[1].deep_eq(other.__parsed[1]) and \
            self.__pattern == other.__pattern and \
            self.__engine == other.__engine
        
    @property
    def __parser_state(self):
        return self.__parsed[0]

    @property
    def flags(self):
        return self.__parser_state.flags
        
    @property
    def pattern(self):
        return self.__pattern
    
    @property
    def groups(self):
        return self.__parser_state.groups.count
    
    @property
    def groupindex(self):
        return dict(self.__parser_state.groups.names)
    
    def scanner(self, text, pos=0, endpos=None):
        return MatchIterator(self, self.__parsed, text, pos=pos, endpos=endpos,
                             engine=self.__engine)
        
    def match(self, text, pos=0, endpos=None):
        return self.scanner(text, pos=pos, endpos=endpos).match()
    
    def search(self, text, pos=0, endpos=None):
        return self.scanner(text, pos=pos, endpos=endpos).search()
        
    def finditer(self, text, pos=0, endpos=None):
        pending_empty = None
        for found in self.scanner(text, pos=pos, endpos=endpos).searchiter():
            # this is the "not touching" condition
            if pending_empty:
                if pending_empty.end() < found.start():
                    yield pending_empty
                pending_empty = None
            if found.group():
                yield found
            else:
                pending_empty = found
        if pending_empty:
            yield pending_empty

    def splititer(self, text, maxsplit=0):
        pos = 0
        maxsplit = maxsplit if maxsplit else -1
        for found in self.finditer(text):
            if found.group():
                yield text[pos:found.start()]
                for group in found.groups():
                    yield group
                pos = found.end()
                maxsplit -= 1
                if not maxsplit:
                    break
        yield text[pos:]
        
    def subiter(self, text, count=0):
        # this implements the "not adjacent" condition
        count = count if count else -1
        prev = None
        pending_empty = None
        for found in self.scanner(text).searchiter():
            if pending_empty:
                if pending_empty.end() < found.start():
                    yield pending_empty
                    prev = pending_empty
                    count -= 1
                    if not count:
                        break
                pending_empty = None
            if found.group():
                yield found
                prev = found
                count -= 1
                if not count:
                    break
            elif not prev or prev.end() < found.start():
                pending_empty = found
        if pending_empty and count:
            yield pending_empty
            
    def subn(self, repl, text, count=0):
        replacement = compile_repl(repl, self.__parser_state)
        n = 0
        pos = 0
        results = []
        for found in self.subiter(text, count):
            results.append(text[pos:found.start()])
            results.append(replacement(found))
            n += 1
            pos = found.end()
        results += text[pos:]
        return (self.__parser_state.alphabet.join(*results), n)
    
    def findall(self, text, pos=0, endpos=None):
        def expand(match):
            if match.lastindex:
                groups = match.groups(default='')
                if len(groups) == 1:
                    return groups[0]
                else:
                    return groups
            else:
                return match.group()
        return list(map(expand, self.finditer(text, pos=pos, endpos=endpos)))
    
    def split(self, text, maxsplit=0):
        return list(self.splititer(text, maxsplit=maxsplit))
    
    def sub(self, repl, text, count=0):
        return self.subn(repl, text, count=count)[0]
    
    
class MatchIterator(object):
    '''
    A compiled regexp and a string, plus offset state.
    
    Originally, this was implemented as generators in RegexObject, but the 
    standard tests imply the existence of this (otherwise undocumented)
    class.
    
    Successive calls to match and search increment indices.  Methods return
    None when no more calls will work.
    '''
    
    def __init__(self, re, parsed, text, pos=0, endpos=None, engine=None):
        require_engine(engine)
        self.__re = re
        self.__parsed = parsed
        self.__text = text
        self.__pos = pos
        self.__endpos = endpos if endpos else len(text)
        self.__engine = engine(*parsed)
    
    @property
    def __parser_state(self):
        return self.__parsed[0]

    def next(self, search):
        if self.__pos <= self.__endpos:
            groups = self.__engine.run(self.__text[:self.__endpos], 
                                       pos=self.__pos, search=search)
            if groups:
                found = MatchObject(groups, self.__re, self.__text, 
                                    self.__pos, self.__endpos, 
                                    self.__parser_state)
                offset = found.end()
                self.__pos = offset if offset > self.__pos else offset + 1 
                return found
        return None
    
    def match(self):
        return self.next(False)
    
    def search(self):
        return self.next(True)
    
    def iter(self, search):
        while True:
            found = self.next(search)
            if found is None:
                break
            yield found
    
    def matchiter(self):
        return self.iter(False)
            
    def searchiter(self):
        return self.iter(True)
    
    @property
    def remaining(self):
        return self.__text[self.__pos:]
    

class MatchObject(object):
    
    def __init__(self, groups, re, text, pos, endpos, state):
        self.__groups = groups
        self.re = re
        self.string = text
        self.pos = pos
        self.endpos = endpos
        self.__state = state
        self.lastindex = groups.lastindex
        self.lastgroup = groups.lastgroup
        
    def group(self, *indices):
        if not indices:
            indices = [0]
        if len(indices) == 1:
            return self.__groups.group(indices[0])
        else:
            return tuple(map(lambda n: self.__groups.group(n), indices))
        
    def groups(self, default=None):
        return tuple(self.__groups.group(index, default=default) 
                     for index in self.__groups.indices)
        
    def start(self, group=0):
        return self.__groups.start(group)

    def end(self, group=0):
        return self.__groups.end(group)
    
    def span(self, group=0):
        return (self.start(group), self.end(group))
    
    def groupdict(self, default=None):
        groups = {}
        for name in self.re.groupindex:
            groups[name] = self.__groups.group(name, default=default)
        return groups
    
    def expand(self, repl):
        replacement = compile_repl(repl, self.__state)
        return replacement(self)
    
    @property
    def regs(self):
        '''
        This is an undocumented hangover from regex in 1.5
        '''
        groups = [(self.start(index), self.end(index)) 
                    for index in range(self.re.groups+1)
                    if self.__groups.group(index)]
        return tuple(groups)
    
    
def match(pattern, text, flags=0, alphabet=None, engine=None):
    require_engine(engine)
    return compile(pattern, flags=flags, 
                   alphabet=alphabet, engine=engine).match(text)


def search(pattern, text, flags=0, alphabet=None, engine=None):
    require_engine(engine)
    return compile(pattern, flags=flags, 
                   alphabet=alphabet, engine=engine).search(text)


def findall(pattern, text, flags=0, alphabet=None, engine=None):
    require_engine(engine)
    return compile(pattern, flags=flags, 
                   alphabet=alphabet, engine=engine).findall(text)


def finditer(pattern, text, flags=0, alphabet=None, engine=None):
    require_engine(engine)
    return compile(pattern, flags=flags, 
                   alphabet=alphabet, engine=engine).finditer(text)


def sub(pattern, repl, text, count=0, flags=0, alphabet=None, engine=None):
    '''
    Find `pattern` in `text` and replace it with `repl`; limit this to
    `count` replacements (from left) if `count > 0`.
    '''
    require_engine(engine)
    return compile(pattern, flags=flags, 
                   alphabet=alphabet, engine=engine).sub(repl, text, count=count)


def subn(pattern, repl, text, count=0, flags=0, alphabet=None, engine=None):
    return compile(pattern, flags=flags, 
                   alphabet=alphabet, engine=engine).subn(repl, text, count=count)


def split(pattern, text, maxsplit=0, flags=0, alphabet=None, engine=None):
    return compile(pattern, flags=flags, 
                   alphabet=alphabet, engine=engine).split(text, maxsplit=maxsplit)


error = RxpyException


def escape(text):
    def letters():
        for letter in text:
            if letter not in _ALPHANUMERICS:
                yield '\\'
            yield letter
    return type(text)('').join(list(letters()))


class Scanner(object):
    '''
    Also undocumented in the Python docs.
    http://code.activestate.com/recipes/457664-hidden-scanner-functionality-in-re-module/
    '''

    def __init__(self, pairs, flags=0, alphabet=None, engine=None):
        require_engine(engine)
        self.__regex = RegexObject(parse_groups(map(lambda x: x[0], pairs), 
                                                engine, flags=flags, alphabet=alphabet),
                                   engine=engine)
        self.__actions = list(map(lambda x: x[1], pairs))
    
    def scaniter(self, text, pos=0, endpos=None, search=False):
        return self.__scaniter(self.__regex.scanner(text, pos=pos, endpos=endpos), 
                               search=search)

    def scan(self, text, pos=0, endpos=None, search=False):
        scanner = self.__regex.scanner(text, pos=pos, endpos=endpos)
        return (list(self.__scaniter(scanner, search=search)), scanner.remaining)
                     
    def __scaniter(self, scanner, search=False):
        for found in scanner.iter(search):
            if self.__actions[found.lastindex-1]:
                yield self.__actions[found.lastindex-1](self, found.group())
        

def require_engine(engine):
    if not engine:
        raise RxpyException('Engine must be given for RXPY '
                            '(use an engine-specific re module).')
