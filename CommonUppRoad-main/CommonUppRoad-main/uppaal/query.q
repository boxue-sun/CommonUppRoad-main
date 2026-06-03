strategy safe = control:A[] !cps_i_state.detection.collide && !cps_i_state.detection.outside
strategy reachSafe = minE(10*rSafe+rComfort+(5+100*cps_i_state.detection.reach)*rProgress) [<=MAXTIME] {}->{}: <> timer.Done under safe
simulate [<=MAXTIME] { cps_dynamic.x, cps_dynamic.y, cps_dynamic.orientation, cps_dynamic.velocity, cps_dynamic.acceleration } under reachSafe
