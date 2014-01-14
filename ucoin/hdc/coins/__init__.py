#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
# Caner Candan <caner@candan.fr>, http://caner.candan.fr
#

from .. import HDC, logging

logger = logging.getLogger("ucoin/hdc/coins")

class Coins(HDC):
    def __init__(self, pgp_fingerprint):
        super().__init__('hdc/coins/%s' % pgp_fingerprint)

class List(Coins):
    """GET a list of coins owned by the given [PGP_FINGERPRINT]."""

    def __get__(self):
        return self.requests_get('/list').json()

class View(Coins):
    """GET the ownership state of the coin [COIN_NUMBER] issued by [PGP_FINGERPRINT]."""

    def __init__(self, pgp_fingerprint, coin_number):
        super().__init__(pgp_fingerprint)

        self.coin_number = coin_number

    def __get__(self):
        return self.requests_get('/view/%d' % self.coin_number).json()

from . import view
