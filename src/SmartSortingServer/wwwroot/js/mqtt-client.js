// MQTT 메시지를 받아서 dashboard-live.js 함수 호출

console.log('mqtt-client.js 로드됨');
console.log('MQTT.js 로드 여부:', typeof mqtt !== 'undefined');

const MQTT_BROKER_URL = window.location.protocol === 'https:'
    ? `wss://${window.location.hostname}:9001`
    : `ws://${window.location.hostname}:9001`;

const client = mqtt.connect(
    MQTT_BROKER_URL,
    {
        username: "root",
        password: "mqtt123456",

        clientId:
            "AdminWeb_"
            + Math.random().toString(16).slice(2),

        reconnectPeriod: 1000
    }
);

client.on("connect", () => {
    console.log("MQTT 연결 성공");

    client.subscribe(
        "smart_sorting/production/status"
    );

    client.subscribe(
        "smart_sorting/alert"
    );

    client.subscribe(
        "smart_sorting/component/status"
    );

    client.subscribe(
        "smart_sorting/product/detection"
    );
});

client.on("message", (topic, message) => {
    let data;

    try {
        data = JSON.parse(message.toString());
    } catch (error) {
        console.error("MQTT 메시지 JSON 파싱 실패:", error);
        return;
    }

    console.log("Topic:", topic);
    console.log("Data:", data);

    if (
        topic
        === "smart_sorting/production/status"
    ) {
        console.log("생산 현황:", data);
        if (typeof refreshDashboardSummary === 'function') {
            refreshDashboardSummary();
        } else if (typeof updateProductionStatus === 'function') {
            updateProductionStatus(data);
        }
        if (typeof refreshDashboardCharts === 'function') {
            refreshDashboardCharts();
        }
    }

    else if (topic === 'smart_sorting/alert') {
        console.log('알림:', data);
        if (typeof prependAlert === 'function') {
            prependAlert(data);
        }
        if (typeof handleAlertsPageMqttAlert === 'function') {
            handleAlertsPageMqttAlert(data);
        }
    }
    
    else if (
    topic
    === "smart_sorting/component/status"
        ) {
        console.log("장비 상태:", data);
        if (typeof updateComponentStatus === 'function') {
            updateComponentStatus(data);
        }
    }

    else if (
        topic === "smart_sorting/product/detection"
    ) {
        console.log("제품 감지:", data);
        if (typeof prependRecentProductDetection === 'function') {
            prependRecentProductDetection(data);
        }
    }
});

client.on("error", (error) => {
    console.error(
        "MQTT 연결 오류:",
        error
    );
});
