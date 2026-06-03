def write_large_block(file):
    large_block = """
typedef int[-1,65535] id_t;

typedef struct {
    int32_t x;
    int32_t y;
}ST_IPOINT;

typedef struct {
    double x;
    double y;
}ST_DPOINT;

typedef struct {
    ST_IPOINT ends[2];
}ST_DLINE;

typedef struct {
    ST_IPOINT points[MAXP];
    bool dashLine;
}ST_BOUND;

typedef struct {
    id_t ID;
    ST_BOUND left;
    ST_BOUND right;
    id_t predecessor[MAXPRE];
    id_t successor[MAXSUC];
    id_t adjLeft;
    bool dirLeft;
    id_t adjRight;
    bool dirRight;
}ST_LANE;

typedef struct {
    bool collide; // collision
    bool outside; // outside road
    bool reach;   // reach the goal
}ST_DETECTION;

typedef struct {
    ST_DPOINT position;
    double velocity;
    double orientation;
    double acceleration;
    double accRate;
    double yawRate;
}ST_DSTATE;

typedef struct {
    ST_IPOINT position;
    int32_t velocity;
    int32_t orientation;
    int32_t acceleration;
    int32_t accRate;
    int32_t yawRate;
    ST_DETECTION detection;
}ST_ISTATE;

typedef struct {
    hybrid clock x;
    hybrid clock y;
    hybrid clock velocity;
    hybrid clock orientation;
    hybrid clock acceleration;
    //hybrid clock accRate;
    //hybrid clock yawRate;
}ST_DYNAMICS;

typedef struct {
    ST_IPOINT center;
    int32_t width;
    int32_t length;
    int32_t orientation;
}ST_RECTANGLE;

typedef struct {
    int32_t maxVelocity;
    int32_t minVelocity;
    int32_t maxOrientation;
    int32_t minOrientation;
}ST_RULES;

typedef struct {
    ST_IPOINT goal;
}ST_PLANNING;

typedef struct {
    int32_t time;
    ST_DSTATE dState;
}ST_PAIR;

typedef struct {
    int32_t vMin;
    int32_t vMax;
    int32_t accMax;
    int32_t decMax;
    int32_t laneChangeProb;
    int32_t cutInRange;
    int32_t initialLane;
}ST_OBEHAVIOR;
"""
    file.write(large_block)