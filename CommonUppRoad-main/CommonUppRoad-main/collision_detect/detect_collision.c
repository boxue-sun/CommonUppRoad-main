#include <stdio.h>
#include <math.h>
#include <stdint.h>
#include <stdbool.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif



typedef struct {
    int32_t x;
    int32_t y;
}ST_DPOINT;

typedef struct {
    double x;
    double y;
}ST_CPOINT;

typedef struct {
    ST_CPOINT position;
    double velocity;
    double orientation;
    double acceleration;
    double yawRate;
}ST_CSTATE;

typedef struct {
    ST_DPOINT center;
    int16_t width;
    int16_t length;
    int16_t orientation;
}ST_RECTANGLE;

typedef struct {
    double length;
    double width;
} VehicleDimensions;


double i2d(const int i) {
    const double SCALE = 100.0; // scale from int to double: 100 = 1.0
    double v = i/SCALE;
    return v;
}

int d2i(const double i) {
    const double SCALE = 100.0; // scale from int to double: 100 = 1.0
    int v = (int)(i*SCALE); // TODO: I update the function here, remember to change to fint during integration 
    return v;
}

// Function to check if all elements in the vector (size=4) have the same sign
bool same_sign(int vec[]) {
    int i = 0;
    int sign = (vec[0] >= 0) ? 1 : -1; // Get the sign of the first element
    for (i = 1; i < 4; i++) {
        if ((vec[i] >= 0) != (sign >= 0)) {
            return false; // Different signs found
        }
    }
    return true; // All elements have the same sign
}

// check if pt1 is on the same line defined by pt2-pt3
int check_online(ST_DPOINT pt1, ST_DPOINT pt2, ST_DPOINT pt3) {
    int dis12 = sqrt(pow(pt1.x - pt2.x, 2) + pow(pt1.y - pt2.y, 2));
    int dis13 = sqrt(pow(pt1.x - pt3.x, 2) + pow(pt1.y - pt3.y, 2));
    int dis23 = sqrt(pow(pt2.x - pt3.x, 2) + pow(pt2.y - pt3.y, 2));
    if (dis12 + dis13 == dis23)
        return 1;
    else
        return 0; 
}

// Check if any corner of box2 is outside box1
// int check_coverage(ST_DPOINT box1[], ST_DPOINT box2[]) {
//     int i = 0, j = 0;
//     int abx = 0, aby = 0, apx = 0, apy = 0;
//     int cross_prod[4];
//     int inside_sum = 0;
//     int is_online = 0;
//     // Check if all corners of box2 fall outside the bounding box of box1   
//     for (i = 0; i < 4; i++) {
//         // get the x y coordinate of the test points
//         for (j = 0; j < 4; j++) {
//             abx = box1[(j+1)%4].x - box1[j].x; // when j+1=4, back to the first one
//             aby = box1[(j+1)%4].y - box1[j].y;
//             apx = box2[i].x - box1[j].x;
//             apy = box2[i].y - box1[j].y;
//             // cross product of ab and ap
//             cross_prod[j] = abx*apy - apx*aby;
//             // check if on the line
//             if (check_online(box2[i], box1[j], box1[(j+1)%4]) == 1)
//                 is_online = 1;
//         }
//         // if all the cross production have the same sign, then the test point is within the box1
//         if (same_sign(cross_prod) || is_online == 1)
//             inside_sum++;
//     }
//     return inside_sum;
// }

int check_coverage(ST_DPOINT box1[4], ST_DPOINT box2[4]) {
    int i, j;
    int32_t abx[4], aby[4], apx, apy;
    int32_t cross_prod[4];
    int inside_sum = 0;
    int is_online = 0;
    
    // Pre-calculate abx and aby
    for (j = 0; j < 4; j++) {
        abx[j] = box1[(j+1)%4].x - box1[j].x;
        aby[j] = box1[(j+1)%4].y - box1[j].y;
    }

    for (i = 0; i < 4; i++) {
        // get the x y coordinate of the test points
        apx = box2[i].x - box1[0].x;
        apy = box2[i].y - box1[0].y;

        for (j = 0; j < 4; j++) {
            // cross product of ab and ap
            cross_prod[j] = abx[j]*apy - apx*aby[j];
            // check if on the line
            if (!is_online && check_online(box2[i], box1[j], box1[(j+1)%4]))
                is_online = 1;
        }
        // if all the cross productions have the same sign, or if any point is on the line
        if (same_sign(cross_prod) || is_online)
            inside_sum++;
        
        // Reset is_online for the next point
        is_online = 0;
    }
    return inside_sum;
}


int compute_approximating_circle_radius(int ego_length, int ego_width) {
    double length = i2d(ego_length);
    double width = i2d(ego_width);

    if (length <= 0 || width <= 0) {
        printf("Invalid vehicle dimensions\n");
        return -1.0;
    }

    if (fabs(length) < 1e-6 && fabs(width) < 1e-6)
        return 0.0;
    // Divide rectangle into 3 smaller rectangles
    double square_length = length/3.0;
    // Calculate minimum radius
    double diagonal_square = sqrt(pow(square_length/2.0, 2) + pow(width/2.0, 2));
    // Round up value
    double approx_radius = round(diagonal_square*10.0) / 10.0 + 0.1;

    return d2i(approx_radius);
}

