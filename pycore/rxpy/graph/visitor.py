
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


from rxpy.lib import UnsupportedOperation


class BaseVisitor(object):
    
    def string(self, next, text, state=None):
        raise UnsupportedOperation('string')
    
    def character(self, next, charset, state=None):
        raise UnsupportedOperation('character')
    
    def start_group(self, next, number, state=None):
        raise UnsupportedOperation('start_group')
    
    def end_group(self, next, number, state=None):
        raise UnsupportedOperation('end_group')

    def group_reference(self, next, number, state=None):
        raise UnsupportedOperation('group_reference')

    def conditional(self, next, number, state=None):
        raise UnsupportedOperation('conditional')

    def split(self, next, state=None):
        raise UnsupportedOperation('split')

    def match(self, state=None):
        raise UnsupportedOperation('match')

    def no_match(self, state=None):
        raise UnsupportedOperation('no_match')

    def dot(self, next, multiline, state=None):
        raise UnsupportedOperation('dot')
    
    def start_of_line(self, next, multiline, state=None):
        raise UnsupportedOperation('start_of_line')
    
    def end_of_line(self, next, multiline, state=None):
        raise UnsupportedOperation('end_of_line')
    
    def lookahead(self, next, node, equal, forwards, state=None):
        raise UnsupportedOperation('lookahead')

    def repeat(self, next, node, begin, end, lazy, state=None):
        raise UnsupportedOperation('repeat')
    
    def word_boundary(self, next, inverted, state=None):
        raise UnsupportedOperation('word_boundary')

    def digit(self, next, inverted, state=None):
        raise UnsupportedOperation('digit')
    
    def space(self, next, inverted, state=None):
        raise UnsupportedOperation('space')
    
    def word(self, next, inverted, state=None):
        raise UnsupportedOperation('word')
    
    def checkpoint(self, next, id, state=None):
        raise UnsupportedOperation('checkpoint')

