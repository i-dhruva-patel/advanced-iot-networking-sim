#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <math.h>
#include "aes.h"

#define PORT 9000
#define BUFFER_SIZE 36
#define AES_KEY_SIZE 16
#define MAX_VALUES 20
#define THRESHOLD 20.0

const uint8_t aes_key[AES_KEY_SIZE] = "mysecretkey12345";

float values[MAX_VALUES];
int value_count = 0;

float calculate_rolling_avg(float new_val) {
    if (value_count < MAX_VALUES) {
        values[value_count++] = new_val;
    } else {
        for (int i = 1; i < MAX_VALUES; ++i)
            values[i - 1] = values[i];
        values[MAX_VALUES - 1] = new_val;
    }
    float sum = 0;
    for (int i = 0; i < value_count; ++i)
        sum += values[i];
    return sum / value_count;
}

uint8_t calculate_crc8(const uint8_t *data, size_t len) {
    uint8_t crc = 0x00;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
    }
    return crc;
}

int main() {
    int sockfd;
    struct sockaddr_in server_addr, client_addr;
    socklen_t addr_len = sizeof(client_addr);
    uint8_t buffer[BUFFER_SIZE];

    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Bind failed");
        return 1;
    }

    printf("🛡️  Secure Hub (C) listening on port %d...\n", PORT);

    while (1) {
        ssize_t len = recvfrom(sockfd, buffer, BUFFER_SIZE, 0,
                               (struct sockaddr *)&client_addr, &addr_len);
        if (len != BUFFER_SIZE) {
            printf("⚠️  Unexpected packet size: %ld bytes\n", len);
            continue;
        }

        // Extract fields from Python packet
        uint8_t header = buffer[0];
        uint8_t node_id = buffer[1];
        uint8_t sensor_type = buffer[2];
        uint8_t iv[16];
        uint8_t ciphertext[16];
        memcpy(iv, buffer + 3, 16);
        memcpy(ciphertext, buffer + 19, 16);
        uint8_t recv_crc = buffer[35];

        // Compute CRC8 over first 35 bytes
        uint8_t calc_crc = calculate_crc8(buffer, 35);
        if (calc_crc != recv_crc) {
            printf("❌ CRC mismatch for Node %d\n", node_id);
            continue;
        }

        // Decrypt
        struct AES_ctx ctx;
        AES_init_ctx_iv(&ctx, aes_key, iv);
        uint8_t decrypted[16];
        memcpy(decrypted, ciphertext, 16);
        AES_CBC_decrypt_buffer(&ctx, decrypted, 16);

        float value;
        memcpy(&value, decrypted, sizeof(float));

        float avg = calculate_rolling_avg(value);
        printf("✅ Node %d | Value = %.2f°C | Rolling Avg = %.2f°C | CRC OK\n",
               node_id, value, avg);

        if (fabs(value - avg) > THRESHOLD) {
            printf("🚨 Anomaly Detected! Node %d | Value = %.2f°C (Avg = %.2f°C)\n",
                   node_id, value, avg);
        }
    }

    close(sockfd);
    return 0;
}

