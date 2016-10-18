import attr
import re
from ..entities import Blockchain
from .nodes import NodesProcessor
from ..connectors import BmaConnector
from duniterpy.api import bma, errors
from duniterpy.documents import Block, BMAEndpoint
import asyncio


@attr.s
class BlockchainProcessor:
    _repo = attr.ib()  # :type sakia.data.repositories.CertificationsRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(app.db.blockchains_repo,
                   BmaConnector(NodesProcessor(app.db.nodes_repo)))

    def current_buid(self, currency):
        """
        Get the local current blockuid
        :rtype: duniterpy.documents.BlockUID
        """
        return self._repo.get_one({'currency': currency}).current_buid

    def time(self, currency):
        """
        Get the local current median time
        :rtype: int
        """
        return self._repo.get_one({'currency': currency}).median_time

    def parameters(self, currency):
        """
        Get the parameters of the blockchain
        :rtype: sakia.data.entities.BlockchainParameters
        """
        return self._repo.get_one({'currency': currency}).parameters

    def monetary_mass(self, currency):
        """
        Get the local current monetary mass
        :rtype: int
        """
        return self._repo.get_one({'currency': currency}).monetary_mass

    def members_count(self, currency):
        """
        Get the number of members in the blockchain
        :rtype: int
        """
        return self._repo.get_one({'currency': currency}).members_count

    def last_ud(self, currency):
        """
        Get the last ud value and base
        :rtype: int, int
        """
        blockchain = self._repo.get_one({'currency': currency})
        return blockchain.last_ud, blockchain.last_ud_base

    def last_ud_time(self, currency):
        """
        Get the last ud time
        :rtype: int
        """
        blockchain = self._repo.get_one({'currency': currency})
        return blockchain.last_ud_time

    def previous_monetary_mass(self, currency):
        """
        Get the local current monetary mass
        :rtype: int
        """
        return self._repo.get_one({'currency': currency}).previous_mass

    def previous_members_count(self, currency):
        """
        Get the local current monetary mass
        :rtype: int
        """
        return self._repo.get_one({'currency': currency}).previous_members_count

    def previous_ud(self, currency):
        """
        Get the previous ud value and base
        :rtype: int, int
        """
        blockchain = self._repo.get_one({'currency': currency})
        return blockchain.previous_ud, blockchain.previous_ud_base

    def previous_ud_time(self, currency):
        """
        Get the previous ud time
        :rtype: int
        """
        blockchain = self._repo.get_one({'currency': currency})
        return blockchain.previous_ud_time

    async def new_blocks_with_identities(self, currency):
        """
        Get blocks more recent than local blockuid
        with identities
        """
        with_identities = []
        future_requests = []
        for req in (bma.blockchain.Joiners,
                    bma.blockchain.Leavers,
                    bma.blockchain.Actives,
                    bma.blockchain.Excluded,
                    bma.blockchain.Newcomers):
            future_requests.append(self._bma_connector.get(currency, req))
        results = await asyncio.gather(future_requests)

        for res in results:
            with_identities += res["result"]["blocks"]

        local_current_buid = self.current_buid(currency)
        return sorted([b for b in with_identities if b > local_current_buid.number])

    async def new_blocks_with_money(self, currency):
        """
        Get blocks more recent than local block uid
        with money data (tx and uds)
        """
        with_money = []
        future_requests = []
        for req in (bma.blockchain.UD, bma.blockchain.TX):
            future_requests.append(self._bma_connector.get(currency, req))
        results = await asyncio.gather(future_requests)

        for res in results:
            with_money += res["result"]["blocks"]

        local_current_buid = self.current_buid(currency)
        return sorted([b for b in with_money if b > local_current_buid.number])

    async def blocks(self, numbers, currency):
        """
        Get blocks from the network
        :param List[int] numbers: list of blocks numbers to get
        :return: the list of block documents
        :rtype: List[duniterpy.documents.Block]
        """
        from_block = min(numbers)
        to_block = max(numbers)
        count = to_block - from_block

        blocks_data = await self._bma_connector.get(currency, bma.blockchain.Blocks, req_args={'count': count,
                                                                                     'from_': from_block})
        blocks = []
        for data in blocks_data:
            if data['number'] in numbers:
                blocks.append(Block.from_signed_raw(data["raw"] + data["signature"] + "\n"))

        return blocks

    async def initialize_blockchain(self, currency, log_stream):
        """
        Start blockchain service if it does not exists
        """
        blockchain = self._repo.get_one(currency=currency)
        if not blockchain:
            blockchain = Blockchain(currency=currency)
            log_stream("Requesting current block")
            try:
                current_block = await self._bma_connector.get(currency, bma.blockchain.Current)
                signed_raw = "{0}{1}\n".format(current_block['raw'], current_block['signature'])
                block = Block.from_signed_raw(signed_raw)
                blockchain.current_buid = block.blockUID
                blockchain.median_time = block.mediantime
            except errors.DuniterError as e:
                if e.ucode != errors.NO_CURRENT_BLOCK:
                    raise

            log_stream("Requesting blocks with dividend")
            with_ud = await self._bma_connector.get(currency, bma.blockchain.UD)
            blocks_with_ud = with_ud['result']['blocks']

            if len(blocks_with_ud) > 0:
                log_stream("Requesting last block with dividend")
                try:
                    index = max(len(blocks_with_ud) - 1, 0)
                    block_number = blocks_with_ud[index]
                    block_with_ud = await self._bma_connector.get(currency, bma.blockchain.Block,
                                                                  req_args={'number': block_number})
                    if block_with_ud:
                        blockchain.last_ud = block_with_ud['dividend']
                        blockchain.last_ud_base = block_with_ud['unitbase']
                        blockchain.last_ud_time = block_with_ud['medianTime']
                        blockchain.current_mass = block_with_ud['monetaryMass']
                        blockchain.nb_members = block_with_ud['membersCount']
                except errors.DuniterError as e:
                    if e.ucode != errors.NO_CURRENT_BLOCK:
                        raise

                log_stream("Requesting previous block with dividend")
                try:
                    index = max(len(blocks_with_ud) - 2, 0)
                    block_number = blocks_with_ud[index]
                    block_with_ud = await self._bma_connector.get(currency, bma.blockchain.Block,
                                                                  req_args={'number': block_number})
                    blockchain.previous_mass = block_with_ud['monetaryMass']
                except errors.DuniterError as e:
                    if e.ucode != errors.NO_CURRENT_BLOCK:
                        raise

            self._repo.insert(blockchain)

