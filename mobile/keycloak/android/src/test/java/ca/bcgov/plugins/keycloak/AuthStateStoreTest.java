package ca.bcgov.plugins.keycloak;

import static org.junit.Assert.*;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.datastore.preferences.core.Preferences;
import androidx.datastore.preferences.core.PreferencesKeys;
import androidx.datastore.rxjava3.RxDataStore;
import androidx.test.core.app.ApplicationProvider;
import java.lang.reflect.Field;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 23, manifest = Config.NONE)
public class AuthStateStoreTest {

    private static final String KEY_AUTH_STATE = "auth_state";
    private static final String LEGACY_PREFS_NAME = "KeycloakAuthState";
    private static final Preferences.Key<String> AUTH_STATE_KEY = PreferencesKeys.stringKey(KEY_AUTH_STATE);

    private Context context;
    private AuthStateStore store;

    @Before
    public void setUp() throws Exception {
        context = ApplicationProvider.getApplicationContext();
        store = new AuthStateStore(context);
        store.clear();
        legacyPreferences().edit().clear().commit();
    }

    @Test
    public void testWriteAndRead_roundTripsAuthState() throws Exception {
        String stateJson = "{\"authorized\":true,\"refreshToken\":\"refresh-token\"}";

        assertTrue(store.write(stateJson));

        assertEquals(stateJson, store.read());
    }

    @Test
    public void testWrite_storesEncryptedAuthState() throws Exception {
        String stateJson = "{\"authorized\":true,\"refreshToken\":\"refresh-token\"}";

        assertTrue(store.write(stateJson));

        String rawStoredValue = getRawStoredValue();
        assertNotNull(rawStoredValue);
        assertNotEquals(stateJson, rawStoredValue);
    }

    @Test
    public void testRead_migratesLegacyAuthState() throws Exception {
        String legacyStateJson = "{\"authorized\":true,\"refreshToken\":\"legacy-refresh-token\"}";
        legacyPreferences().edit().putString(KEY_AUTH_STATE, legacyStateJson).commit();

        assertEquals(legacyStateJson, store.read());

        assertNull(legacyPreferences().getString(KEY_AUTH_STATE, null));
        assertEquals(legacyStateJson, store.read());
    }

    @Test
    public void testClear_removesStoredAndLegacyAuthState() throws Exception {
        String stateJson = "{\"authorized\":true,\"refreshToken\":\"refresh-token\"}";
        assertTrue(store.write(stateJson));
        legacyPreferences().edit().putString(KEY_AUTH_STATE, stateJson).commit();

        store.clear();

        assertNull(store.read());
        assertNull(legacyPreferences().getString(KEY_AUTH_STATE, null));
    }

    private SharedPreferences legacyPreferences() {
        return context.getSharedPreferences(LEGACY_PREFS_NAME, Context.MODE_PRIVATE);
    }

    @SuppressWarnings("unchecked")
    private String getRawStoredValue() throws Exception {
        Field dataStoreField = AuthStateStore.class.getDeclaredField("dataStore");
        dataStoreField.setAccessible(true);
        RxDataStore<Preferences> dataStore = (RxDataStore<Preferences>) dataStoreField.get(null);
        Preferences preferences = dataStore.data().firstOrError().blockingGet();
        return preferences.get(AUTH_STATE_KEY);
    }
}
