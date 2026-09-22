set terminal epscairo
set output 'test_sim.xml-q1.eps'
set title 'Simulations (1)'
set key outside center right enhanced Left reverse samplen 1
set grid xtics ytics lc rgb '#808080'
set xlabel 'time'
set ylabel 'value'
set style data points
set datafile separator ','
plot 'test_sim.xml-q1-e0.csv' with lines lc rgb '#ff0000' title 'i2d((cps_i_state.position).x)',\
	'test_sim.xml-q1-e1.csv' with lines lc rgb '#ff9900' title 'i2d((cps_i_state.position).y)',\
	'test_sim.xml-q1-e2.csv' with lines lc rgb '#ccff00' title 'i2d(cps_i_state.orientation)',\
	'test_sim.xml-q1-e3.csv' with lines lc rgb '#33ff00' title 'i2d(cps_i_state.velocity)',\
	'test_sim.xml-q1-e4.csv' with lines lc rgb '#00ff66' title 'i2d(cps_i_state.acceleration)',\
	'test_sim.xml-q1-e5.csv' with lines lc rgb '#00ffff' title 'i2d((obs_i_state[0].position).x)',\
	'test_sim.xml-q1-e6.csv' with lines lc rgb '#0066ff' title 'i2d((obs_i_state[0].position).y)',\
	'test_sim.xml-q1-e7.csv' with lines lc rgb '#3300ff' title 'i2d(obs_i_state[0].orientation)',\
	'test_sim.xml-q1-e8.csv' with lines lc rgb '#cc00ff' title 'i2d(obs_i_state[0].velocity)',\
	'test_sim.xml-q1-e9.csv' with lines lc rgb '#ff0099' title 'i2d(obs_i_state[0].acceleration)'
