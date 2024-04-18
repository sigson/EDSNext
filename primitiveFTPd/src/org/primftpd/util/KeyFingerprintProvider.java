package org.primftpd.util;

import android.content.Context;
import android.util.Base64;

import org.apache.ftpserver.util.IoUtils;
import org.primftpd.crypto.HostKeyAlgorithm;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.Serializable;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.PublicKey;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

public class KeyFingerprintProvider implements Serializable {

    private static final long serialVersionUID = 1L;

    private boolean fingerprintsGenerated = false;
    private boolean keyPresent = false;

    private final Map<HostKeyAlgorithm, KeyFingerprintBean> fingerprints = new HashMap<>();

    public FileInputStream buildPublickeyInStream(Context ctxt, HostKeyAlgorithm hka) throws IOException {
        return ctxt.openFileInput(hka.getFilenamePublicKey());
    }

    public FileOutputStream buildPublickeyOutStream(Context ctxt, HostKeyAlgorithm hka) throws IOException {
        return ctxt.openFileOutput(hka.getFilenamePublicKey(), Context.MODE_PRIVATE);
    }

    public FileInputStream buildPrivatekeyInStream(Context ctxt, HostKeyAlgorithm hka) throws IOException {
        return ctxt.openFileInput(hka.getFilenamePrivateKey());
    }

    public FileOutputStream buildPrivatekeyOutStream(Context ctxt, HostKeyAlgorithm hka) throws IOException {
        return ctxt.openFileOutput(hka.getFilenamePrivateKey(), Context.MODE_PRIVATE);
    }

    /**
     * Creates figerprints of public key.
     */
    public void calcPubkeyFingerprints(Context ctxt) {
        Logger logger = LoggerFactory.getLogger(getClass());
        logger.trace("calcPubkeyFingerprints()");
        fingerprintsGenerated = true;
        FileInputStream fis = null;
        for (HostKeyAlgorithm hka : HostKeyAlgorithm.values()) {
            try {
                fis = buildPublickeyInStream(ctxt, hka);

                // check if key is present
                if (fis.available() <= 0) {
                    keyPresent = false;
                    throw new Exception("key seems not to be present");
                }

                PublicKey pubKey = hka.readPublicKey(fis);
                if (pubKey == null) {
                    logger.info("key is null");
                    return;
                }
                byte[] encodedKey = hka.encodeAsSsh(pubKey);

                String fingerprintMd5 = " - ";
                String fingerprintSha1 = " - ";
                String fingerprintSha256 = " - ";
                String base64Md5 = "";
                String base64Sha1 = "";
                String base64Sha256 = "";
                String bytesMd5 = "";
                String bytesSha1 = "";
                String bytesSha256 = "";

                // fingerprints
                FingerprintBean bean = fingerprint(encodedKey, "MD5");
                if (bean != null) {
                    fingerprintMd5 = bean.fingerprint();
                    base64Md5 = bean.base64;
                    bytesMd5 = bean.bytes;
                }

                bean = fingerprint(encodedKey, "SHA-1");
                if (bean != null) {
                    fingerprintSha1 = bean.fingerprint();
                    base64Sha1 = bean.base64;
                    bytesSha1 = bean.bytes;
                }

                bean = fingerprint(encodedKey, "SHA-256");
                if (bean != null) {
                    fingerprintSha256 = bean.fingerprint();
                    base64Sha256 = bean.base64;
                    bytesSha256 = bean.bytes;
                }

                fingerprints.put(hka, new KeyFingerprintBean(
                        fingerprintMd5,
                        fingerprintSha1,
                        fingerprintSha256,
                        base64Md5,
                        base64Sha1,
                        base64Sha256,
                        bytesMd5,
                        bytesSha1,
                        bytesSha256
                ));

                keyPresent = true;

            } catch (Exception e) {
                logger.info("key does probably not exist");
                logger.debug("tried to load key", e);
            } finally {
                if (fis != null) {
                    IoUtils.close(fis);
                }
            }
        }
    }

    public FingerprintBean fingerprint(byte[] pubKeyEnc, String hashAlgo)
            throws NoSuchAlgorithmException {
        MessageDigest md = MessageDigest.getInstance(hashAlgo);
        md.update(pubKeyEnc);
        byte[] fingerPrintBytes = md.digest();
        String base64 = Base64.encodeToString(fingerPrintBytes, Base64.NO_PADDING);
        String beautified = beautify(fingerPrintBytes);
        return new FingerprintBean(beautified, base64);
    }

    protected String beautify(byte[] fingerPrintBytes)
    {
        StringBuilder fingerPrint = new StringBuilder();
        for (int i=0; i<fingerPrintBytes.length; i++) {
            byte b = fingerPrintBytes[i];
            String hexString = Integer.toHexString(b);
            if (hexString.length() > 2) {
                hexString = hexString.substring(
                        hexString.length() - 2,
                        hexString.length());
            } else if (hexString.length() < 2) {
                hexString = "0" + hexString;
            }
            fingerPrint.append(hexString.toUpperCase(Locale.ENGLISH));
            if (i != fingerPrintBytes.length -1) {
                fingerPrint.append(":");

                if ((i + 1) % 10 == 0) {
                    // force line breaks in UI
                    fingerPrint.append("\n");
                }
            }
        }
        return fingerPrint.toString();
    }

    public boolean areFingerprintsGenerated() {
        return fingerprintsGenerated;
    }

    public boolean isKeyPresent() {
        return keyPresent;
    }

    public Map<HostKeyAlgorithm, KeyFingerprintBean> getFingerprints() {
        return fingerprints;
    }
}
