#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <stdint.h>
#include <arpa/inet.h>
#include <sys/socket.h>

#include "tiny-AES-c/aes.h"

#define SERVER_PORT 9000
#define SERVER_IP "127.0.0.1"
#define AES_KEYLEN 16
#define IV_SIZE 16
#define PAYLOAD_SIZE 16
#define PACKET_SIZE 36

#define HEADER_BYTE 0xAA
#define SENSOR_TYPE_TEMP 0x01

const uint8_t aes_key[AES_KEYLEN] = "mysecretkey12345";  // Must match hub

// Generate 16-byte random IV
void generate_random_iv(uint8_t* iv, size_t len) {
    for (size_t i = 0; i < len; ++i) {
        iv[i] = rand() % 256;
    }
}

// Pad float value to 16 bytes using PKCS#7 padding
void pad_float(float value, uint8_t* out) {
    memcpy(out, &value, sizeof(float));
    uint8_t pad_len = 16 - sizeof(float);
    for (int i = sizeof(float); i < 16; i++) {
        out[i] = pad_len;
    }
}

// Calculate CRC (simple XOR of all bytes)
uint8_t calculate_crc(uint8_t* data, size_t len) {
    uint8_t crc = 0;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
    }
    return crc;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printf("Usage: %s <node_id>\n", argv[0]);
        return 1;
    }

    int node_id = atoi(argv[1]);
    srand(time(NULL) + node_id);

    printf("🌡️ Secure Sensor Node %d starting...\n", node_id);

    // UDP socket setup
    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("socket");
        return 1;
    }

    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &server_addr.sin_addr);

    while (1) {
        float temperature = (rand() % 10000) / 100.0f; // 0.00°C to 99.99°C
        uint8_t iv[IV_SIZE];
        uint8_t plaintext[PAYLOAD_SIZE];
        uint8_t ciphertext[PAYLOAD_SIZE];
        uint8_t packet[PACKET_SIZE];

        // Prepare secure payload
        generate_random_iv(iv, IV_SIZE);
        pad_float(temperature, plaintext);

        // Encrypt
        struct AES_ctx ctx;
        AES_init_ctx_iv(&ctx, aes_key, iv);
        memcpy(ciphertext, plaintext, PAYLOAD_SIZE);
        AES_CBC_encrypt_buffer(&ctx, ciphertext, PAYLOAD_SIZE);

        // Construct packet
        packet[0] = HEADER_BYTE;
        packet[1] = (uint8_t)node_id;
        packet[2] = SENSOR_TYPE_TEMP;
        memcpy(&packet[3], iv, IV_SIZE);              // 3–18
        memcpy(&packet[19], ciphertext, PAYLOAD_SIZE); // 19–34

        // CRC
        packet[35] = calculate_crc(packet, 35);

        // Send
        sendto(sockfd, packet, PACKET_SIZE, 0, (struct sockaddr*)&server_addr, sizeof(server_addr));

        printf("🔐 Sent encrypted temp = %.2f°C\n", temperature);
        usleep(1000000); // 1 sec delay
    }

    close(sockfd);
    return 0;
}

