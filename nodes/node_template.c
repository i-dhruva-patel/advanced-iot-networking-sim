#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <arpa/inet.h>

#define HUB_IP "127.0.0.1"
#define HUB_PORT 9000
#define HEADER_BYTE 0xAA
#define SENSOR_TYPE_TEMP 0x01

typedef struct {
    uint8_t header;
    uint8_t node_id;
    uint8_t type;
    float payload;
    uint8_t crc;
} SensorPacket;

// XOR-based dummy checksum
uint8_t calculate_crc(SensorPacket *pkt) {
    uint8_t *raw = (uint8_t*) pkt;
    uint8_t crc = 0;
    for (int i = 0; i < sizeof(SensorPacket) - 1; i++) {
        crc ^= raw[i];
    }
    return crc;
}

float generate_fake_temp() {
    return (rand() % 1000) / 10.0f;  // 0.0 to 99.9 °C
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <node_id>\n", argv[0]);
        return 1;
    }

    uint8_t node_id = atoi(argv[1]);
    srand(time(NULL) + node_id); // unique randomness per node

    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("socket failed");
        return 1;
    }

    struct sockaddr_in hub_addr;
    hub_addr.sin_family = AF_INET;
    hub_addr.sin_port = htons(HUB_PORT);
    inet_pton(AF_INET, HUB_IP, &hub_addr.sin_addr);

    printf("🌡️ Sensor Node %d starting...\n", node_id);

    while (1) {
        SensorPacket pkt;
        pkt.header = HEADER_BYTE;
        pkt.node_id = node_id;
        pkt.type = SENSOR_TYPE_TEMP;
        pkt.payload = generate_fake_temp();
        pkt.crc = calculate_crc(&pkt);

        sendto(sockfd, &pkt, sizeof(pkt), 0,
               (struct sockaddr*)&hub_addr, sizeof(hub_addr));

        printf("📤 Node %d sent: Temp = %.1f°C, CRC = 0x%02X\n",
               node_id, pkt.payload, pkt.crc);

        sleep(2);  // send every 2 seconds
    }

    close(sockfd);
    return 0;
}

