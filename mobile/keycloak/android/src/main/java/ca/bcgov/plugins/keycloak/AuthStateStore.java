package ca.bcgov.plugins.keycloak;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;
import android.util.Log;
import androidx.annotation.Nullable;
import androidx.datastore.preferences.core.MutablePreferences;
import androidx.datastore.preferences.core.Preferences;
import androidx.datastore.preferences.core.PreferencesKeys;
import androidx.datastore.preferences.rxjava3.RxPreferenceDataStoreBuilder;
import androidx.datastore.rxjava3.RxDataStore;
import com.google.crypto.tink.Aead;
import com.google.crypto.tink.KeyTemplates;
import com.google.crypto.tink.RegistryConfiguration;
import com.google.crypto.tink.aead.AeadConfig;
import com.google.crypto.tink.integration.android.AndroidKeysetManager;
import io.reactivex.rxjava3.core.Single;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.GeneralSecurityException;

class AuthStateStore {

    private static final String TAG = "Keycloak";
    private static final String DATASTORE_NAME = "keycloak_auth_state";
    private static final String KEY_AUTH_STATE = "auth_state";
    private static final String LEGACY_PREFS_NAME = "KeycloakAuthState";
    private static final String TINK_KEYSET_NAME = "keycloak_auth_state_keyset";
    private static final String TINK_KEYSET_PREFS_NAME = "keycloak_auth_state_keyset_prefs";
    private static final String MASTER_KEY_URI = "android-keystore://keycloak_auth_state_master_key";
    private static final Preferences.Key<String> AUTH_STATE_KEY = PreferencesKeys.stringKey(KEY_AUTH_STATE);
    private static final Object DATASTORE_LOCK = new Object();

    private static RxDataStore<Preferences> dataStore;

    private final Context context;
    private final Aead aead;

    AuthStateStore(Context context) throws GeneralSecurityException, IOException {
        this.context = context.getApplicationContext();
        AeadConfig.register();
        this.aead = new AndroidKeysetManager.Builder()
            .withSharedPref(this.context, TINK_KEYSET_NAME, TINK_KEYSET_PREFS_NAME)
            .withKeyTemplate(KeyTemplates.get("AES256_GCM"))
            .withMasterKeyUri(MASTER_KEY_URI)
            .build()
            .getKeysetHandle()
            .getPrimitive(RegistryConfiguration.get(), Aead.class);
        getDataStore(this.context);
    }

    @Nullable
    String read() {
        try {
            Preferences preferences = getDataStore(context).data().firstOrError().blockingGet();
            String encryptedState = preferences.get(AUTH_STATE_KEY);

            if (encryptedState != null) {
                try {
                    return decrypt(encryptedState);
                } catch (GeneralSecurityException | IllegalArgumentException e) {
                    Log.e(TAG, "Failed to decrypt stored auth state", e);
                    clear();
                    return null;
                }
            }

            String legacyState = readLegacyAuthState();
            if (legacyState != null && write(legacyState)) {
                clearLegacyAuthState();
                Log.d(TAG, "Migrated auth state to encrypted DataStore");
            }
            return legacyState;
        } catch (Exception e) {
            Log.e(TAG, "Failed to read auth state from encrypted DataStore", e);
            return null;
        }
    }

    boolean write(String stateJson) {
        try {
            String encryptedState = encrypt(stateJson);
            getDataStore(context)
                .updateDataAsync(preferences -> {
                    MutablePreferences mutablePreferences = preferences.toMutablePreferences();
                    mutablePreferences.set(AUTH_STATE_KEY, encryptedState);
                    return Single.just(mutablePreferences);
                })
                .blockingGet();
            Log.d(TAG, "Auth state persisted to encrypted DataStore");
            return true;
        } catch (Exception e) {
            Log.e(TAG, "Failed to persist auth state to encrypted DataStore", e);
            return false;
        }
    }

    void clear() {
        try {
            getDataStore(context)
                .updateDataAsync(preferences -> {
                    MutablePreferences mutablePreferences = preferences.toMutablePreferences();
                    mutablePreferences.remove(AUTH_STATE_KEY);
                    return Single.just(mutablePreferences);
                })
                .blockingGet();
        } catch (Exception e) {
            Log.e(TAG, "Failed to clear encrypted auth state", e);
        }
        clearLegacyAuthState();
    }

    private static RxDataStore<Preferences> getDataStore(Context context) {
        synchronized (DATASTORE_LOCK) {
            if (dataStore == null) {
                dataStore = new RxPreferenceDataStoreBuilder(context, DATASTORE_NAME).build();
            }
            return dataStore;
        }
    }

    private String encrypt(String stateJson) throws GeneralSecurityException {
        byte[] ciphertext = aead.encrypt(stateJson.getBytes(StandardCharsets.UTF_8), associatedData());
        return Base64.encodeToString(ciphertext, Base64.NO_WRAP);
    }

    private String decrypt(String encryptedState) throws GeneralSecurityException {
        byte[] ciphertext = Base64.decode(encryptedState, Base64.NO_WRAP);
        byte[] plaintext = aead.decrypt(ciphertext, associatedData());
        return new String(plaintext, StandardCharsets.UTF_8);
    }

    private byte[] associatedData() {
        return (context.getPackageName() + ":" + DATASTORE_NAME + ":" + KEY_AUTH_STATE).getBytes(
            StandardCharsets.UTF_8
        );
    }

    @Nullable
    private String readLegacyAuthState() {
        return context.getSharedPreferences(LEGACY_PREFS_NAME, Context.MODE_PRIVATE).getString(KEY_AUTH_STATE, null);
    }

    private void clearLegacyAuthState() {
        SharedPreferences preferences = context.getSharedPreferences(LEGACY_PREFS_NAME, Context.MODE_PRIVATE);
        preferences.edit().remove(KEY_AUTH_STATE).apply();
    }
}
