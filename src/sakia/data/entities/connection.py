import attr
from duniterpy.documents import block_uid, BlockUID


@attr.s()
class Connection:
    """
    A connection represents a connection to a currency's network
    It is defined by the currency name, and the key informations
    used to connect to it. If the user is using an identity, it is defined here too.
    """
    currency = attr.ib(convert=str)
    pubkey = attr.ib(convert=str)
    salt = attr.ib(convert=str)
    uid = attr.ib(convert=str, default="", cmp=False, hash=False)
    blockstamp = attr.ib(convert=block_uid, default=BlockUID.empty(), cmp=False, hash=False)
    password = attr.ib(convert=str, default="", cmp=False, hash=False)
