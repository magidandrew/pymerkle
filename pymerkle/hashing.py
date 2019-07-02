"""
Provides a class ``hash_machine`` encapsulating the two basic hash utilities used accross the library.
Instances of this class should receive their configuration parameters from the ``ENCODINGS`` and
``HASH_TYPES`` global variables of this module
"""

import hashlib
from pymerkle.exceptions import NotSupportedEncodingError, NotSupportedHashTypeError, EmptyPathException

ENCODINGS = (
    'euc_jisx0213',
    'euc_kr',
    'ptcp154',
    'hp_roman8',
    'cp852',
    'iso8859_8',
    'cp858',
    'big5hkscs',
    'cp860',
    'iso2022_kr',
    'iso8859_3',
    'mac_iceland',
    'cp1256',
    'kz1048',
    'cp869',
    'ascii',
    'cp932',
    'utf_7',
    'mac_roman',
    'shift_jis',
    'cp1251',
    'iso8859_5',
    'utf_32_be',
    'cp037',
    'iso2022_jp_1',
    'cp855',
    'cp850',
    'gb2312',
    'iso8859_9',
    'cp775',
    'utf_32_le',
    'iso8859_11',
    'cp1140',
    'iso8859_10',
    'cp857',
    'johab',
    'cp1252',
    'mac_greek',
    'utf_8',
    'euc_jis_2004',
    'cp1254',
    'iso8859_4',
    'utf_32',
    'iso2022_jp_3',
    'iso2022_jp_2004',
    'cp1125',
    'tis_620',
    'cp950',
    'hz',
    'iso8859_13',
    'iso8859_7',
    'iso8859_6',
    'cp862',
    'iso8859_15',
    'mac_cyrillic',
    'iso2022_jp_ext',
    'cp437',
    'gbk',
    'iso8859_16',
    'iso8859_14',
    'cp1255',
    'cp949',
    'cp1026',
    'cp866',
    'gb18030',
    'utf_16',
    'iso8859_2',
    'cp865',
    'cp500',
    'shift_jis_2004',
    'mac_turkish',
    'cp1257',
    'big5',
    'cp864',
    'shift_jisx0213',
    'cp273',
    'cp861',
    'cp424',
    'mac_latin2',
    'cp1258',
    'koi8_r',
    'cp863',
    'latin_1',
    'iso2022_jp_2',
    'utf_16_le',
    'cp1250',
    'euc_jp',
    'utf_16_be',
    'cp1253',
    'iso2022_jp')
"""Supported encoding types"""

HASH_TYPES = (
    'md5',
    'sha224',
    'sha256',
    'sha384',
    'sha512',
    'sha3_224',
    'sha3_256',
    'sha3_384',
    'sha3_512'
)
"""Supported hash types"""


