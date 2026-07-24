import Foundation
import Security

struct RSAPSSReleaseSignatureVerifier: FirmwareReleaseSignatureVerifying {
    private let publicKey: SecKey
    private let allowedKeyId: String

    init(pkcs1PublicKeyPEM: String, keyId: String) throws {
        let base64Value = pkcs1PublicKeyPEM
            .replacingOccurrences(of: "-----BEGIN RSA PUBLIC KEY-----", with: "")
            .replacingOccurrences(of: "-----END RSA PUBLIC KEY-----", with: "")
            .components(separatedBy: .whitespacesAndNewlines)
            .joined()
        guard let keyData = Data(base64Encoded: base64Value) else {
            throw FirmwareReleaseError.invalidSignature
        }
        let attributes: [CFString: Any] = [
            kSecAttrKeyType: kSecAttrKeyTypeRSA,
            kSecAttrKeyClass: kSecAttrKeyClassPublic,
        ]
        guard let key = SecKeyCreateWithData(
            keyData as CFData,
            attributes as CFDictionary,
            nil
        ) else {
            throw FirmwareReleaseError.invalidSignature
        }
        publicKey = key
        allowedKeyId = keyId
    }

    func verify(
        data: Data,
        signature: Data,
        keyId: String,
        algorithm: String
    ) -> Bool {
        guard
            keyId == allowedKeyId,
            algorithm == "rsa-pss-sha256",
            SecKeyIsAlgorithmSupported(
                publicKey,
                .verify,
                .rsaSignatureMessagePSSSHA256
            )
        else {
            return false
        }
        var error: Unmanaged<CFError>?
        return SecKeyVerifySignature(
            publicKey,
            .rsaSignatureMessagePSSSHA256,
            data as CFData,
            signature as CFData,
            &error
        )
    }
}
