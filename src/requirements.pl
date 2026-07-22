app(weatherApp, [weatherMonitor]).
securityRequirements(weatherMonitor, N) :-
    (anti_tampering(N) ; access_control(N)),
    (wireless_security(N) ; iot_data_encryption(N)).

%%% Trust: appOp si fida direttamente di cloudOp e edgeOp
1.0::trusts(appOp, cloudOp).
1.0::trusts(appOp, edgeOp).