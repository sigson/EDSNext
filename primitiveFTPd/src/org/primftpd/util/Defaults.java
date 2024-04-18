package org.primftpd.util;

import android.content.Context;
import android.content.Intent;
import android.os.Environment;


import org.primftpd.crypto.HostKeyAlgorithm;
import org.primftpd.filepicker.ResettingFilePickerActivity;
import org.primftpd.filepicker.nononsenseapps.AbstractFilePickerActivity;
import org.primftpd.filepicker.nononsenseapps.FilePickerActivity;

import java.io.File;
import java.util.UUID;

public final class Defaults {
	private Defaults(){}

	public static final File HOME_DIR = Environment.getExternalStorageDirectory();
	public static final File DOWNLOADS_DIR = Environment.getExternalStoragePublicDirectory(
			Environment.DIRECTORY_DOWNLOADS);
	public static final String PUB_KEY_AUTH_KEY_PATH_OLD =
		HOME_DIR.getAbsolutePath() + "/.ssh/authorized_keys";
	public static final String PUB_KEY_AUTH_KEY_PATH_OLDER =
			HOME_DIR.getAbsolutePath() + "/.ssh/authorized_key.pub";

	public static final HostKeyAlgorithm DEFAULT_HOST_KEY_ALGO = HostKeyAlgorithm.ED_25519;

	public static File homeDirScoped(Context ctxt) {
		return ctxt.getExternalFilesDir(null);
	}
	public static String pubKeyAuthKeyPath(Context ctxt) {
		return homeDirScoped(ctxt).getAbsolutePath() + "/.ssh/authorized_keys";
	}
	public static File quickShareTmpDir(Context ctxt) {
		return new File(homeDirScoped(ctxt), "quick-share");
	}
	public static File rootCopyTmpDir(Context ctxt) {
		return new File(homeDirScoped(ctxt), "root-copy");
	}

	public static File buildTmpDir(Context ctxt, TmpDirType type) {
		File tmpDir = null;
		switch (type) {
			case QUICK_SHARE:
				tmpDir = Defaults.quickShareTmpDir(ctxt);
				break;
			case ROOT_COPY:
				tmpDir = Defaults.rootCopyTmpDir(ctxt);
				break;
		}
		tmpDir.mkdirs();
		UUID uuid = UUID.randomUUID();
		File targetPath = new File(tmpDir, uuid.toString());
		targetPath.mkdir();
		return targetPath;
	}

	public static Intent createDefaultDirPicker(Context ctxt) {
		return createDefaultDirPicker(ctxt, HOME_DIR);
	}

	public static Intent createDefaultDirPicker(Context ctxt, File initialVal) {
		Intent dirPickerIntent = new Intent(ctxt, ResettingFilePickerActivity.class);
		dirPickerIntent.putExtra(FilePickerActivity.EXTRA_ALLOW_MULTIPLE, false);
		dirPickerIntent.putExtra(FilePickerActivity.EXTRA_ALLOW_CREATE_DIR, false);
		dirPickerIntent.putExtra(FilePickerActivity.EXTRA_MODE, FilePickerActivity.MODE_DIR);
		dirPickerIntent.putExtra(FilePickerActivity.EXTRA_START_PATH, initialVal.getAbsolutePath());
		return dirPickerIntent;
	}

	public static Intent createPrefDirPicker(Context ctxt, File initialVal, String prefKey) {
		Intent dirPickerIntent = createDefaultDirPicker(ctxt, initialVal);
		dirPickerIntent.putExtra(AbstractFilePickerActivity.MODE_SAFE_PREFERENCE, prefKey);
		return dirPickerIntent;
	}

	public static Intent createDirAndFilePicker(Context ctxt) {
		Intent intent = new Intent(ctxt, ResettingFilePickerActivity.class);
		intent.putExtra(FilePickerActivity.EXTRA_ALLOW_MULTIPLE, false);
		intent.putExtra(FilePickerActivity.EXTRA_ALLOW_CREATE_DIR, false);
		intent.putExtra(FilePickerActivity.EXTRA_MODE, FilePickerActivity.MODE_FILE_AND_DIR);
		intent.putExtra(FilePickerActivity.EXTRA_START_PATH, HOME_DIR.getAbsolutePath());
		return intent;
	}
}
