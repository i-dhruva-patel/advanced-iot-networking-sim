typedef struct {
    uint8_t header;       // 0xAA
    uint8_t node_id;      // unique for each
    uint8_t type;         // 0x01 for temp
    float payload;        // temp value
    uint8_t crc;          // basic XOR
} SensorPacket;
