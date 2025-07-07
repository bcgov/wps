package ca.bcgov.plugins.keycloak;

import android.util.Log;

public class Keycloak {

    public String echo(String value) {
        Log.i("Echo", value);
        return value;
    }
}
