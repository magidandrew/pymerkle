"""
Provides high-level prover interface for Merkle-trees
"""

from abc import ABCMeta, abstractmethod
import uuid
from time import time, ctime
import json
from pymerkle.exceptions import (NoPathException, InvalidChallengeError,)
from pymerkle.serializers import ProofSerializer
from pymerkle.utils import stringify_path


class Prover(object, metaclass=ABCMeta):
    """
    High-level prover interface for Merkle-trees
    """

    @abstractmethod
    def find_index(self, checksum):
        """
        """

    @abstractmethod
    def audit_path(self, index):
        """
        """

    @abstractmethod
    def multi_hash(self, signed_hashes, start):
        """
        """

    @abstractmethod
    def consistency_path(self, sublength):
        """
        """

    @abstractmethod
    def get_commitment(self):
        """
        """

    def merkleProof(self, challenge, commit=True):
        """
        :param challenge:
        :type challenge: dict
        :returns:
        :rtype: Proof
        """
        keys = set(challenge.keys())
        if keys == {'checksum'}:
            checksum = challenge['checksum']
            proof = self.auditProof(checksum, commit=commit)
        elif keys == {'subhash', 'sublength'}:
            subhash = challenge['subhash']
            sublength = challenge['sublength']
            proof = self.consistencyProof(subhash, sublength,
                commit=commit)
        else:
            raise InvalidChallengeError

        return proof


    def auditProof(self, checksum, commit=False):
        """
        Response of the Merkle-tree to the request of providing an
        audit-proof based upon the provided checksum

        :param checksum: the checksum which the requested audit-proof is to
                be based upon
        :type checksum: bytes
        :returns: audit-path along with validation parameters
        :rtype: proof.Proof

        :raises InvalidChallengeError: if the provided argument's type
            is not as prescribed
        """
        if isinstance(checksum, bytes):                     # Assuming hexdigest
            pass
        elif isinstance(checksum, str):
            checksum = checksum.encode()                    # Assuming hexstring
        else:
            raise InvalidChallengeError

        index = self.find_index(checksum)
        if commit is True:
            commitment = self.get_commitment()
        else:
            commitment = None

        try:
            proof_index, audit_path = self.audit_path(index)
        except NoPathException:
            return Proof(
                provider=self.uuid,
                hash_type=self.hash_type,
                encoding=self.encoding,
                security=self.security,
                raw_bytes=self.raw_bytes,
                commitment=commitment,
                proof_index=-1,
                proof_path=())

        return Proof(
            provider=self.uuid,
            hash_type=self.hash_type,
            encoding=self.encoding,
            security=self.security,
            raw_bytes=self.raw_bytes,
            commitment=commitment,
            proof_index=proof_index,
            proof_path=audit_path)


    def consistencyProof(self, subhash, sublength, commit=False):
        """
        Response of the Merkle-tree to the request of providing a
        consistency-proof for the provided parameters

        Arguments of this function amount to a presumed previous state
        (root-hash and length) of the Merkle-tree

        :param subhash: root-hash of a presumably valid previous
            state of the Merkle-tree
        :type subhash: bytes
        :param sublength: presumable length (number of leaves) for the
            above previous state of the Merkle-tree
        :type sublength: int
        :returns: consistency-path along with validation parameters
        :rtype: proof.Proof

        .. note:: If no proof-path corresponds to the provided parameters (that
            is, a ``NoPathException`` gets implicitly raised) or the provided
            parameters do not correpond to a valid previous state of the
            Merkle-tree (that is, the implicit inclusion-test fails),
            then the proof generated contains an empty proof-path, or,
            equivalently a negative proof-index ``-1`` is inscribed in it,
            so that it is predestined to be found invalid.

        :raises InvalidChallengeError: if type of any of the provided
            arguments is not as prescribed
        """
        if isinstance(subhash, bytes):                      # Assuming hexdigest
            pass
        elif isinstance(subhash, str):
            subhash = subhash.encode()                      # Assuming hexstring
        else:
            raise InvalidChallengeError

        if type(sublength) is not int or sublength <= 0:
            raise InvalidChallengeError

        if commit is True:
            commitment = self.get_commitment()
        else:
            commitment = None

        try:
            proof_index, left_path, full_path = self.consistency_path(sublength)
        except NoPathException: # Covers also the empty-tree case
            return Proof(
                provider=self.uuid,
                hash_type=self.hash_type,
                encoding=self.encoding,
                raw_bytes=self.raw_bytes,
                security=self.security,
                commitment=commitment,
                proof_index=-1,
                proof_path=())

        # Inclusion test
        if subhash != self.multi_hash(left_path,len(left_path) - 1):
            return Proof(
                provider=self.uuid,
                hash_type=self.hash_type,
                encoding=self.encoding,
                raw_bytes=self.raw_bytes,
                security=self.security,
                commitment=commitment,
                proof_index=-1,
                proof_path=())

        return Proof(
            provider=self.uuid,
            hash_type=self.hash_type,
            encoding=self.encoding,
            raw_bytes=self.raw_bytes,
            security=self.security,
            commitment=commitment,
            proof_index=proof_index,
            proof_path=full_path)


