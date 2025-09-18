package ca.bc.gov.asago;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(KeycloakPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
