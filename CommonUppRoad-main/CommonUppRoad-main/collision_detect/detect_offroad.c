#include <stdio.h>
#include <math.h>
#include <stdint.h>
#include <stdbool.h>

#define MAXP 22
#define NONE -1
#define MAXL 20
#define MAXSO 1
#define MAXPRE 1
#define MAXSUC 1
#define SCALE 10000.0 // scale from int to double: 100 = 1.0

typedef int id_t;

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

double i2d(const int32_t i) {
    double v = i/SCALE;
    return v;
}

int32_t d2i(const double i) {
    int32_t v = rint(i*SCALE);
    return v;
}

int32_t min(const int32_t v1, const int32_t v2){
    return v1 < v2? v1:v2;
}

int32_t max(const int32_t v1, const int32_t v2){
    return v1 > v2? v1:v2;
}

// Function to calculate the corner points of a rectangle
void calculateCornerPoints(ST_RECTANGLE veh_state, ST_IPOINT corners[]) {
    double halfLength = i2d(veh_state.length)/2.0;
    double halfWidth = i2d(veh_state.width)/2.0;
    double angle = i2d(veh_state.orientation);

    // Calculate the coordinates of each corner point based on the center, length, width, and orientation
    corners[0].x = d2i(i2d(veh_state.center.x) + halfLength*cos(angle) - halfWidth*sin(angle));
    corners[0].y = d2i(i2d(veh_state.center.y) + halfLength*sin(angle) + halfWidth*cos(angle));

    corners[1].x = d2i(i2d(veh_state.center.x) + halfLength*cos(angle) + halfWidth*sin(angle));
    corners[1].y = d2i(i2d(veh_state.center.y) + halfLength*sin(angle) - halfWidth*cos(angle));

    corners[2].x = d2i(i2d(veh_state.center.x) - halfLength*cos(angle) + halfWidth*sin(angle));
    corners[2].y = d2i(i2d(veh_state.center.y) - halfLength*sin(angle) - halfWidth*cos(angle));

    corners[3].x = d2i(i2d(veh_state.center.x) - halfLength*cos(angle) - halfWidth*sin(angle));
    corners[3].y = d2i(i2d(veh_state.center.y) - halfLength*sin(angle) + halfWidth*cos(angle));
}

// Function to count non-zero elements in a 2D array
int check_pts_num(const ST_IPOINT lane_pts[MAXP]) {
    uint16_t count = 0;
    // NONE or 0?
    while (count < MAXP && (lane_pts[count].x != NONE || lane_pts[count].y != NONE)){
        count++;
    }
    return count;
}

// Checking if a point is inside a polygon
bool point_in_polygon(ST_IPOINT point, ST_IPOINT polygon[])
{
    int num_vertices = 4, i = 0;
    int32_t x = point.x;
    int32_t y = point.y;
    double x_intersection;
    bool inside = false;
 
    // Store the first point in the polygon and initialize
    // the second point
    ST_IPOINT p1 = polygon[0], p2;
 
    // Loop through each edge in the polygon
    for (i = 1; i <= num_vertices; i++) {
        // Get the next point in the polygon
        p2 = polygon[i % num_vertices];
 
        // Check if the point is above the minimum y
        // coordinate of the edge
        if (y > min(p1.y, p2.y)) {
            // Check if the point is below the maximum y
            // coordinate of the edge
            if (y <= max(p1.y, p2.y)) {
                // Check if the point is to the left of the
                // maximum x coordinate of the edge
                if (x <= max(p1.x, p2.x)) {
                    // Calculate the x-intersection of the
                    // line connecting the point to the edge
                    x_intersection = (y - p1.y) * (p2.x - p1.x)/(p2.y - p1.y) + p1.x;
 
                    // Check if the point is on the same
                    // line as the edge or to the left of
                    // the x-intersection
                    if (p1.x == p2.x || x <= x_intersection) {
                        // Flip the inside flag
                        inside = !inside;
                    }
                }
            }
        }
 
        // Store the current point as the first point for
        // the next iteration
        p1 = p2;
    }
 
    // Return the value of the inside flag
    return inside;
}


