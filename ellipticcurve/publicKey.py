from .point import Point
from .utils.pem import getPemContent, createPem
from .utils.binary import hexFromByteString, byteStringFromHex, intFromHex, base64FromByteString, byteStringFromBase64
from .utils.der import hexFromInt, parse, DerFieldType, encodeConstructed, encodePrimitive
from .curve import secp256k1, getCurveByOid


class PublicKey:

    def __init__(self, point, curve):
        self.point = point
        self.curve = curve

    def toString(self, encoded=False):
        baseLength = 2 * self.curve.length()
        xHex = hexFromInt(self.point.x).zfill(baseLength)
        yHex = hexFromInt(self.point.y).zfill(baseLength)
        string = xHex + yHex
        if encoded:
            return "0004" + string
        return string

    def toDer(self):
        hexadecimal = encodeConstructed(
            encodeConstructed(
                encodePrimitive(DerFieldType.object, _ecdsaPublicKeyOid),
                encodePrimitive(DerFieldType.object, self.curve.oid),
            ),
            encodePrimitive(DerFieldType.bitString, self.toString(encoded=True)),
        )
        return byteStringFromHex(hexadecimal)

    def toPem(self):
        der = self.toDer()
        return createPem(content=base64FromByteString(der), template=_pemTemplate)

    @classmethod
    def fromPem(cls, string):
        publicKeyPem = getPemContent(pem=string, template=_pemTemplate)
        return cls.fromDer(byteStringFromBase64(publicKeyPem))

    @classmethod
    def fromDer(cls, string):
        hexadecimal = hexFromByteString(string)
        curveData, pointString = parse(hexadecimal)[0]
        publicKeyOid, curveOid = curveData
        if publicKeyOid != _ecdsaPublicKeyOid:
            raise Exception("The Public Key Object Identifier (OID) should be {ecdsaPublicKeyOid}, but {actualOid} was found instead".format(
                ecdsaPublicKeyOid=_ecdsaPublicKeyOid,
                actualOid=publicKeyOid,
            ))
        curve = getCurveByOid(curveOid)
        return cls.fromString(string=pointString, curve=curve)

    @classmethod
    def fromString(cls, string, curve=secp256k1, validatePoint=True):
        baseLength = 2 * curve.length()
        if len(string) > 2 * baseLength and string[:4] == "0004":
            string = string[4:]

        xs = string[:baseLength]
        ys = string[baseLength:]

        p = Point(
            x=intFromHex(xs),
            y=intFromHex(ys),
        )
        if validatePoint and not curve.contains(p):
            raise Exception(
                "Point ({x},{y}) is not valid for curve {name}".format(x=p.x, y=p.y, name=curve.name)
            )

        return PublicKey(point=p, curve=curve)


_ecdsaPublicKeyOid = (1, 2, 840, 10045, 2, 1)


_pemTemplate = """
-----BEGIN PUBLIC KEY-----
{content}
-----END PUBLIC KEY-----
"""
