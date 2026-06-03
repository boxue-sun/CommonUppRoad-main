echo "\nSCENARIO: USA_US101-1_1_T-1\n" >> result_exp1.log
../uppaal/bin_mac/verifyta exp1/USA_US101-1_1_T-1_generated_lanelet.xml query_exp1.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp1.log

echo "\nSCENARIO: ZAM_Ramp-1_1-T-1\n" >> result_exp1.log
../uppaal/bin_mac/verifyta exp1/ZAM_Ramp-1_1-T-1_generated_lanelet.xml query_exp1.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp1.log

echo "SCENARIO: ZAM_Tutorial-1_2_T-1\n" >> result_exp1.log
../uppaal/bin_mac/verifyta exp1/ZAM_Tutorial-1_2_T-1_generated_lanelet.xml query_exp1.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp1.log

echo "\nSCENARIO: DEU_A9-2_1_T-1\n" >> result_exp1.log
../uppaal/bin_mac/verifyta exp1/DEU_A9-2_1_T-1_generated_lanelet.xml query_exp1.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp1.log

echo "\nSCENARIO: DEU_Hhr-1_1\n" >> result_exp1.log
../uppaal/bin_mac/verifyta exp1/DEU_Hhr-1_1_generated_lanelet.xml query_exp1.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp1.log

echo "\nSCENARIO: ZAM_Over-1_1\n" >> result_exp1.log
../uppaal/bin_mac/verifyta exp1/ZAM_Over-1_1_generated_lanelet.xml query_exp1.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp1.log

echo "\nSCENARIO: DEU_Ffb-1_3_T-1\n" >> result_exp1.log
../uppaal/bin_mac/verifyta exp1/DEU_Ffb-1_3_T-1_generated_lanelet.xml query_exp1.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp1.log

echo "\nSCENARIO: ZAM_Tjunction-1_216_T-1\n" >> result_exp1.log
../uppaal/bin_mac/verifyta exp1/ZAM_Tjunction-1_216_T-1_generated_lanelet.xml query_exp1.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp1.log

echo "\nSCENARIO: DEU_Muc-11_1_T-1\n" >> result_exp1.log
../uppaal/bin_mac/verifyta exp1/DEU_Muc-11_1_T-1_generated_lanelet.xml query_exp1.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp1.log

echo "\nSCENARIO: DEU_Muc-3_1_T-1\n" >> result_exp1.log
../uppaal/bin_mac/verifyta exp1/DEU_Muc-3_1_T-1_generated_lanelet.xml query_exp1.q -u -D 0.01 -s --max-iterations 1 --eval-runs 1 --good-runs 100 --total-runs 200 --reset-no-better 1 --max-reset-learning 1 >> result_exp1.log