// check if veh_state are not covered by a single lane, or if vehicle rectangle touches the edge of the lane
uint8_t check_inlane_lane_single(const ST_LANE lane, ST_RECTANGLE veh_state, ST_IPOINT veh_corners[], ST_IPOINT box_corners[]) {
    uint8_t num_box = 0;
    uint8_t i_box = 0, i_veh = 0;
    uint8_t inlane_pts_num = 0;

    //ST_IPOINT veh_corners[4];
    //ST_IPOINT box_corners[4];
    // Calculate the corner points
    calculateCornerPoints(veh_state, veh_corners);

    // check the number of points in the lane
    num_box = check_pts_num(lane.left.points) - 1;
    for (i_box = 0; i_box < num_box && inlane_pts_num < 4; i_box++){
        // define the corner of the road box
        box_corners[0] = lane.right.points[i_box];
        box_corners[1] = lane.right.points[i_box + 1];
        box_corners[2] = lane.left.points[i_box + 1];
        box_corners[3] = lane.left.points[i_box];
        // check if the inlane status of the vehicle box to the current box
        // inlane_pts_num += check_coverage(box_corners, veh_corners);   
        for(i_veh = 0; i_veh < 4; i_veh++){
            if(point_in_polygon(veh_corners[i_veh],box_corners)){
                inlane_pts_num++;
            }
        }   
    }

    return inlane_pts_num;
}

bool check_inlane_laneNet(const ST_LANE laneNet[], const ST_RECTANGLE veh_state, int *lane, ST_IPOINT veh_corners[], ST_IPOINT box_corners[]) {
    uint8_t i_lane = 0, inlane_pts_num = 0;
    bool inside = false;

    for(i_lane = 0; i_lane < MAXL && inlane_pts_num < 4; i_lane++){
        inlane_pts_num += check_inlane_lane_single(laneNet[i_lane], veh_state, veh_corners, box_corners);
    }
    
    if(inlane_pts_num >= 4) {
        inside = true;
    }
    else {
        inside = false;
    }

    return inside;
}


