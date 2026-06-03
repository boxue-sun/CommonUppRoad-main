//This file was generated from (Academic) UPPAAL 5.1.0-beta5 (rev. C7C01B0740E14075), 2023-12-11

/*

*/
simulate [<=30] { obs1.vars.x, obs1.vars.y }

/*

*/
simulate [<=30] { obs1.vars.velocity, obs1.vars.orientation, obs1.vars.yawRate, obs1.vars.acceleration }

/*

*/
simulate [<=30] { obs1.vars.acceleration, i2d(obs1.dState.acceleration) }

/*

*/
simulate [<=30] { obs1.vars.yawRate, i2d(obs1.dState.yawRate) }

/*

*/
simulate [<=30] { obs1.vars.velocity, i2d(obs1.dState.velocity) }

/*

*/
simulate [<=30] { obs1.vars.orientation, i2d(obs1.dState.orientation) }

/*

*/
simulate [<=30] { obs1.vars.x, i2d(obs1.dState.position.x), obs1.vars.y, i2d(obs1.dState.position.y) }

/*

*/
simulate [<=30;100] { sqrt(pow(obs1.vars.x-i2d(obs1.dState.position.x),2) + pow(obs1.vars.y-i2d(obs1.dState.position.y),2)) }

/*
\/\/
*/
//NO_QUERY

/*

*/
simulate [<=30;100] { vars.x-i2d(dStateEgo.position.x), vars.y-i2d(dStateEgo.position.y) }

/*
\/\/
*/
//NO_QUERY

/*

*/
A[] !dStateEgo.detection.collide

/*

*/
A[] !dStateEgo.detection.outside

/*

*/
E[] !dStateEgo.detection.outside

/*
\/\/
*/
//NO_QUERY

/*

*/
strategy safe = control:A[] !dStateEgo.detection.collide && !dStateEgo.detection.outside

/*

*/
strategy safe = control:A[] !dStateEgo.detection.outside

/*

*/
saveStrategy("/Users/rgu01/Library/CloudStorage/OneDrive-Ma?lardalensuniversitet/Documents/Postdoc/Conferences/2024/ISoLA/models/safe.out", safe)

/*

*/
simulate [<=30] { vars.acceleration, i2d(dStateEgo.acceleration), vars.velocity, i2d(dStateEgo.velocity) } under safe

/*

*/
simulate [<=30] { vars.yawRate, i2d(dStateEgo.orientation), vars.orientation } under safe

/*

*/
simulate [<=30] { vars.x, i2d(dStateEgo.position.x), vars.y, i2d(dStateEgo.position.y) } under safe

/*

*/
simulate [<=30;100] { vars.x-i2d(dStateEgo.position.x), vars.y-i2d(dStateEgo.position.y) } under safe

/*

*/
A[] !dStateEgo.detection.collide && !dStateEgo.detection.outside under safe

/*

*/
Pr[<=10](<>dStateEgo.detection.reach) under safe

/*

*/
E[<=100;100](min:getDisP2P(dStateEgo.position, staticObs[0].center)) under safe

/*

*/
E[<=100;100](min:getDisP2P(dStateEgo.position, planning.goal)) under safe

/*

*/
//

/*

*/
strategy reachSafe = minE(D) [<=MAXTIME] {egoController.location, dStateEgo.position.x, dStateEgo.position.y,\
					  dStateEgo.velocity, dStateEgo.orientation, dStateEgo.acceleration,\
					  dStateEgo.yawRate}->{}: <> time>=MAXTIME under safe

/*

*/
simulate [<=30;100] { getDisP2P(dStateEgo.position, planning.goal) } under safe

/*

*/
simulate [<=30;100] { getDisP2P(dStateEgo.position, planning.goal) } under reachSafe

/*

*/
Pr[<=10](<> dStateEgo.detection.reach) under reachSafe

/*

*/
E[<=100;100](min:getDisP2P(dStateEgo.position, staticObs[0].center)) under reachSafe

/*

*/
E[<=100;100](min:getDisP2P(dStateEgo.position, planning.goal)) under reachSafe

/*
\/\/
*/
//NO_QUERY

/*

*/
strategy reach = minE(D) [<=MAXTIME] {egoController.location, dStateEgo.position.x, dStateEgo.position.y,\
					  dStateEgo.velocity, dStateEgo.orientation, dStateEgo.acceleration,\
					  dStateEgo.yawRate}->{}: <> time>=MAXTIME

/*

*/
saveStrategy("/home/ron/Projects/Commonroad/uppaal/reach.out", reach)

/*

*/
A<> dStateEgo.detection.reach under reach

/*

*/
A[] !dStateEgo.detection.collide && !dStateEgo.detection.outside under reach

/*

*/
simulate [<=MAXTIME] { vars.x, i2d(dStateEgo.position.x), vars.y, i2d(dStateEgo.position.y) } under reach

/*

*/
E[<=100;100](min:getDisP2P(dStateEgo.position, staticObs[0].center)) under reach

/*

*/
E[<=100;100](min:getDisP2P(dStateEgo.position, planning.goal)) under reach