void compute_centers_of_approximation_circles(ST_RECTANGLE veh_rect, ST_DPOINT *centers) {
    double disc_radius = i2d(compute_approximating_circle_radius(veh_rect.length, veh_rect.width));
    double distance_centers = disc_radius/2.0;

    // Compute the center position of first circle (front)
    double veh_cent_x_double = i2d(veh_rect.center.x);
    double veh_cent_y_double = i2d(veh_rect.center.y);
    centers[0].x = d2i(veh_cent_x_double + (distance_centers/2.0)*cos(i2d(veh_rect.orientation)));
    centers[0].y = d2i(veh_cent_y_double + (distance_centers/2.0)*sin(i2d(veh_rect.orientation)));

    // Compute the center position of second circle (rear)
    centers[1].x = d2i(veh_cent_x_double - (distance_centers/2.0)*cos(i2d(veh_rect.orientation)));
    centers[1].y = d2i(veh_cent_y_double - (distance_centers/2.0)*sin(i2d(veh_rect.orientation)));
}

// Function to calculate the corner points of a rectangle
void calculateCornerPoints(ST_RECTANGLE veh_state, ST_DPOINT corners[]) {
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

// int check_collision(ST_RECTANGLE veh_st_rect1, ST_RECTANGLE veh_st_rect2, int dis_thres) {
//     int i, j;
//     double dis, min_dis;
//     // define two vehicles' circle tuple (front and rear)
//     ST_DPOINT veh_circle_tuple1[2];
//     ST_DPOINT veh_circle_tuple2[2];
//     ST_DPOINT veh1_corners[4];
//     ST_DPOINT veh2_corners[4];
    
//     // calculate the centers of the vehicles' circles
//     compute_centers_of_approximation_circles(veh_st_rect1, veh_circle_tuple1);
//     compute_centers_of_approximation_circles(veh_st_rect2, veh_circle_tuple2);

//     min_dis = INFINITY;
//     for (i = 0; i < 2; ++i) {
//         for (j = 0; j < 2; ++j) {
//             dis = sqrt(pow(veh_circle_tuple1[i].x - veh_circle_tuple2[j].x, 2) + pow(veh_circle_tuple1[i].y - veh_circle_tuple2[j].y, 2));
//             min_dis = fmin(min_dis, dis);
//         }
//     }
//     //int min_dis_int = d2i(min_dis);
//     calculateCornerPoints(veh_st_rect1, veh1_corners);
//     calculateCornerPoints(veh_st_rect2, veh2_corners);
//     i = check_coverage(veh1_corners, veh2_corners);
//     if (dis_thres > min_dis || i != 0)
//         return 1; //collision happens
//     else
//         return 0;
// }

int check_collision(ST_RECTANGLE veh_st_rect1, ST_RECTANGLE veh_st_rect2, int dis_thres) {
    // Define variables
    int i;
    double dis_sq, min_dis_sq;
    ST_DPOINT veh_circle_tuple1[2];
    ST_DPOINT veh_circle_tuple2[2];
    ST_DPOINT veh1_corners[4];
    ST_DPOINT veh2_corners[4];

    // Calculate centers of approximation circles
    compute_centers_of_approximation_circles(veh_st_rect1, veh_circle_tuple1);
    compute_centers_of_approximation_circles(veh_st_rect2, veh_circle_tuple2);

    // Initialize minimum squared distance
    min_dis_sq = INFINITY;

    // Calculate minimum squared distance
    for (int i = 0; i < 2; ++i) {
        for (int j = 0; j < 2; ++j) {
            dis_sq = pow(veh_circle_tuple1[i].x - veh_circle_tuple2[j].x, 2) + pow(veh_circle_tuple1[i].y - veh_circle_tuple2[j].y, 2);
            min_dis_sq = fmin(min_dis_sq, dis_sq);
        }
    }

    // Early termination if minimum distance satisfies threshold
    if (min_dis_sq <= dis_thres * dis_thres) 
        return 1;

    // Calculate corner points
    calculateCornerPoints(veh_st_rect1, veh1_corners);
    calculateCornerPoints(veh_st_rect2, veh2_corners);

    // Check coverage
    i = check_coverage(veh1_corners, veh2_corners);
    
    // Collision detection based on distance threshold and coverage
    if (dis_thres > sqrt(min_dis_sq) || i != 0)
        return 1; // Collision detected
    else
        return 0; // No collision
}


int main() {
    const int DIS_THRES = 0;
    double state1[] = {-36.0, -0.4, 5.0, 2.0, M_PI/4.0};       //ego vehicle
    double state2[] = {-35.75, -0.4, 5.0, 2.0, 3.0*M_PI/4.0};   //obs

    ST_CPOINT veh_circle_tuple1[2];
    ST_CPOINT veh_circle_tuple2[2];

    ST_CPOINT position1_double[2] = {state1[0], state1[1]};
    ST_CPOINT position2_double[2] = {state2[0], state2[1]};

    int32_t position1_x = d2i(state1[0]);
    int32_t position1_y = d2i(state1[1]);
    int32_t position2_x = d2i(state2[0]);
    int32_t position2_y = d2i(state2[1]);

    ST_DPOINT position1_int16t = {position1_x, position1_y};
    ST_DPOINT position2_int16t = {position2_x, position2_y};

    //ST_RECTANGLE veh_st_rect1 = {position1_int16t, (int16_t)state1[3], (int16_t)state1[2], (int16_t)d2i(state1[4])};
    //ST_RECTANGLE veh_st_rect2 = {position2_int16t, (int16_t)state2[3], (int16_t)state2[2], (int16_t)d2i(state2[4])};
    ST_RECTANGLE veh_st_rect1 = {position1_int16t, 100, 450, 0};
    ST_RECTANGLE veh_st_rect2 = {position2_int16t, 100, 450, 0};

    
    int is_collsion = check_collision(veh_st_rect1, veh_st_rect2, DIS_THRES);
    if(is_collsion == 1)
        printf("collision detected");
    else
        printf("no collision");
    
    return 0;
}