int main() {
    const ST_BOUND leftLane1 = {{{-864415, 77473}, {-640253, 64078}, {-629739, 63235}, {-409995, 45614}, {-406464, 45330}, {-200958, 29011}, {-9709, 19898}, {241981, 14901}, {482161, 25682}, {552906, 29476}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane1 = {{{-872272, 16101}, {-641354, 11278}, {-633918, 11124}, {-413426, 2830}, {-409705, 2549}, {-203016, -13106}, {-10476, -17092}, {240565, -25808}, {482819, -22561}, {559920, -22592}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane1 = {49564, leftLane1, rightLane1, {NONE, NONE, NONE}, {49586, 49594, 49602}, 49566, false, NONE, false};

const ST_BOUND leftLane2 = {{{552906, 29476}, {482161, 25682}, {477170, 25459}, {243636, 14975}, {-8651, 19877}, {-199635, 28948}, {-405165, 45227}, {-640253, 64078}, {-864415, 77473}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane2 = {{{558084, 78427}, {477384, 69663}, {475195, 69426}, {241830, 55203}, {-7940, 55666}, {-197765, 68171}, {-402039, 84608}, {-636253, 106625}, {-860982, 127752}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane2 = {49566, leftLane2, rightLane2, {49584, 49588, 49600}, {NONE, NONE, NONE}, 49564, false, NONE, false};

const ST_BOUND leftLane3 = {{{690323, -90079}, {684545, -228035}, {678717, -364879}, {674875, -480822}, {661521, -771729}, {643769, -972417}, {593600, -1414287}, {563045, -1638390}, {549506, -1745266}, {544126, -1800925}, {534827, -1851339}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane3 = {{{655306, -88577}, {650213, -226770}, {643699, -363392}, {639849, -479560}, {625605, -769508}, {606345, -968800}, {558516, -1410303}, {529717, -1633829}, {515339, -1740971}, {508233, -1797711}, {495244, -1837887}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane3 = {49568, leftLane3, rightLane3, {49586, 49590, 49596}, {NONE, NONE, NONE}, 49570, false, NONE, false};

const ST_BOUND leftLane4 = {{{534827, -1851339}, {538799, -1831487}, {543488, -1808052}, {546018, -1779800}, {548131, -1756201}, {560625, -1656818}, {591988, -1426907}, {643038, -978852}, {661215, -775192}, {674875, -480822}, {678707, -365206}, {684509, -228836}, {690323, -90079}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane4 = {{{574905, -1871005}, {578100, -1839350}, {581024, -1812075}, {584117, -1783211}, {586929, -1761144}, {599595, -1661716}, {627835, -1431813}, {679229, -982961}, {699201, -778553}, {709901, -482085}, {713736, -366367}, {717357, -230234}, {726123, -95889}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane4 = {49570, leftLane4, rightLane4, {NONE, NONE, NONE}, {49580, 49588, 49598}, 49568, false, NONE, false};

const ST_BOUND leftLane5 = {{{823071, 66800}, {950017, 53801}, {960293, 52834}, {1143261, 35613}, {1147143, 35247}, {1402999, 2132}, {1599413, -27667}, {1604353, -28417}, {1970149, -81782}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane5 = {{{813691, 19386}, {947878, 12447}, {956450, 12004}, {1139500, -4348}, {1141938, -4666}, {1397800, -38035}, {1593983, -63421}, {1599119, -64173}, {1966374, -117932}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane5 = {49572, leftLane5, rightLane5, {49580, 49592, 49602}, {NONE, NONE, NONE}, 49574, false, NONE, false};

const ST_BOUND leftLane6 = {{{1970149, -81782}, {1605646, -28605}, {1404373, 1950}, {1147143, 35247}, {951512, 53660}, {823071, 66800}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane6 = {{{1974864, -44146}, {1610725, 6199}, {1409959, 38734}, {1152207, 73161}, {955348, 94414}, {831092, 109435}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane6 = {49574, leftLane6, rightLane6, {NONE, NONE, NONE}, {49582, 49590, 49600}, 49572, false, NONE, false};

const ST_BOUND leftLane7 = {{{680586, 192900}, {671791, 414953}, {661654, 684507}, {647516, 1025033}, {638968, 1175336}, {632317, 1293039}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane7 = {{{714785, 197663}, {703356, 416601}, {692326, 685763}, {680398, 1026183}, {669929, 1177096}, {665153, 1295975}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane7 = {49576, leftLane7, rightLane7, {49582, 49594, 49598}, {NONE, NONE, NONE}, 49578, false, NONE, false};

const ST_BOUND leftLane8 = {{{632317, 1293039}, {638523, 1183199}, {647516, 1025033}, {661568, 686556}, {671657, 418526}, {680586, 192900}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane8 = {{{598344, 1290613}, {604458, 1181275}, {613724, 1023054}, {629663, 685231}, {638723, 417288}, {650366, 193859}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane8 = {49578, leftLane8, rightLane8, {NONE, NONE, NONE}, {49584, 49592, 49596}, 49576, false, NONE, false};

const ST_BOUND leftLane9 = {{{690323, -90079}, {691107, -70890}, {692074, -60413}, {692504, -55751}, {693152, -48880}, {694177, -38037}, {694572, -33852}, {697767, -19526}, {698997, -14008}, {702324, -4406}, {703357, -1424}, {708249, 9311}, {714366, 17635}, {718873, 23766}, {731603, 34626}, {735311, 37142}, {746095, 44456}, {760047, 53920}, {769128, 56565}, {788178, 62115}, {823071, 66800}, {NONE, NONE}}, false};
const ST_BOUND rightLane9 = {{{726123, -95889}, {728496, -75171}, {729787, -63893}, {730094, -62064}, {731697, -52521}, {733829, -45042}, {734734, -41867}, {739133, -28750}, {739133, -28750}, {742088, -23585}, {744666, -19079}, {747932, -13362}, {750477, -8908}, {752256, -6977}, {759731, 1139}, {759731, 1139}, {770698, 8183}, {776387, 10315}, {781991, 12415}, {798317, 16005}, {813691, 19386}, {NONE, NONE}}, false};
const ST_LANE lane9 = {49580, leftLane9, rightLane9, {49570, NONE, NONE}, {49572, NONE, NONE}, 49590, false, NONE, false};

const ST_BOUND leftLane10 = {{{823071, 66800}, {801763, 65844}, {781671, 64943}, {768946, 64372}, {759608, 66059}, {751703, 67487}, {734672, 73494}, {728226, 77880}, {713379, 87983}, {708435, 93473}, {698587, 104408}, {692630, 121658}, {689545, 130592}, {686964, 138066}, {685408, 151442}, {680586, 192900}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane10 = {{{831092, 109435}, {799665, 112614}, {779488, 113615}, {779488, 113615}, {768826, 117083}, {768826, 117083}, {757842, 121402}, {757842, 121402}, {747516, 128670}, {747516, 128670}, {738399, 137463}, {735805, 140164}, {731186, 144972}, {725147, 156063}, {725147, 156063}, {714785, 197663}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane10 = {49582, leftLane10, rightLane10, {49574, NONE, NONE}, {49576, NONE, NONE}, 49592, false, NONE, false};

const ST_BOUND leftLane11 = {{{680586, 192900}, {681921, 164564}, {682636, 149404}, {680149, 131127}, {677582, 121050}, {675778, 113965}, {667824, 96744}, {659892, 84499}, {658006, 81586}, {650463, 70081}, {646591, 65058}, {640447, 57089}, {626565, 46857}, {612252, 39538}, {588527, 35120}, {586586, 34759}, {552906, 29476}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane11 = {{{650366, 193859}, {643874, 162773}, {643874, 162773}, {643874, 162773}, {631412, 132810}, {631412, 132810}, {631412, 132810}, {616916, 112337}, {616916, 112337}, {616916, 112337}, {602864, 100040}, {602092, 99365}, {599977, 98272}, {585698, 90888}, {578805, 87323}, {566321, 81963}, {558084, 78427}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane11 = {49584, leftLane11, rightLane11, {49578, NONE, NONE}, {49566, NONE, NONE}, 49594, false, NONE, false};

const ST_BOUND leftLane12 = {{{552906, 29476}, {581875, 30935}, {599004, 31798}, {616853, 28701}, {633049, 25890}, {643266, 20106}, {661136, 9990}, {668107, 659}, {673512, -6574}, {678240, -12902}, {684277, -20982}, {690444, -49336}, {690444, -49336}, {690444, -49336}, {690468, -41185}, {690323, -90079}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane12 = {{{559920, -22592}, {584521, -21578}, {596144, -22193}, {607914, -22817}, {618156, -24248}, {618156, -24248}, {628753, -28745}, {632037, -31072}, {636496, -34232}, {641423, -40411}, {643596, -44217}, {646444, -49205}, {650352, -58339}, {650475, -58628}, {653026, -68487}, {655306, -88577}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane12 = {49586, leftLane12, rightLane12, {49564, NONE, NONE}, {49568, NONE, NONE}, 49588, false, NONE, false};

const ST_BOUND leftLane13 = {{{690323, -90079}, {690391, -67267}, {690468, -41185}, {690468, -41185}, {690468, -41185}, {684277, -20982}, {684277, -20982}, {684277, -20982}, {671285, -3592}, {661400, 9637}, {661136, 9990}, {661136, 9990}, {643934, 19729}, {635286, 24624}, {633049, 25890}, {633049, 25890}, {633049, 25890}, {615315, 28968}, {603188, 31072}, {599004, 31798}, {589557, 31322}, {552906, 29476}}, false};
const ST_BOUND rightLane13 = {{{726123, -95889}, {727161, -67376}, {727719, -42004}, {727817, -37539}, {725293, -20918}, {723121, -11763}, {721732, -5911}, {716705, 9620}, {708696, 24360}, {698750, 37545}, {694270, 42159}, {685274, 51425}, {670017, 65801}, {667848, 67611}, {662260, 72271}, {650196, 78720}, {634245, 84137}, {625190, 85877}, {612816, 86560}, {594243, 84894}, {586891, 84235}, {558084, 78427}}, false};
const ST_LANE lane13 = {49588, leftLane13, rightLane13, {49570, NONE, NONE}, {49566, NONE, NONE}, 49586, false, NONE, false};

const ST_BOUND leftLane14 = {{{823071, 66800}, {788178, 62115}, {788178, 62115}, {765986, 55650}, {760047, 53920}, {759072, 53258}, {744188, 43164}, {732280, 35086}, {731603, 34626}, {718873, 23766}, {713270, 16143}, {708249, 9311}, {704125, 260}, {703357, -1424}, {701256, -7490}, {698997, -14008}, {698665, -15498}, {694572, -33852}, {692811, -52497}, {692504, -55751}, {691107, -70890}, {690323, -90079}}, false};
const ST_BOUND rightLane14 = {{{831092, 109435}, {789538, 110600}, {775745, 110986}, {752345, 102471}, {737983, 94701}, {732847, 91922}, {718542, 80976}, {708160, 70645}, {699813, 60315}, {689475, 47522}, {682435, 38809}, {676880, 30638}, {670341, 21022}, {667554, 16921}, {662886, 5805}, {660555, -1179}, {658747, -6596}, {656341, -29905}, {654564, -56632}, {654564, -56632}, {654383, -48868}, {655306, -88577}}, false};
const ST_LANE lane14 = {49590, leftLane14, rightLane14, {49574, NONE, NONE}, {49568, NONE, NONE}, 49580, false, NONE, false};

const ST_BOUND leftLane15 = {{{680586, 192900}, {686964, 138066}, {697681, 107029}, {710007, 91728}, {713379, 87983}, {719314, 83945}, {734672, 73494}, {751703, 67487}, {764536, 65169}, {768946, 64372}, {823071, 66800}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane15 = {{{650366, 193859}, {653338, 136329}, {657415, 99076}, {676063, 61158}, {682143, 55340}, {692867, 45079}, {711185, 32809}, {737689, 22844}, {755905, 17395}, {766213, 16803}, {813691, 19386}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane15 = {49592, leftLane15, rightLane15, {49578, NONE, NONE}, {49572, NONE, NONE}, 49582, false, NONE, false};

const ST_BOUND leftLane16 = {{{552906, 29476}, {586586, 34759}, {601885, 37608}, {612252, 39538}, {622839, 44952}, {626565, 46857}, {640447, 57089}, {650463, 70081}, {652900, 73799}, {658006, 81586}, {660100, 84820}, {667824, 96744}, {675778, 113965}, {679808, 129786}, {680586, 192900}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane16 = {{{559920, -22592}, {594716, -17142}, {611589, -14500}, {629462, -8033}, {645838, -25}, {657784, 8675}, {674626, 29660}, {684681, 41976}, {690545, 49117}, {695187, 55811}, {698192, 60146}, {705954, 73775}, {715134, 96137}, {718563, 119915}, {714785, 197663}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane16 = {49594, leftLane16, rightLane16, {49564, NONE, NONE}, {49576, NONE, NONE}, 49584, false, NONE, false};

const ST_BOUND leftLane17 = {{{680586, 192900}, {692777, 51744}, {690323, -90079}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane17 = {{{650366, 193859}, {652990, 48641}, {655306, -88577}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane17 = {49596, leftLane17, rightLane17, {49578, NONE, NONE}, {49568, NONE, NONE}, 49598, false, NONE, false};

const ST_BOUND leftLane18 = {{{690323, -90079}, {692929, 49379}, {684972, 151845}, {680586, 192900}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane18 = {{{726123, -95889}, {729620, 48832}, {720300, 154600}, {714785, 197663}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane18 = {49598, leftLane18, rightLane18, {49570, NONE, NONE}, {49576, NONE, NONE}, 49596, false, NONE, false};

const ST_BOUND leftLane19 = {{{823071, 66800}, {795656, 64833}, {774228, 62958}, {758435, 61576}, {714133, 53506}, {703250, 51524}, {646793, 43244}, {608416, 37616}, {552906, 29476}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane19 = {{{831092, 109435}, {798567, 111465}, {769825, 113260}, {758344, 113239}, {703270, 113143}, {694108, 111752}, {637995, 103234}, {600154, 93954}, {558084, 78427}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane19 = {49600, leftLane19, rightLane19, {49574, NONE, NONE}, {49566, NONE, NONE}, 49602, false, NONE, false};

const ST_BOUND leftLane20 = {{{552906, 29476}, {603888, 36952}, {646772, 43240}, {703250, 51524}, {748686, 59801}, {758435, 61576}, {795656, 64833}, {823071, 66800}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_BOUND rightLane20 = {{{559920, -22592}, {611942, -17969}, {654916, -12293}, {712923, -4769}, {758160, 7792}, {769183, 10094}, {805501, 17676}, {813691, 19386}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}, {NONE, NONE}}, false};
const ST_LANE lane20 = {49602, leftLane20, rightLane20, {49564, NONE, NONE}, {49572, NONE, NONE}, 49600, false, NONE, false};

const ST_LANE laneNet[MAXL] = {lane1, lane2, lane3, lane4, lane5, lane6, lane7, lane8, lane9, lane10, lane11, lane12, lane13, lane14, lane15, lane16, lane17, lane18, lane19, lane20};


    const ST_RECTANGLE ego = {{333521, 11774}, 10000, 45000, 3500};
    //const ST_RECTANGLE ego = {{-100224, -28456}, 10000, 20000, -17705};
    //const ST_RECTANGLE ego = {{-300531, -40168}, 10000, 10000, 0};

    int lane;
    ST_IPOINT veh_corners[4], box_corners[4];

    //calculateCornerPoints(ego, veh_corners);

    bool is_inlane_net = check_inlane_laneNet(laneNet, ego, &lane, veh_corners, box_corners); 
    if (is_inlane_net)
        printf("The vehicle is in the lane network.\n");
    else
        printf("The vehicle is not in the lane network.\n");
        
    printf("vehicle corners: [%d, %d], [%d, %d], [%d, %d], [%d, %d]\n", veh_corners[0].x,  veh_corners[0].y, 
    veh_corners[1].x,  veh_corners[1].y, veh_corners[2].x,  veh_corners[2].y, veh_corners[3].x,  veh_corners[3].y);

    for(int i = 0; i < MAXL; i++) {
        uint8_t is_inlane_num = check_inlane_lane_single(laneNet[i], ego, veh_corners, box_corners);
        if (is_inlane_num != 0)
            printf("%d points of the ego vehicle are in the single lane: %d.\n", is_inlane_num, laneNet[i].ID);
        else
            printf("The vehicle is not in the single lane: %d.\n", laneNet[i].ID);
    }

    //fflush(stdout);

    return 0;
}



