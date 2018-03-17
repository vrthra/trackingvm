
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


from rxpy.engine.parallel.base import ParallelEngine


class SerialEngine(ParallelEngine):
    '''
    Modify the outer loops so that, at each initial offset, all states
    are explored before progressing to the next search position.
    '''

    def _outer_loop(self, states, search, new_state):
        search_offset = self._offset
        first = True
        while first or (search and not states.final_state and
                            search_offset <= len(self._text)):
            if search:
                states.add_next(new_state(search_offset))
                self._set_offset(search_offset)
                search_offset += 1
            first = False
            while not states.final_state and states.more and \
                    self._offset <= len(self._text):
                self._inner_loop(states)


class HashingSerialEngine(SerialEngine):
    
    def __init__(self, parser_state, graph, hash_state=True):
        super(HashingSerialEngine, self).__init__(parser_state, graph, 
                                                  hash_state=hash_state)