class Proof(object):
    """
    Class for Merkle-proofs

    :param provider: uuid of the provider Merkle-tree
    :type provider: str
    :param hash_type: hash type of the provider Merkle-tree
    :type hash_type: str
    :param encoding: encoding type of the provider Merkle-tree
    :type encoding: str
    :param security: security mode of the provider Merkle-tree
    :type security: bool
    :param proof_index: path index (zero based) where the
        validation procedure should start from
    :type proof_index: int
    :param proof_path: path of signed hashes
    :type proof_path: tuple<(+1/-1, bytes)>

    .. note:: Required Merkle-tree parameters are necessary for proof
        validation to be performed

    Instead of providing the above arguments corresponding to `*args`, given a
    proof ``p`` instances of ``Proof`` may also be constructed in the following
    ways:

    >>> from pymerkle.proof import Proof
    >>> q = Proof(from_json=p.toJSONString())
    >>> r = Proof(from_dict=json.loads(p.toJSONString()))

    .. note:: Constructing proofs in the above ways is a genuine *replication*,
        since ``q`` and ``r`` have the same *uuid* and *timestamp* as ``p``

    :ivar header: (*dict*) contains the keys *uuid*, *timestamp*,
        *creation_moment*, *generation*, *provider*, *hash_type*, *encoding*,
        *raw_bytes*, *security* and *status*
    :ivar body: (*dict*) Contains the keys *proof_index* and *proof_path*
    """

    def __init__(self, **kwargs):
        """
        """
        header = {}
        body = {}
        if kwargs.get('from_dict'):                             # from json dict
            input = kwargs['from_dict']
            header.update(input['header'])
            if header['commitment']:
                header['commitment'] = header['commitment'].encode()
            body['proof_index'] = input['body']['proof_index']
            body['proof_path'] = tuple((
                pair[0],
                bytes(pair[1], header['encoding'])
            ) for pair in input['body']['proof_path'])
        elif kwargs.get('from_json'):                           # from json text
            input = json.loads(kwargs['from_json'])
            header.update(input['header'])
            if header['commitment']:
                header['commitment'] = header['commitment'].encode()
            body['proof_index'] = input['body']['proof_index']
            body['proof_path'] = tuple((
                pair[0],
                bytes(pair[1], header['encoding'])
            ) for pair in input['body']['proof_path'])
        else:                                                  # multiple kwargs
            header.update({
                'uuid': str(uuid.uuid1()),
                'timestamp': int(time()),
                'creation_moment': ctime(),
                'provider': kwargs['provider'],
                'hash_type': kwargs['hash_type'],
                'encoding': kwargs['encoding'],
                'raw_bytes': kwargs['raw_bytes'],
                'security': kwargs['security'],
                'commitment': kwargs.get('commitment'),
                'status': None})
            body.update({
                'proof_index': kwargs['proof_index'],
                'proof_path': kwargs['proof_path']})
        self.header = header
        self.body = body


    def get_validation_params(self):
        """
        Extracts from the proof's header all necessary parameters
        required for its validation

        :rtype: dict
        """
        header = self.header
        validation_params = dict({
            'hash_type': header['hash_type'],
            'encoding': header['encoding'],
            'raw_bytes': header['raw_bytes'],
            'security': header['security'],
        })
        return validation_params


    def __repr__(self):
        """
        Overrides the default implementation.

        Sole purpose of this function is to easily display info
        about a proof by just invoking it at console

        .. warning:: Contrary to convention, the output of this implementation
            is *not* insertible into the ``eval()`` builtin function
        """
        header = self.header
        body = self.body
        encoding = header['encoding']

        return '\n    ----------------------------------- PROOF ------------------------------------\
                \n\
                \n    uuid        : {uuid}\
                \n\
                \n    timestamp   : {timestamp} ({creation_moment})\
                \n    provider    : {provider}\
                \n\
                \n    hash-type   : {hash_type}\
                \n    encoding    : {encoding}\
                \n    raw_bytes   : {raw_bytes}\
                \n    security    : {security}\
                \n\
                \n    proof-index : {proof_index}\
                \n    proof-path  :\
                \n    {proof_path}\
                \n\
                \n    commitment  : {commitment}\
                \n\
                \n    status      : {status}\
                \n\
                \n    -------------------------------- END OF PROOF --------------------------------\
                \n'.format(
                    uuid=header['uuid'],
                    timestamp=header['timestamp'],
                    creation_moment=header['creation_moment'],
                    provider=header['provider'],
                    hash_type=header['hash_type'].upper().replace('_', '-'),
                    encoding=header['encoding'].upper().replace('_', '-'),
                    raw_bytes='TRUE' if header['raw_bytes'] else 'FALSE',
                    security='ACTIVATED' if header['security'] else 'DEACTIVATED',
                    commitment=header['commitment'].decode() \
                    if header['commitment'] else None,
                    proof_index=body['proof_index'],
                    proof_path=stringify_path(body['proof_path'], header['encoding']),
                    status='UNVALIDATED' if header['status'] is None \
                    else 'VALID' if header['status'] is True else 'NON VALID')


    @classmethod
    def deserialize(cls, serialized):
        """
        :params serialized:
        :type: dict or str
        """
        kwargs = {}
        if isinstance(serialized, dict):
            kwargs.update({'from_dict': serialized})
        elif isinstance(serialized, str):
            kwargs.update({'from_json': serialized})
        return cls(**kwargs)

# Serialization

    def serialize(self):
        """
        Returns a JSON entity with the proof's current
        characteristics as key-value pairs

        :rtype: dict
        """
        return ProofSerializer().default(self)

    def toJSONString(self):
        """
        Returns a stringification of the proof's JSON serialization

        :rtype: str
        """
        return json.dumps(self, cls=ProofSerializer, sort_keys=True, indent=4)