class hash_machine(object):
    """Encapsulates the two basic hash utilities used accross this library.

    Sole purpose of this class is to fix at construction the hash and encoding types used for encryption,
    so that these parameters need not be redefined every time a hash utility is invoked. Instances
    of this class are thus to be initialized with every new construction of a Merkle-tree or every time
    a proof validation is about to be performed

    :param hash_type: specifies the hash algorithm to be used by the machine; must be among the elements of the ``HASH_TYPES``
                      global variable (upper- or mixed-case with '-' instead of '_' allowed). Defaults to ``'sha256'``
                      if unspecified
    :type hash_type:  str
    :param encoding:  specifies the encoding algorithm to be used by machine before hashing; must be among the elements of the
                      ENCODINGS global variable (upper- or mixed-case with ``-`` instead of ``_`` allowed). Defaults to ``'utf_8'``
                      if unspecified
    :type encoding:   str
    :param security:  defaults to ``True``, in which case security standards are applied against second-preimage attack, i.e.,
                      single, resp. double arguments of the ``.hash`` method will be prepended with ``'\\x00'``, resp. ``'\\x01'``
                      before hashing
    :type security:   bool

    :raises Exception: if ``hash_type``, resp. ``encoding`` is not contained in ``hashing.HASH_TYPES``, resp. ``hashing.ENCODINGS``

    :ivar HASH_ALGORITHM: (*builtin_function_or_method*) Hash algorithm used by the machine, specified in the obvious way
                          by the ``hash_type`` argument at construction
    :ivar ENCODING:       (*str*) Encoding type used by the machine before hashing, specified in the obvious way
                          by the ``encoding`` argument at construction
    :ivar SECURITY:       (*bool*) Indicates whether defense against second-preimage attack is activated, specified in the
                          obvious way by the ``security`` argument at construction
    """

    # -------------------------------- Construction --------------------------

    def __init__(self, hash_type='sha256', encoding='utf-8', security=True):

        # Select hash-algorithm

        _hash_type = hash_type.lower().replace('-', '_')

        if _hash_type not in HASH_TYPES:
            raise NotSupportedHashTypeError('Hash type %s is not supported' % hash_type)

        self.HASH_ALGORITHM = getattr(hashlib, _hash_type)

        # Select encoding

        _encoding = encoding.lower().replace('-', '_')

        if _encoding not in ENCODINGS:
            raise NotSupportedEncodingError('Encoding type %s is not supported' % encoding)

        self.ENCODING = _encoding

        # ~ If True, security prefices will be prepended before
        # ~ hashing for defense against second-preimage attack
        self.SECURITY = security
        self.PREFIX_0 = '\x00' if security else ''
        self.PREFIX_1 = '\x01' if security else ''


    def hash(self, first, second=None):
        """Core hash utility

        Returns the hash of the object occuring by concatenation of arguments in the given order.
        If only one argument is passed in, then the hash of this single argument is returned

        :param first:  left member of the pair to be hashed
        :type first:   str or bytes or bytearray
        :param second: [optional] right member of the pair to be hashed
        :type second:  bytes or bytearray

        .. warning:: if ``second`` is provided, then ``first`` *must* also be of `bytes`
                    or `byetarray` type

        :returns:      the hash of the provided pair
        :rtype:        bytes
        """

        if not second:                                                          # single argument case

            if isinstance(first, (bytes, bytearray)):                           # bytes-like input

                _hexdigest = self.HASH_ALGORITHM(
                    bytes(
                        '%s%s' % (
                            self.PREFIX_0,
                            first.decode(self.ENCODING)
                        ),
                        self.ENCODING
                    )
                ).hexdigest()

                return bytes(_hexdigest, self.ENCODING)

            else:                                                               # string input

                _hexdigest = self.HASH_ALGORITHM(
                    bytes(
                        '%s%s' % (
                            self.PREFIX_0,
                            first
                        ),
                        self.ENCODING)
                    ).hexdigest()

                return bytes(_hexdigest, self.ENCODING)

        else:                                                                   # two arguments case

            _hexdigest = self.HASH_ALGORITHM(
                bytes(
                    '%s%s%s%s' % (
                        self.PREFIX_1,
                        first.decode(self.ENCODING),
                        self.PREFIX_1,
                        second.decode(self.ENCODING)
                    ),
                    self.ENCODING
                )
            ).hexdigest()

            return bytes(_hexdigest, self.ENCODING)


    def multi_hash(self, signed_hashes, start):
        """Hash utility used in proof validation

        Repeatedly applies the ``.hash`` method over a tuple of signed hashes parenthesized in pairs
        as specified by accompanying signs. Schematically speaking, the result of

            ``multi_hash(signed_hashes=((1, a), (1, b), (-1, c), (-1, d)), start=1)``

        is equivalent to ``hash(hash(a, hash(b, c)), d)``. If the given sequence of signed hashes
        contains only one member, then this one hash is returned (without sign). That is,

            ``multi_hash(signed_hashes=((+/-1, a)), start=1)``

        is the same as ``a`` (no hashing over unique elements)

        .. warning:: When using this method, make sure that the combination of signs corresponds indeed
                     to a valid parenthetization

        :param signed_hashes: a sequence of signed hashes
        :type signed_hashes:  tuple of (+1/-1, bytes) pairs
        :param start:         position where the application of ``.hash`` will start from
        :type start:          int
        :returns:             the computed hash
        :rtype:               bytes

        .. note:: Returns ``None`` if the inserted sequence of signed hashes was empty
        """

        signed_hashes = list(signed_hashes)

        if signed_hashes == []:                                                 # Empty-tuple case
            raise EmptyPathException

        elif len(signed_hashes) == 1:                                           # One-element case
            return signed_hashes[0][1]

        else:

            i = start
            while len(signed_hashes) > 1:

                if signed_hashes[i][0] == +1:                                   # Pair with the right neighbour

                    if i == 0:

                        new_sign = +1
                    else:
                        new_sign = signed_hashes[i + 1][0]

                    new_hash = self.hash(
                        signed_hashes[i][1],
                        signed_hashes[i + 1][1]
                    )
                    move = +1

                else:                                                           # Pair with the left neighbour
                    new_sign = signed_hashes[i - 1][0]

                    new_hash = self.hash(
                        signed_hashes[i - 1][1],
                        signed_hashes[i][1]
                    )
                    move = -1

                # Store and shrink

                signed_hashes[i] = (new_sign, new_hash)
                del signed_hashes[i + move]

                if move < 0:
                    i -= 1

            # Return the unique element having remained after shrinking

            return signed_hashes[0][1]
