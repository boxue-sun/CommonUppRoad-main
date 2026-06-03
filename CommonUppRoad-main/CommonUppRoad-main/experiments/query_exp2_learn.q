strategy reach = minE(D) [<=MAXTIME] {egoController.location}->{dStateEgo.position.x, dStateEgo.position.y, dStateEgo.velocity, dStateEgo.orientation, dStateEgo.acceleration, dStateEgo.yawRate}: <> time>=MAXTIME
A[] !dStateEgo.detection.collide && !dStateEgo.detection.outside under reach
A<> dStateEgo.detection.reach under reach