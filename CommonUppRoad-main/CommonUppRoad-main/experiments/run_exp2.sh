#echo "\nSCENARIO: ZAM_Ramp-1_1-T-1_MAXTIME_10\n" >> result_exp2_search.log
#../uppaal/bin_mac/verifyta exp2/ZAM_Ramp-1_1-T-1_MAXTIME_10.xml query_exp2_search.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp2_search.log

#echo "\nSCENARIO: ZAM_Ramp-1_1-T-1_MAXTIME_10\n" >> result_exp2_learn.log
#../uppaal/bin_mac/verifyta exp2/ZAM_Ramp-1_1-T-1_MAXTIME_10.xml query_exp2_learn.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 10 --max-reset-learning 10 >> result_exp2_learn.log

#echo "\nSCENARIO: ZAM_Ramp-1_1-T-1_MAXTIME_15\n" >> result_exp2_search.log
#../uppaal/bin_mac/verifyta exp2/ZAM_Ramp-1_1-T-1_MAXTIME_15.xml query_exp2_search.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp2_search.log

#echo "\nSCENARIO: ZAM_Ramp-1_1-T-1_MAXTIME_15\n" >> result_exp2_learn.log
#../uppaal/bin_mac/verifyta exp2/ZAM_Ramp-1_1-T-1_MAXTIME_15.xml query_exp2_learn.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 1000 --total-runs 1500 --reset-no-better 10 --max-reset-learning 10 >> result_exp2_learn.log

#echo "\nSCENARIO: ZAM_Ramp-1_1-T-1_MAXTIME_20\n" >> result_exp2_search.log
#../uppaal/bin_mac/verifyta exp2/ZAM_Ramp-1_1-T-1_MAXTIME_20.xml query_exp2_search.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp2_search.log

echo "\nSCENARIO: ZAM_Ramp-1_1-T-1_MAXTIME_20\n" >> result_exp2_learn.log
../uppaal/bin_mac/verifyta exp2/ZAM_Ramp-1_1-T-1_MAXTIME_20.xml query_exp2_learn.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 800 --total-runs 1000 --reset-no-better 10 --max-reset-learning 10 >> result_exp2_learn.log

#echo "\nSCENARIO: ZAM_Ramp-1_1-T-1_MAXTIME_25\n" >> result_exp2_search.log
#../uppaal/bin_mac/verifyta exp2/ZAM_Ramp-1_1-T-1_MAXTIME_25.xml query_exp2_search.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp2_search.log

echo "\nSCENARIO: ZAM_Ramp-1_1-T-1_MAXTIME_25\n" >> result_exp2_learn2.log
../uppaal/bin_mac/verifyta exp2/ZAM_Ramp-1_1-T-1_MAXTIME_25.xml query_exp2_learn.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 1500 --total-runs 2000 --reset-no-better 10 --max-reset-learning 10 >> result_exp2_learn2.log

#echo "\nSCENARIO: ZAM_Ramp-1_1-T-1_MAXTIME_30\n" >> result_exp2_search.log
#../uppaal/bin_mac/verifyta exp2/ZAM_Ramp-1_1-T-1_MAXTIME_30.xml query_exp2_search.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp2_search.log

#echo "\nSCENARIO: ZAM_Ramp-1_1-T-1_MAXTIME_30\n" >> result_exp2_learn.log
#../uppaal/bin_mac/verifyta exp2/ZAM_Ramp-1_1-T-1_MAXTIME_30.xml query_exp2_learn.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 1000 --total-runs 1500 --reset-no-better 10 --max-reset-learning 10 >> result_exp2_learn.log
