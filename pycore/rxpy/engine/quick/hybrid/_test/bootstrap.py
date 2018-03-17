
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


from unittest import TestCase

from rxpy.engine._test.base import BaseTest
from rxpy.engine.quick.hybrid.engine import HybridEngine


class HybridEngineTest(BaseTest, TestCase):

    def default_engine(self):
        return HybridEngine
    
    def test_string(self):
        assert self.engine(self.parse('a'), 'a')
        assert not self.engine(self.parse('a'), 'b')
        assert self.engine(self.parse('a'), 'ba', search=True)
        assert self.engine(self.parse('abc'), 'abc')
        assert not self.engine(self.parse('abcd'), 'abc')
        
    def test_groups(self):
        self.assert_groups('(.)', 'a', {0: ('a', 0, 1), 1: ('a', 0, 1)})
        self.assert_groups('.(.)(.)', 'abc', 
                           {0: ('abc', 0, 3), 1: ('b', 1, 2), 2: ('c', 2, 3)})
    
    def test_null_group_bug(self):
        assert self.engine(self.parse('(a(?=\s[^a]))'), 'a b')
        
        